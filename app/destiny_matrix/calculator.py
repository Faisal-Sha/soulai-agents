"""Validated Ladini Matrix of Destiny calculations."""

from typing import Dict, TypedDict

from .parser import DOB, DOBInput, parse_dob
from .utils import reduce_to_22, sum_digits


MatrixValues = Dict[str, int]


class CompatibilitySummary(TypedDict):
    person_a: MatrixValues
    person_b: MatrixValues
    pair_center: int
    relationship_energy: int
    challenge_area: int
    harmony_area: int
    growth_potential: int
    communication_style: int


def _derive_matrix(a: int, b: int, c: int, d: int, e: int) -> MatrixValues:
    """Derive the complete matrix from its five primary anchor points."""
    # Male and female lineage
    f = reduce_to_22(a + b)
    y = reduce_to_22(c + d)
    o = reduce_to_22(f + y)
    g = reduce_to_22(b + c)
    k = reduce_to_22(a + d)
    u = reduce_to_22(g + k)

    # Parent-child zone and karmic tail
    a1 = reduce_to_22(a + e)
    a2 = reduce_to_22(a + a1)
    d1 = reduce_to_22(d + e)
    d2 = reduce_to_22(d + d1)

    # Prosperity line
    c1 = reduce_to_22(c + e)
    x = reduce_to_22(d1 + c1)
    x1 = reduce_to_22(d1 + x)
    c2 = reduce_to_22(c + c1)
    x2 = reduce_to_22(x + c1)

    # Sexuality and additional lineage points
    e1 = reduce_to_22(f + g + y + k)
    e2 = reduce_to_22(e + e1)
    s1 = reduce_to_22(e1 + f)
    s2 = reduce_to_22(f + s1)
    s4 = reduce_to_22(y + e1)
    s3 = reduce_to_22(y + s4)
    p1 = reduce_to_22(g + e1)
    p2 = reduce_to_22(g + p1)
    p3 = reduce_to_22(k + e1)
    p4 = reduce_to_22(k + p3)

    # Talents and life purposes
    b1 = reduce_to_22(b + e)
    b2 = reduce_to_22(b + b1)
    h = reduce_to_22(b + d)
    j = reduce_to_22(a + c)
    m = reduce_to_22(h + j)
    n = reduce_to_22(f + y)
    t = reduce_to_22(g + k)
    z = reduce_to_22(n + t)
    s = reduce_to_22(m + z)

    # Health chart
    a3 = reduce_to_22(a1 + e)
    b3 = reduce_to_22(b1 + e)
    c3 = reduce_to_22(c1 + e)
    d3 = reduce_to_22(d1 + e)
    l = reduce_to_22(a + b)
    l1 = reduce_to_22(a2 + b2)
    l2 = reduce_to_22(a1 + b1)
    l3 = reduce_to_22(a3 + b3)
    l4 = reduce_to_22(e + e)
    l5 = reduce_to_22(d1 + c1)
    l6 = reduce_to_22(d + c)
    health_phys_total = reduce_to_22(a + a2 + a1 + a3 + e + c1 + c)
    health_energy_total = reduce_to_22(b + b2 + b1 + b3 + e + d1 + d)
    health_balance_total = reduce_to_22(l + l1 + l2 + l3 + l4 + l5 + l6)

    return {
        "a": a, "b": b, "c": c, "d": d, "e": e,
        "f": f, "y": y, "o": o, "g": g, "k": k, "u": u,
        "a1": a1, "a2": a2, "d1": d1, "d2": d2,
        "c1": c1, "c2": c2, "x": x, "x1": x1, "x2": x2,
        "e1": e1, "e2": e2,
        "s1": s1, "s2": s2, "s3": s3, "s4": s4,
        "p1": p1, "p2": p2, "p3": p3, "p4": p4,
        "b1": b1, "b2": b2,
        "h": h, "j": j, "m": m, "n": n, "t": t, "z": z, "s": s,
        "a3": a3, "b3": b3,
        "l": l, "l1": l1, "l2": l2, "l3": l3,
        "l4": l4, "l5": l5, "l6": l6,
        "healthPhysTotal": health_phys_total,
        "healthEnergyTotal": health_energy_total,
        "healthBalanceTotal": health_balance_total,
        "c3": c3, "d3": d3,
        # Aliases retained for parity with the web application.
        "center": e, "top": b, "left": a, "right": c, "bottom": d,
        "money": reduce_to_22(c + a),
        "love": reduce_to_22(b + c),
        "health": e,
    }


