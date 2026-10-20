"""T8's models (plan section 6; D133 (6)) and their held-out predictions.

- Main model: additive logistic regression (statsmodels GLM, binomial, logit link). Day of year as
  a smooth cycle (Fourier harmonics), place as smooth latitude and longitude (natural cubic
  splines), effort (the log of T6's expected outings, E1), and each of W1 to W4 a natural cubic
  spline of 3 degrees of freedom. Unpenalised: a fixed-df regression spline is a smooth curve of
  exactly that many degrees of freedom.
- No-weather twin: the same without W1 to W4.
- Challenger: LightGBM as T1 (t1_model: the same 20 configurations, inner leave-one-year-out
  tuning on the training years only, T1's seed), on the same inputs: day of year as sine and
  cosine, latitude, longitude, E1, and W1 to W4; and its own no-weather twin.

The day-of-year cycle's harmonics, the place smooth's form and df, and the effort term's form are
not set by the plan or D133 (design.PENDING M-calendar-place, M-effort-form); `ModelSpec` carries
them, and PROPOSED_SPEC is the proposal, not a ruling.

Spline knots are placed on each fold's training rows only (boundary knots at the training minimum
and maximum, interior knots at equal quantiles), so nothing about a held-out year shapes its
curve; beyond the boundary a natural spline is linear.
"""

from __future__ import annotations

import gc
import math
import warnings
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date

import numpy as np

from forager_forecast import t1_model as tm
from forager_forecast.t8.design import MEASURE_DF


@dataclass(frozen=True)
class ModelSpec:
    harmonics: int  # day-of-year Fourier harmonics: 2 x harmonics columns
    place_df: int  # natural spline df for latitude and for longitude, added
    effort: str  # "linear", "offset" or "spline3"
    measure_df: int = MEASURE_DF

    def __post_init__(self) -> None:
        if self.effort not in ("linear", "offset", "spline3"):
            raise ValueError(f"unknown effort form {self.effort!r}")
        if self.harmonics < 1 or self.place_df < 1 or self.measure_df < 1:
            raise ValueError("harmonics and degrees of freedom must be at least 1")


PROPOSED_SPEC = ModelSpec(harmonics=3, place_df=3, effort="linear")


# Bases ----------------------------------------------------------------------------------------


def day_of_year_angle(mondays: Sequence[date]) -> np.ndarray:
    """2 pi (day of year - 1) / days in the year, as weather_windows.calendar_place_features."""
    out = np.empty(len(mondays))
    for i, d in enumerate(mondays):
        n = 366 if (d.year % 4 == 0 and (d.year % 100 != 0 or d.year % 400 == 0)) else 365
        out[i] = 2 * math.pi * (d.timetuple().tm_yday - 1) / n
    return out


def fourier(angle: np.ndarray, harmonics: int) -> np.ndarray:
    cols = []
    for k in range(1, harmonics + 1):
        cols += [np.sin(k * angle), np.cos(k * angle)]
    return np.column_stack(cols)


def ns_knots(x_train: np.ndarray, df: int) -> np.ndarray:
    """df + 1 knots: the training minimum and maximum, and df - 1 interior knots at equal
    quantiles (R's ns(x, df) placement). Repeated knots (a measure with tied values) are refused."""
    x = np.asarray(x_train, dtype=np.float64)
    interior = np.quantile(x, np.arange(1, df) / df) if df > 1 else np.array([])
    knots = np.concatenate([[x.min()], interior, [x.max()]])
    if np.any(np.diff(knots) <= 0):
        raise ValueError(f"knots are not distinct: {knots}")
    return knots


def ns_basis(x: np.ndarray, knots: np.ndarray) -> np.ndarray:
    """Natural cubic spline basis without the constant: len(knots) - 1 columns (Hastie,
    Tibshirani and Friedman, The Elements of Statistical Learning, eq. 5.4 and 5.5), on x scaled
    to the boundary knots for conditioning. Linear beyond the boundary knots."""
    lo, hi = knots[0], knots[-1]
    t = (np.asarray(x, dtype=np.float64) - lo) / (hi - lo)
    k = (knots - lo) / (hi - lo)
    big_k = len(k)

    def d(j: int) -> np.ndarray:
        return (np.maximum(t - k[j], 0.0) ** 3 - np.maximum(t - k[big_k - 1], 0.0) ** 3) / (
            k[big_k - 1] - k[j]
        )

    cols = [t]
    last = d(big_k - 2)
    for j in range(big_k - 2):
        cols.append(d(j) - last)
    return np.column_stack(cols)


