"""Eligibility checks and EcoCoin reward calculations."""
import math

def calculate_reward(quantity_kg, reward_rate):
    """Return (rate, whole EcoCoins); fractions are rounded down."""
    quantity = float(quantity_kg)
    rate = int(reward_rate)
    if not math.isfinite(quantity) or quantity <= 0:
        raise ValueError("Quantity must be a positive number.")
    if rate < 0:
        raise ValueError("Reward rate cannot be negative.")
    return rate, math.floor(quantity * rate)

def validate_submission(category, quantity_kg, category_accepted, point_accepted_waste):
    """Raise a clear error when a submission does not meet the rules."""
    try:
        quantity = float(quantity_kg)
    except (TypeError, ValueError):
        raise ValueError("Enter a valid quantity in kilograms.")
    if not math.isfinite(quantity) or quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")
    if not category_accepted:
        raise ValueError(f"{category} is not accepted for EcoCoin rewards.")
    accepted_at_point = {item.strip().casefold() for item in point_accepted_waste.split(",")}
    if category.casefold() not in accepted_at_point:
        raise ValueError("This collection point does not accept the selected waste type.")
