def clamp(value, min_value, max_value) -> int | float:
    return min(
        max_value,
        max(min_value, value)
    )

def normalize_axis(value, max_value) -> float:
    return clamp(value / max_value, 0, 1)

def split_centered_axis(axis_value) -> tuple[int | float]:
    forward = ((1 - axis_value) - 0.5) * 2
    forward = clamp(forward, 0, 1)

    backward = (axis_value - 0.5) * 2
    backward = clamp(backward, 0, 1)
    return forward, backward

def invert_axis(axis_value):
    return clamp(1 - axis_value, 0, 1)