# Additive logistic ----------------------------------------------------------------------------


@dataclass(frozen=True)
class Inputs:
    """Everything the models read, per unit, in one order."""

    y: np.ndarray
    years: np.ndarray  # ISO year = fold year
    mondays: list[date]
    latitude: np.ndarray
    longitude: np.ndarray
    log_effort: dict[int, np.ndarray]  # held-out year -> E1 for every unit in that fold
    weather: np.ndarray | None  # [unit, measure], or None for no-weather only

    def __post_init__(self) -> None:
        n = len(self.y)
        for name in ("years", "mondays", "latitude", "longitude"):
            if len(getattr(self, name)) != n:
                raise ValueError(f"{name} has {len(getattr(self, name))} entries for {n} units")
        for h, e in self.log_effort.items():
            if e.shape != (n,) or not np.isfinite(e).all():
                raise ValueError(f"effort for fold {h} is not one finite value per unit")
        if self.weather is not None and (
            self.weather.shape[0] != n or not np.isfinite(self.weather).all()
        ):
            raise ValueError("weather is not one finite row per unit")


def design_matrix(
    spec: ModelSpec,
    angle: np.ndarray,
    lat: np.ndarray,
    lon: np.ndarray,
    log_effort: np.ndarray,
    weather: np.ndarray | None,
    train: np.ndarray,
) -> tuple[np.ndarray, np.ndarray | None]:
    """(X, offset) for every unit, bases fitted on the training rows."""
    cols = [np.ones((len(angle), 1)), fourier(angle, spec.harmonics)]
    for v in (lat, lon):
        cols.append(ns_basis(v, ns_knots(v[train], spec.place_df)))
    offset = None
    if spec.effort == "linear":
        cols.append(log_effort[:, None])
    elif spec.effort == "spline3":
        cols.append(ns_basis(log_effort, ns_knots(log_effort[train], 3)))
    else:
        offset = log_effort
    if weather is not None:
        for j in range(weather.shape[1]):
            w = weather[:, j]
            cols.append(ns_basis(w, ns_knots(w[train], spec.measure_df)))
    return np.hstack(cols), offset


class FitFailed(RuntimeError):
    """The logistic fit did not converge; never a silent fallback."""


def fit_predict_logistic(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    offset_train: np.ndarray | None = None,
    offset_test: np.ndarray | None = None,
) -> np.ndarray:
    import statsmodels.api as sm  # noqa: PLC0415

    # statsmodels' model and results hold each other, and the design arrays, in reference cycles.
    # The cyclic collector triggers on object counts, not bytes, so across the 199 swaps x 11 folds
    # these piled up uncollected: test_t8_run reached 7.4 GB on synthetic data (measured
    # 2026-10-20: about 35 MB more resident per 11-fold pass, flat once collected), and the real
    # fits, about 30 times larger per fit, would have run out far sooner. So only the fitted
    # coefficients leave this function, and the cycles are collected before it returns.
    try:
        model = sm.GLM(y_train, x_train, family=sm.families.Binomial(), offset=offset_train)
        with warnings.catch_warnings():
            warnings.simplefilter("error", category=sm.tools.sm_exceptions.PerfectSeparationWarning)
            warnings.simplefilter("error", category=sm.tools.sm_exceptions.ConvergenceWarning)
            try:
                result = model.fit(maxiter=100, tol=1e-10)
            except (Warning, np.linalg.LinAlgError) as e:
                raise FitFailed(f"logistic fit failed: {e}") from e
        converged = bool(result.converged)
        params = np.array(result.params, dtype=np.float64)
    finally:
        model = result = None
        gc.collect(0)
    if not converged:
        raise FitFailed("logistic fit did not converge in 100 iterations")
    eta = x_test @ params + (0.0 if offset_test is None else offset_test)
    return 1.0 / (1.0 + np.exp(-eta))


