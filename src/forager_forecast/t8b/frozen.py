"""C5's frozen model (plan section 7; D159 (5)): fitted once, saved with its checksum before any
2026 record is read, and loaded only against that checksum.

`fit_frozen` follows PENDING C5-frozen-fit and C5-calendar (proposed): the model is refitted on
all 2015 to 2025 units, its configuration chosen by T1's inner leave-one-year-out over those
eleven years (t1_model.inner_choice with T1's own fitter), and its clamp range is those years'
range for each weather column. `predict` applies that clamp before the trees, as the folds did.

The saved file is one JSON document with sorted keys: the configuration, the feature names, the
clamp, the training years, LightGBM's own model text and free metadata. `save` returns the file's
sha256, which the caller records (the fit report, and the register beside the file); `load`
refuses a file whose sha256 is not the one given, so a model changed after freezing cannot be
scored.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

from forager_forecast import t1_model as tm
from forager_forecast.t8b import clamp as cl

FORMAT = "t8b-frozen-1"


class ChecksumDiffers(RuntimeError):
    """A frozen model's file is not the one whose checksum was recorded."""


@dataclass(frozen=True)
class FrozenModel:
    name: str
    config: dict
    features: tuple[str, ...]
    clamp_low: tuple[float, ...]
    clamp_high: tuple[float, ...]
    weather_columns: tuple[int, ...]
    training_years: tuple[int, ...]
    booster: str  # LightGBM's model text
    meta: dict = field(default_factory=dict)


def _train(config: dict, x: np.ndarray, y: np.ndarray, threads: int) -> str:
    import lightgbm as lgb  # noqa: PLC0415

    params = {
        "objective": "binary",
        "verbose": -1,
        "seed": tm.SEED,
        "deterministic": True,
        "force_row_wise": True,
        "num_threads": threads,
        "bagging_seed": tm.SEED,
        "feature_fraction_seed": tm.SEED,
        **{k: v for k, v in config.items() if k not in ("id", "num_boost_round")},
    }  # the same parameters as t1_model.fit_predict
    booster = lgb.train(params, lgb.Dataset(x, y), num_boost_round=config["num_boost_round"])
    return booster.model_to_string()


def fit_frozen(
    name: str,
    x: np.ndarray,
    y: np.ndarray,
    years: np.ndarray,
    configs: Sequence[dict],
    features: Sequence[str],
    weather_columns: Sequence[int],
    threads: int = 1,
    meta: dict | None = None,
) -> FrozenModel:
    x = np.asarray(x, dtype=np.float64)
    if x.shape[1] != len(features):
        raise ValueError(f"{x.shape[1]} columns for {len(features)} feature names")
    cols = list(weather_columns)
    low = high = np.zeros(0)
    if cols:
        low, high = cl.training_range(x[:, cols], np.ones(len(x), dtype=bool))

    def fitter(config, train_x, train_y, test_x):
        return tm.fit_predict(config, train_x, train_y, test_x, threads)

    best, _scores = tm.inner_choice(configs, x, y, np.asarray(years), fitter)
    return FrozenModel(
        name=name,
        config=dict(best),
        features=tuple(features),
        clamp_low=tuple(float(v) for v in low),
        clamp_high=tuple(float(v) for v in high),
        weather_columns=tuple(int(c) for c in cols),
        training_years=tuple(sorted(int(v) for v in set(np.asarray(years).tolist()))),
        booster=_train(best, x, y, threads),
        meta=dict(meta or {}),
    )


def predict(model: FrozenModel, x: np.ndarray) -> np.ndarray:
    import lightgbm as lgb  # noqa: PLC0415

    x = np.array(x, dtype=np.float64)
    if x.shape[1] != len(model.features):
        raise ValueError(f"{x.shape[1]} columns for the model's {len(model.features)}")
    cols = list(model.weather_columns)
    if cols:
        x[:, cols] = cl.clamp(x[:, cols], np.array(model.clamp_low), np.array(model.clamp_high))
    return lgb.Booster(model_str=model.booster).predict(x)


def _document(model: FrozenModel) -> bytes:
    body = {"format": FORMAT, **asdict(model)}
    return (json.dumps(body, sort_keys=True, indent=1) + "\n").encode()


def save(model: FrozenModel, path: Path) -> str:
    """Writes the model and returns its sha256 (hex). Refuses to overwrite a frozen file."""
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"{path} exists; a frozen model is never overwritten")
    data = _document(model)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def load(path: Path, expected_sha256: str) -> FrozenModel:
    data = Path(path).read_bytes()
    got = hashlib.sha256(data).hexdigest()
    if got != expected_sha256:
        raise ChecksumDiffers(f"{Path(path).name}: sha256 {got}, recorded {expected_sha256}")
    body = json.loads(data)
    if body.pop("format", None) != FORMAT:
        raise ChecksumDiffers(f"{Path(path).name} is not a {FORMAT} file")
    for key in ("features", "clamp_low", "clamp_high", "weather_columns", "training_years"):
        body[key] = tuple(body[key])
    return FrozenModel(**body)
