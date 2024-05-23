def calculate_recurring_interval(duration: int) -> str:
    if duration < 12:
        return "month"
    elif duration >= 12:
        return "year"
    else:
        raise ValueError("Duration out of range for Stripe recurring interval")