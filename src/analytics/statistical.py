"""Statistical analytics: OLS regression, correlation, ADF test.

Provides defensive implementations used by the API endpoints.
"""

import logging
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import adfuller
from statsmodels.api import OLS, add_constant

logger = logging.getLogger(__name__)


class StatisticalAnalytics:
    """Statistical tools for pairs trading analysis.

    All methods are static and return plain Python dictionaries suitable for
    JSON serialization by the API layer.
    """

    @staticmethod
    def ols_regression(x: List[float], y: List[float]) -> Dict[str, Any]:
        """Perform OLS regression y = alpha + beta * x.

        Returns a dict with hedge_ratio (beta), alpha (intercept), R² and
        additional statistics. This function is defensive against degenerate
        inputs and statsmodels failures and will fall back to simpler
        estimators when needed.
        """
        try:
            logger.debug("[OLS] Input: len(x)=%d, len(y)=%d", len(x), len(y))

            x_arr = np.asarray(x, dtype=float)
            y_arr = np.asarray(y, dtype=float)

            if x_arr.shape != y_arr.shape or x_arr.size < 2:
                logger.error("[OLS] Invalid input shapes x=%s y=%s", x_arr.shape, y_arr.shape)
                raise ValueError(f"Invalid input dimensions for OLS: x={x_arr.size}, y={y_arr.size}")

            # Zero variance handling
            if np.nanstd(x_arr) == 0 or np.nanstd(y_arr) == 0:
                logger.warning("[OLS] One or both series have zero variance")
                return {
                    "hedge_ratio": 0.0,
                    "alpha": float(np.nanmean(y_arr)) if np.nanstd(x_arr) == 0 else 0.0,
                    "r_squared": 0.0,
                    "adj_r_squared": 0.0,
                    "p_value": 1.0,
                    "std_err": 0.0,
                    "t_stat": 0.0,
                    "residual_std": 0.0,
                    "observations": int(x_arr.size),
                    "warning": "zero_variance",
                    "fallback_used": True,
                }

            # Add constant for intercept
            X = add_constant(x_arr)

            # Try statsmodels OLS
            try:
                model = OLS(y_arr, X).fit()
            except Exception as e:
                logger.warning("[OLS] statsmodels OLS failed: %s", e)
                # Fallback: numpy polyfit (slope, intercept)
                try:
                    slope, intercept = np.polyfit(x_arr, y_arr, 1)
                    residuals = y_arr - (intercept + slope * x_arr)
                    return {
                        "hedge_ratio": float(slope),
                        "alpha": float(intercept),
                        "r_squared": 0.0,
                        "adj_r_squared": 0.0,
                        "p_value": 1.0,
                        "std_err": 0.0,
                        "t_stat": 0.0,
                        "residual_std": float(np.nanstd(residuals)),
                        "observations": int(x_arr.size),
                        "warning": "fallback_polyfit",
                        "fallback_used": True,
                    }
                except Exception:
                    # Last resort: median ratio
                    try:
                        mask = x_arr != 0
                        if np.count_nonzero(mask) == 0:
                            raise ValueError("Cannot compute median ratio: no non-zero x")
                        slope = float(np.median(y_arr[mask] / x_arr[mask]))
                        intercept = 0.0
                        residuals = y_arr - (intercept + slope * x_arr)
                        return {
                            "hedge_ratio": slope,
                            "alpha": intercept,
                            "r_squared": 0.0,
                            "adj_r_squared": 0.0,
                            "p_value": 1.0,
                            "std_err": 0.0,
                            "t_stat": 0.0,
                            "residual_std": float(np.nanstd(residuals)),
                            "observations": int(x_arr.size),
                            "warning": "fallback_median_ratio",
                            "fallback_used": True,
                        }
                    except Exception:
                        logger.exception("[OLS] All fallbacks failed")
                        raise

            # Extract safe params
            params = np.asarray(getattr(model, "params", np.array([])))
            pvalues = np.asarray(getattr(model, "pvalues", np.array([1.0, 1.0])))
            bse = np.asarray(getattr(model, "bse", np.array([0.0, 0.0])))
            tvalues = np.asarray(getattr(model, "tvalues", np.array([0.0, 0.0])))

            # Default fallbacks
            hedge_ratio = 0.0
            alpha = float(np.nanmean(y_arr))

            if params.size >= 2:
                # expected: [const, slope]
                try:
                    hedge_ratio = float(params[1])
                except Exception:
                    hedge_ratio = 0.0
                try:
                    alpha = float(params[0])
                except Exception:
                    alpha = float(np.nanmean(y_arr))
            elif params.size == 1:
                # ambiguous: decide based on model.model.hasconst
                has_const = False
                try:
                    has_const = bool(getattr(model.model, "hasconst", False))
                except Exception:
                    has_const = False
                if has_const:
                    alpha = float(params[0])
                    hedge_ratio = 0.0
                else:
                    hedge_ratio = float(params[0])
                    alpha = 0.0

            residuals = np.asarray(getattr(model, "resid", y_arr - (alpha + hedge_ratio * x_arr)))

            result = {
                "hedge_ratio": float(hedge_ratio),
                "alpha": float(alpha),
                "r_squared": float(getattr(model, "rsquared", 0.0)),
                "adj_r_squared": float(getattr(model, "rsquared_adj", 0.0)),
                "p_value": float(pvalues[1]) if pvalues.size > 1 else float(pvalues[0]) if pvalues.size == 1 else 1.0,
                "std_err": float(bse[1]) if bse.size > 1 else (float(bse[0]) if bse.size == 1 else 0.0),
                "t_stat": float(tvalues[1]) if tvalues.size > 1 else (float(tvalues[0]) if tvalues.size == 1 else 0.0),
                "residual_std": float(np.nanstd(residuals)),
                "observations": int(x_arr.size),
                "fallback_used": False,
            }

            logger.info("[OLS] Result: beta=%.6f, alpha=%.6f, R²=%.6f", result["hedge_ratio"], result["alpha"], result["r_squared"])
            return result

        except Exception:
            logger.exception("[OLS] Regression failed")
            raise

    @staticmethod
    def rolling_correlation(x: List[float], y: List[float], window: int = 50) -> Dict[str, Any]:
        """Compute rolling Pearson correlation between two series.

        Returns a summary dict and the last up-to-100 rolling values.
        """
        try:
            df = pd.DataFrame({"x": x, "y": y})
            rolling = df["x"].rolling(window=window).corr(df["y"])
            vals = rolling.dropna().tolist()
            result = {
                "current_correlation": float(vals[-1]) if vals else None,
                "mean_correlation": float(np.nanmean(vals)) if vals else None,
                "std_correlation": float(np.nanstd(vals)) if vals else None,
                "min_correlation": float(np.nanmin(vals)) if vals else None,
                "max_correlation": float(np.nanmax(vals)) if vals else None,
                "window": int(window),
                "rolling_values": vals[-100:],
            }
            return result
        except Exception:
            logger.exception("Rolling correlation failed")
            raise

    @staticmethod
    def adf_test(series: List[float], significance: float = 0.05) -> Dict[str, Any]:
        """Augmented Dickey-Fuller test wrapper with input cleaning.

        Returns test statistic, p-value, critical values and boolean is_stationary.
        """
        try:
            arr = np.asarray(series, dtype=float)
            mask = np.isfinite(arr)
            if not mask.all():
                arr = arr[mask]
            if arr.size == 0:
                raise ValueError("ADF test requires finite numeric observations")
            if arr.size < 10:
                raise ValueError(f"ADF test requires at least 10 observations, got {arr.size}")

            res = adfuller(arr, autolag="AIC")
            adf_stat = float(res[0])
            p_value = float(res[1])
            critical_values = {k: float(v) for k, v in res[4].items()}
            is_stationary = p_value < float(significance)

            return {
                "adf_statistic": adf_stat,
                "p_value": p_value,
                "critical_values": critical_values,
                "is_stationary": bool(is_stationary),
                "significance_level": float(significance),
                "observations": int(arr.size),
                "interpretation": "Stationary" if is_stationary else "Non-stationary",
            }
        except Exception:
            logger.exception("[ADF] Test failed")
            raise

    @staticmethod
    def simple_correlation(x: List[float], y: List[float]) -> Dict[str, Any]:
        """Compute Pearson correlation and p-value."""
        try:
            corr, p = stats.pearsonr(x, y)
            return {"correlation": float(corr), "p_value": float(p), "is_significant": p < 0.05, "observations": int(len(x))}
        except Exception:
            logger.exception("Correlation calculation failed")
            raise

    @staticmethod
    def cointegration_test(x: List[float], y: List[float]) -> Dict[str, Any]:
        """Residual-based cointegration test: OLS then ADF on residuals."""
        try:
            ols = StatisticalAnalytics.ols_regression(x, y)
            hedge_ratio = ols.get("hedge_ratio", 0.0)
            alpha = ols.get("alpha", 0.0)
            x_arr = np.asarray(x, dtype=float)
            y_arr = np.asarray(y, dtype=float)
            spread = y_arr - (alpha + hedge_ratio * x_arr)
            adf = StatisticalAnalytics.adf_test(spread.tolist())
            return {
                "hedge_ratio": float(hedge_ratio),
                "alpha": float(alpha),
                "spread_adf_stat": adf["adf_statistic"],
                "spread_p_value": adf["p_value"],
                "is_cointegrated": adf["is_stationary"],
                "interpretation": "Cointegrated" if adf["is_stationary"] else "Not cointegrated",
            }
        except Exception:
            logger.exception("Cointegration test failed")
            raise


