"""D20 and T1 amendment 2: the gradient-boosting library must have a wheel for the pinned Python.

This is the wheel check made repeatable: importing lightgbm loads its compiled library, and a
five-round fit on random numbers proves the binary runs. The numbers are synthetic and fixed by
seed. No record or weather data is involved (T1 fits no model until the GBIF download exists).
"""

import importlib.metadata

import numpy as np


def test_lightgbm_wheel_imports_and_runs_on_the_pinned_python():
    import lightgbm as lgb

    assert lgb.__version__ == "4.7.0"
    assert importlib.metadata.version("lightgbm") == "4.7.0"
    rng = np.random.default_rng(20260918)
    features = rng.normal(size=(200, 4))
    labels = (features[:, 0] + rng.normal(scale=0.3, size=200) > 0).astype(int)
    booster = lgb.train(
        {"objective": "binary", "verbose": -1, "num_leaves": 4, "seed": 0, "num_threads": 1},
        lgb.Dataset(features, labels),
        num_boost_round=5,
    )
    assert booster.num_trees() == 5
    predictions = booster.predict(features)
    assert predictions.shape == (200,)
    assert np.all((predictions > 0) & (predictions < 1))
