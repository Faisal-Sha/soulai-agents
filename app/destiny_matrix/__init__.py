"""Portable Python implementation of the project's Matrix of Destiny engine."""

from .calculator import (
    CompatibilitySummary,
    MatrixValues,
    calculate_compatibility_matrix,
    calculate_compatibility_summary,
    calculate_matrix,
    calculate_message_of_the_day_matrix,
)
from .parser import DOB, DOBInput, parse_dob, validate_dob
from .utils import reduce_to_9, reduce_to_22, sum_digits

__all__ = [
    "CompatibilitySummary",
    "DOB",
    "DOBInput",
    "MatrixValues",
    "calculate_compatibility_matrix",
    "calculate_compatibility_summary",
    "calculate_matrix",
    "calculate_message_of_the_day_matrix",
    "parse_dob",
    "reduce_to_9",
    "reduce_to_22",
    "sum_digits",
    "validate_dob",
]