def loyo_additive(
    inputs: Inputs,
    spec: ModelSpec,
    use_weather: bool,
    weather: np.ndarray | None = None,
    years: Sequence[int] | None = None,
) -> np.ndarray:
    """Held-out predictions for every unit, each from a fit that never saw its year. `weather`
    overrides inputs.weather (for the swaps)."""
    w = (inputs.weather if weather is None else weather) if use_weather else None
    if use_weather and w is None:
        raise ValueError("the weather model needs weather")
    angle = day_of_year_angle(inputs.mondays)
    out = np.full(len(inputs.y), np.nan)
    for h in sorted(set(inputs.years.tolist())) if years is None else years:
        held = inputs.years == h
        train = ~held
        x, offset = design_matrix(
            spec, angle, inputs.latitude, inputs.longitude, inputs.log_effort[h], w, train
        )
        out[held] = fit_predict_logistic(
            x[train],
            inputs.y[train],
            x[held],
            None if offset is None else offset[train],
            None if offset is None else offset[held],
        )
    if np.isnan(out).any():
        raise RuntimeError("a unit has no held-out prediction")
    return out


def leave_one_block_out_additive(
    inputs: Inputs, spec: ModelSpec, use_weather: bool, blocks: np.ndarray, log_effort: np.ndarray
) -> np.ndarray:
    """Held-out predictions by block (ecoregion): each block predicted from a fit on the others,
    over all years, with one effort value per unit (design.PENDING M-ecoregion)."""
    angle = day_of_year_angle(inputs.mondays)
    w = inputs.weather if use_weather else None
    out = np.full(len(inputs.y), np.nan)
    for b in sorted(set(blocks.tolist())):
        held = blocks == b
        train = ~held
        x, offset = design_matrix(
            spec, angle, inputs.latitude, inputs.longitude, log_effort, w, train
        )
        out[held] = fit_predict_logistic(
            x[train],
            inputs.y[train],
            x[held],
            None if offset is None else offset[train],
            None if offset is None else offset[held],
        )
    return out


# Challenger -----------------------------------------------------------------------------------


def challenger_matrix(inputs: Inputs, fold: int, use_weather: bool, weather=None) -> np.ndarray:
    angle = day_of_year_angle(inputs.mondays)
    cols = [
        np.sin(angle),
        np.cos(angle),
        inputs.latitude,
        inputs.longitude,
        inputs.log_effort[fold],
    ]
    x = np.column_stack(cols)
    if use_weather:
        w = inputs.weather if weather is None else weather
        x = np.hstack([x, w])
    return x


Fitter = Callable[[dict, np.ndarray, np.ndarray, np.ndarray], np.ndarray]


def loyo_challenger(
    inputs: Inputs,
    use_weather: bool,
    configs: Sequence[dict],
    fitter: Fitter,
    weather: np.ndarray | None = None,
    fixed_choice: dict[int, str] | None = None,
) -> tuple[np.ndarray, dict[int, str]]:
    """Held-out predictions and each fold's chosen configuration id. The configuration is chosen by
    T1's inner leave-one-year-out on the fold's training years (t1_model.inner_choice), unless
    fixed_choice names it (design.PENDING M-challenger-swaps: the swaps reuse the true-weather
    choice)."""
    by_id = {c["id"]: c for c in configs}
    out = np.full(len(inputs.y), np.nan)
    chosen: dict[int, str] = {}
    for h in sorted(set(inputs.years.tolist())):
        held = inputs.years == h
        x = challenger_matrix(inputs, h, use_weather, weather)
        if fixed_choice is None:
            best, _scores = tm.inner_choice(
                configs, x[~held], inputs.y[~held], inputs.years[~held], fitter
            )
        else:
            best = by_id[fixed_choice[h]]
        chosen[h] = best["id"]
        out[held] = fitter(best, x[~held], inputs.y[~held], x[held])
    if np.isnan(out).any():
        raise RuntimeError("a unit has no held-out prediction")
    return out, chosen
