from src.analytics.statistical import ols
from src.analytics.spread_analysis import zscore
import numpy as np


def test_ols():
    x = [1, 2, 3, 4, 5]
    y = [2, 4, 6, 8, 10]
    beta = ols(x, y)
    assert abs(beta - 2.0) < 0.01


def test_zscore():
    data = [1, 2, 3, 4, 5]
    z = zscore(data)
    assert abs(z.mean()) < 0.01