def calculate_matrix(date_of_birth: DOBInput) -> MatrixValues:
    """
    Calculate the complete personal Matrix of Destiny.

    The return value is a plain JSON-serializable dictionary and is suitable
    for direct use as an AI-agent tool result.
    """
    dob = parse_dob(date_of_birth)
    a = reduce_to_22(dob.day)
    b = dob.month
    c = reduce_to_22(sum_digits(dob.year))
    d = reduce_to_22(a + b + c)
    e = reduce_to_22(a + b + c + d)
    return _derive_matrix(a, b, c, d, e)


def calculate_compatibility_summary(
    first_dob: DOBInput, second_dob: DOBInput
) -> CompatibilitySummary:
    """Calculate the compact compatibility indicators used by the web app."""
    person_a = calculate_matrix(first_dob)
    person_b = calculate_matrix(second_dob)
    comp_a = reduce_to_22(person_a["a"] + person_b["a"])
    comp_b = reduce_to_22(person_a["b"] + person_b["b"])
    comp_c = reduce_to_22(person_a["c"] + person_b["c"])
    comp_d = reduce_to_22(person_a["d"] + person_b["d"])
    comp_e = reduce_to_22(person_a["e"] + person_b["e"])
    return {
        "person_a": person_a,
        "person_b": person_b,
        "pair_center": comp_e,
        "relationship_energy": reduce_to_22(comp_b + comp_c),
        "challenge_area": reduce_to_22(abs(person_a["c"] - person_b["c"])),
        "harmony_area": comp_b,
        "growth_potential": comp_d,
        "communication_style": comp_a,
    }


def calculate_compatibility_matrix(
    first_dob: DOBInput, second_dob: DOBInput
) -> MatrixValues:
    """Calculate the complete two-person compatibility matrix."""
    first = calculate_matrix(first_dob)
    second = calculate_matrix(second_dob)
    matrix = _derive_matrix(
        reduce_to_22(first["a"] + second["a"]),
        reduce_to_22(first["b"] + second["b"]),
        reduce_to_22(first["c"] + second["c"]),
        reduce_to_22(first["d"] + second["d"]),
        reduce_to_22(first["e"] + second["e"]),
    )

    # Match the Avatarium-compatible overrides in src/core/calc.ts.
    for key in ("f", "g", "y", "k"):
        matrix[key] = reduce_to_22(first[key] + second[key])
    matrix["o"] = reduce_to_22(matrix["f"] + matrix["y"])
    matrix["u"] = reduce_to_22(matrix["g"] + matrix["k"])
    matrix["e1"] = reduce_to_22(
        matrix["f"] + matrix["g"] + matrix["y"] + matrix["k"]
    )
    matrix["e2"] = reduce_to_22(matrix["e"] + matrix["e1"])
    matrix["n"] = reduce_to_22(matrix["f"] + matrix["y"])
    matrix["t"] = reduce_to_22(matrix["g"] + matrix["k"])
    matrix["z"] = reduce_to_22(matrix["n"] + matrix["t"])
    matrix["s"] = reduce_to_22(matrix["m"] + matrix["z"])
    matrix["s1"] = reduce_to_22(matrix["e1"] + matrix["f"])
    matrix["s2"] = reduce_to_22(matrix["f"] + matrix["s1"])
    matrix["s4"] = reduce_to_22(matrix["y"] + matrix["e1"])
    matrix["s3"] = reduce_to_22(matrix["y"] + matrix["s4"])
    matrix["p1"] = reduce_to_22(matrix["g"] + matrix["e1"])
    matrix["p2"] = reduce_to_22(matrix["g"] + matrix["p1"])
    matrix["p3"] = reduce_to_22(matrix["k"] + matrix["e1"])
    matrix["p4"] = reduce_to_22(matrix["k"] + matrix["p3"])
    return matrix


def calculate_message_of_the_day_matrix(
    user_dob: DOBInput, today_dob: DOBInput
) -> MatrixValues:
    """Port of the web app's Message-of-the-Day matrix calculation."""
    user_matrix = calculate_matrix(user_dob)
    day_matrix = calculate_matrix(today_dob)
    matrix = _derive_matrix(
        *(
            reduce_to_22(user_matrix[key] + day_matrix[key])
            for key in ("a", "b", "c", "d", "e")
        )
    )
    for key in matrix:
        matrix[key] = reduce_to_22(user_matrix[key] + day_matrix[key])
    return matrix
