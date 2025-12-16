"""Kalman filter for dynamic hedge ratio estimation."""
import numpy as np
from pykalman import KalmanFilter
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class KalmanHedgeRatio:
    """
    Use Kalman filter to dynamically estimate hedge ratio between two assets.
    """
    
    def __init__(self, initial_state: float = 1.0, 
                 transition_covariance: float = 0.01,
                 observation_covariance: float = 1.0):
        """
        Initialize Kalman filter for hedge ratio estimation.
        
        Args:
            initial_state: Initial hedge ratio estimate
            transition_covariance: Process noise (how much hedge ratio can change)
            observation_covariance: Measurement noise
        """
        self.initial_state = initial_state
        self.transition_covariance = transition_covariance
        self.observation_covariance = observation_covariance
        
        # State: hedge ratio (beta)
        # Observation: price2 = beta * price1
        self.kf = KalmanFilter(
            transition_matrices=[1],
            observation_matrices=[1],
            initial_state_mean=[initial_state],
            initial_state_covariance=[1],
            transition_covariance=[transition_covariance],
            observation_covariance=[observation_covariance]
        )
        
        self.state_means = []
        self.state_covariances = []
    
    def estimate(self, price1: List[float], price2: List[float]) -> Dict[str, Any]:
        """
        Estimate dynamic hedge ratio using Kalman filter.
        
        Args:
            price1: Asset 1 prices (independent variable)
            price2: Asset 2 prices (dependent variable)
        
        Returns:
            Dictionary with hedge ratios and statistics
        """
        try:
            price1 = np.array(price1)
            price2 = np.array(price2)
            
            if len(price1) != len(price2) or len(price1) < 2:
                raise ValueError("Invalid price arrays for Kalman filter")
            
            # Prepare observations: y/x ratio as observation
            observations = price2 / price1
            observations = observations.reshape(-1, 1)
            
            # Run Kalman filter
            state_means, state_covariances = self.kf.filter(observations)
            
            self.state_means = state_means.flatten()
            self.state_covariances = state_covariances.flatten()
            
            current_hedge_ratio = float(self.state_means[-1])
            current_std = float(np.sqrt(self.state_covariances[-1]))
            
            result = {
                "hedge_ratios": self.state_means.tolist(),
                "current_hedge_ratio": current_hedge_ratio,
                "current_std": current_std,
                "confidence_interval_95": [
                    current_hedge_ratio - 1.96 * current_std,
                    current_hedge_ratio + 1.96 * current_std
                ],
                "mean_hedge_ratio": float(np.mean(self.state_means)),
                "std_hedge_ratio": float(np.std(self.state_means)),
                "observations": len(price1)
            }
            
            logger.debug(
                f"Kalman hedge ratio: {current_hedge_ratio:.4f} "
                f"± {current_std:.4f}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Kalman filter estimation failed: {e}")
            raise
    
    def update_online(self, new_price1: float, new_price2: float) -> float:
        """
        Online update with a single new observation.
        
        Returns current hedge ratio estimate.
        """
        try:
            observation = np.array([[new_price2 / new_price1]])
            
            if len(self.state_means) == 0:
                # First observation
                state_mean = np.array([self.initial_state])
                state_covariance = np.array([1.0])
            else:
                # Use last state
                state_mean = np.array([self.state_means[-1]])
                state_covariance = np.array([self.state_covariances[-1]])
            
            # Filter update
            new_state_mean, new_state_covariance = self.kf.filter_update(
                state_mean,
                state_covariance,
                observation
            )
            
            self.state_means.append(float(new_state_mean[0]))
            self.state_covariances.append(float(new_state_covariance[0, 0]))
            
            return float(new_state_mean[0])
            
        except Exception as e:
            logger.error(f"Kalman online update failed: {e}")
            raise
    
    def get_spread_with_kalman(self, price1: List[float], price2: List[float]) -> Dict[str, Any]:
        """
        Compute spread using Kalman-estimated hedge ratio.
        """
        result = self.estimate(price1, price2)
        hedge_ratios = np.array(result["hedge_ratios"])
        
        price1 = np.array(price1)
        price2 = np.array(price2)
        
        # Compute spread with dynamic hedge ratio
        spread = price2 - hedge_ratios * price1
        
        return {
            "spread": spread.tolist(),
            "current_spread": float(spread[-1]),
            "hedge_ratios": hedge_ratios.tolist(),
            "current_hedge_ratio": result["current_hedge_ratio"]
        }


