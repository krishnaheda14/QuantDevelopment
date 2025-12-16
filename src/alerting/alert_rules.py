"""Alert rules and conditions."""
from typing import Dict, Any, Callable
import logging

logger = logging.getLogger(__name__)


class AlertRule:
    """Base class for alert rules."""
    
    def __init__(self, name: str, condition: Callable, threshold: float, message_template: str):
        self.name = name
        self.condition = condition
        self.threshold = threshold
        self.message_template = message_template
    
    def check(self, data: Dict[str, Any]) -> bool:
        """Check if alert condition is met."""
        try:
            return self.condition(data, self.threshold)
        except Exception as e:
            logger.error(f"Alert rule '{self.name}' check failed: {e}")
            return False
    
    def format_message(self, data: Dict[str, Any]) -> str:
        """Format alert message."""
        return self.message_template.format(**data, threshold=self.threshold)


# Predefined rule conditions
def zscore_above_threshold(data: Dict[str, Any], threshold: float) -> bool:
    """Check if z-score exceeds threshold."""
    zscore = data.get("zscore", 0)
    return abs(zscore) > threshold


def spread_above_threshold(data: Dict[str, Any], threshold: float) -> bool:
    """Check if spread exceeds threshold."""
    spread = data.get("spread", 0)
    mean_spread = data.get("spread_mean", 0)
    
    if mean_spread == 0:
        return False
    
    spread_pct = abs((spread - mean_spread) / mean_spread)
    return spread_pct > threshold


def price_change_threshold(data: Dict[str, Any], threshold: float) -> bool:
    """Check if price change exceeds threshold."""
    price_change_pct = data.get("price_change_pct", 0)
    return abs(price_change_pct) > threshold


def volume_spike_threshold(data: Dict[str, Any], threshold: float) -> bool:
    """Check if volume spike exceeds threshold."""
    volume = data.get("volume", 0)
    avg_volume = data.get("avg_volume", 0)
    
    if avg_volume == 0:
        return False
    
    volume_ratio = volume / avg_volume
    return volume_ratio > threshold


# Predefined alert rules
DEFAULT_RULES = [
    AlertRule(
        name="High Z-Score",
        condition=zscore_above_threshold,
        threshold=2.0,
        message_template="Z-score alert: {symbol1}-{symbol2} z-score = {zscore:.2f} (threshold: {threshold})"
    ),
    AlertRule(
        name="Large Spread Deviation",
        condition=spread_above_threshold,
        threshold=0.005,  # 0.5%
        message_template="Spread alert: {symbol1}-{symbol2} spread deviated {spread:.4f} from mean (threshold: {threshold:.1%})"
    ),
    AlertRule(
        name="Price Spike",
        condition=price_change_threshold,
        threshold=0.02,  # 2%
        message_template="Price spike alert: {symbol} changed {price_change_pct:.2%} (threshold: {threshold:.1%})"
    ),
    AlertRule(
        name="Volume Spike",
        condition=volume_spike_threshold,
        threshold=3.0,  # 3x average
        message_template="Volume spike: {symbol} volume {volume:.2f} is {volume_ratio:.1f}x average"
    )
]


def create_custom_rule(name: str, condition_func: Callable, threshold: float, message: str) -> AlertRule:
    """Create a custom alert rule."""
    return AlertRule(name, condition_func, threshold, message)