def test_analytics() -> None:
    """Simple smoke tests for the module when run standalone."""
    import logging as _logging
    _logging.basicConfig(level=_logging.DEBUG)
    np.random.seed(42)
    x = np.cumsum(np.random.randn(100)) + 100
    y = 2 * x + 5 + np.random.randn(100) * 0.5

    analytics = StatisticalAnalytics()
    print("=== OLS Regression ===")
    ols_result = analytics.ols_regression(x.tolist(), y.tolist())
    print(f"Hedge ratio: {ols_result['hedge_ratio']:.4f}")
    print(f"R-squared: {ols_result['r_squared']:.4f}")

    print("\n=== Correlation ===")
    corr_result = analytics.simple_correlation(x.tolist(), y.tolist())
    print(f"Correlation: {corr_result['correlation']:.4f}")

    print("\n=== Rolling Correlation ===")
    rolling_result = analytics.rolling_correlation(x.tolist(), y.tolist(), window=20)
    print(f"Current: {rolling_result['current_correlation']}")

    print("\n=== ADF Test ===")
    adf_result = analytics.adf_test((y - 2 * x).tolist())
    print(f"ADF Statistic: {adf_result['adf_statistic']:.4f}")
    print(f"Stationary: {adf_result['is_stationary']}")

    print("\n=== Cointegration Test ===")
    coint_result = analytics.cointegration_test(x.tolist(), y.tolist())
    print(f"Cointegrated: {coint_result['is_cointegrated']}")


if __name__ == "__main__":
    test_analytics()