class SimpleKalmanFilter:
    """
    Simplified Kalman filter implementation without pykalman dependency.
    """
    
    def __init__(self, process_variance: float = 0.01, measurement_variance: float = 1.0):
        self.process_variance = process_variance
        self.measurement_variance = measurement_variance
        
        self.state_estimate = 1.0
        self.estimate_variance = 1.0
    
    def update(self, measurement: float) -> float:
        """
        Update Kalman filter with new measurement.
        """
        # Prediction
        predicted_state = self.state_estimate
        predicted_variance = self.estimate_variance + self.process_variance
        
        # Update
        kalman_gain = predicted_variance / (predicted_variance + self.measurement_variance)
        self.state_estimate = predicted_state + kalman_gain * (measurement - predicted_state)
        self.estimate_variance = (1 - kalman_gain) * predicted_variance
        
        return self.state_estimate
    
    def estimate_hedge_ratio(self, price1: List[float], price2: List[float]) -> List[float]:
        """
        Estimate dynamic hedge ratio over time.
        """
        price1 = np.array(price1)
        price2 = np.array(price2)
        
        ratios = price2 / price1
        hedge_ratios = []
        
        for ratio in ratios:
            hr = self.update(ratio)
            hedge_ratios.append(hr)
        
        return hedge_ratios


def test_kalman():
    """Test Kalman filter hedge ratio estimation."""
    np.random.seed(42)
    
    # Generate prices with time-varying hedge ratio
    n = 200
    t = np.linspace(0, 10, n)
    
    # Time-varying hedge ratio (sine wave around 2.0)
    true_hedge_ratio = 2.0 + 0.3 * np.sin(t)
    
    price1 = np.cumsum(np.random.randn(n) * 0.5) + 100
    price2 = true_hedge_ratio * price1 + np.random.randn(n) * 2
    
    print("=== Kalman Filter Hedge Ratio ===")
    
    # Test with pykalman
    try:
        kalman = KalmanHedgeRatio(
            initial_state=2.0,
            transition_covariance=0.01,
            observation_covariance=1.0
        )
        
        result = kalman.estimate(price1.tolist(), price2.tolist())
        
        print(f"Current hedge ratio: {result['current_hedge_ratio']:.4f}")
        print(f"Mean hedge ratio: {result['mean_hedge_ratio']:.4f}")
        print(f"Std hedge ratio: {result['std_hedge_ratio']:.4f}")
        print(f"95% CI: [{result['confidence_interval_95'][0]:.4f}, {result['confidence_interval_95'][1]:.4f}]")
        
        # Compare with true hedge ratio
        true_final = true_hedge_ratio[-1]
        estimated_final = result['current_hedge_ratio']
        error = abs(true_final - estimated_final)
        print(f"\nTrue final hedge ratio: {true_final:.4f}")
        print(f"Estimated final: {estimated_final:.4f}")
        print(f"Error: {error:.4f}")
        
    except ImportError:
        print("pykalman not available, using simple Kalman filter")
        
        simple_kalman = SimpleKalmanFilter(process_variance=0.01, measurement_variance=1.0)
        hedge_ratios = simple_kalman.estimate_hedge_ratio(price1.tolist(), price2.tolist())
        
        print(f"Final hedge ratio: {hedge_ratios[-1]:.4f}")
        print(f"Mean hedge ratio: {np.mean(hedge_ratios):.4f}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_kalman()
