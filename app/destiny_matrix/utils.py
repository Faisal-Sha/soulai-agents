"""Numeric helpers used by the Matrix of Destiny calculator."""


def sum_digits(value: int) -> int:
    """Return the sum of the decimal digits of an integer."""
    return sum(int(digit) for digit in str(abs(int(value))))


def reduce_to_22(value: int) -> int:
    """
    Apply the exact 22-reduction used by the validated TypeScript engine.

    Values from 1 through 22 are retained. Larger values are repeatedly
    reduced by summing their digits. Zero is represented as energy 22.
    """
    result = abs(int(value))
    while result > 22:
        result = sum_digits(result)
    return 22 if result == 0 else result


def reduce_to_9(value: int) -> int:
    """Reduce an integer to 1..9, representing zero as 9."""
    result = abs(int(value))
    while result > 9:
        result = sum_digits(result)
    return 9 if result == 0 else result
