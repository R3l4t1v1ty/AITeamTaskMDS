"""
Tests for the symbolic differentiator / simplifier.

Runs either way:
    pytest test_expression.py          (preferred)
    python  test_expression.py         (no dependencies)

Layers:
    A. SPEC        - the rules required by the task
    B. MATHEMATICS - non-trivial expressions with known closed-form answers
    C. PROPERTIES  - invariants checked over randomly generated expressions
"""
from __future__ import annotations

import math
import random

import pytest

from expression import Expression, Const, Var, Add, Mul, Pow, diff, simplify, simplify2

C, V = Const, Var
x, y, z = V("x"), V("y"), V("z")


# --------------------------------------------------------------------------
# helper: numeric evaluation. This is the ground truth for the property tests.
# --------------------------------------------------------------------------
def ev(e: Expression, env: dict[str, float]) -> float:
    match e:
        case Const(v):     return float(v)
        case Var(n):       return env[n]
        case Add(f, g):    return ev(f, env) + ev(g, env)
        case Mul(f, g):    return ev(f, env) * ev(g, env)
        case Pow(f, n):    return ev(f, env) ** n
    raise TypeError(e)


# ==========================================================================
# A. SPEC - the mandatory rules
# ==========================================================================
@pytest.mark.parametrize("expr, expected", [
    (Add(x, C(0)),        x),                 # Add(x,0) -> x
    (Add(C(0), x),        x),                 # Add(0,x) -> x
    (Add(x, x),           Mul(C(2), x)),      # Add(x,x) -> 2x
    (Mul(x, C(1)),        x),                 # Mul(x,1) -> x
    (Mul(C(1), x),        x),                 # Mul(1,x) -> x
    (Mul(x, C(0)),        C(0)),              # Mul(x,0) -> 0
    (Mul(C(0), x),        C(0)),              # Mul(0,x) -> 0
    (Pow(x, 1),           x),                 # Pow(x,1) -> x
    (Pow(x, 0),           C(1)),              # Pow(x,0) -> 1
    (Add(C(2), C(3)),     C(5)),              # constant folding
    (Mul(C(4), C(7)),     C(28)),             # constant folding
])
def test_spec_rules(expr, expected):
    assert simplify(expr) == expected


def test_diff_does_not_simplify():
    """The task requires diff() to apply the rules verbatim, without simplifying."""
    assert diff(Pow(x, 3), "x") == Mul(Mul(C(3), Pow(x, 2)), C(1))
    assert diff(Add(x, y), "x") == Add(C(1), C(0))
    assert diff(Mul(x, y), "x") == Add(Mul(C(1), y), Mul(x, C(0)))


# ==========================================================================
# B. MATHEMATICS - non-trivial expressions with known answers
# ==========================================================================
def test_binomial_expansion():
    """(x+y)^5 must produce exactly the binomial coefficients 1,5,10,10,5,1."""
    got = simplify2(Pow(Add(x, y), 5))
    want = Add(Pow(x, 5),
           Add(Pow(y, 5),
           Add(Mul(C(10), Mul(Pow(x, 2), Pow(y, 3))),
           Add(Mul(C(10), Mul(Pow(x, 3), Pow(y, 2))),
           Add(Mul(C(5),  Mul(Pow(x, 4), y)),
               Mul(C(5),  Mul(x, Pow(y, 4))))))))
    assert got == want


def test_difference_of_squares():
    """(x+1)(x-1) = x^2 - 1.  The grammar has no subtraction, so -1 is Const(-1)."""
    assert simplify2(Mul(Add(x, C(1)), Add(x, C(-1)))) == Add(C(-1), Pow(x, 2))


def test_product_rule_and_chain_rule():
    """d/dx [x^2 (x+1)^3] = 5x^4 + 12x^3 + 9x^2 + 2x.
    Exercises the product rule and the chain rule at the same time."""
    d = simplify2(diff(Mul(Pow(x, 2), Pow(Add(x, C(1)), 3)), "x"))
    exact = lambda t: 5*t**4 + 12*t**3 + 9*t**2 + 2*t
    for t in (-2.0, -0.5, 0.3, 1.7, 3.1):
        assert math.isclose(ev(d, {"x": t}), exact(t), abs_tol=1e-9)


def test_power_rule_on_a_nested_power():
    assert simplify2(diff(Pow(Pow(x, 2), 3), "x")) == Mul(C(6), Pow(x, 5))


def test_partial_derivatives():
    """f = xy^2 + yz^2 + zx^2 is symmetric under the cycle x -> y -> z -> x."""
    f = Add(Add(Mul(x, Pow(y, 2)), Mul(y, Pow(z, 2))), Mul(z, Pow(x, 2)))
    assert simplify2(diff(f, "x")) == Add(Pow(y, 2), Mul(C(2), Mul(x, z)))
    assert simplify2(diff(f, "y")) == Add(Pow(z, 2), Mul(C(2), Mul(x, y)))


def test_derivative_wrt_absent_variable_is_zero():
    assert simplify2(diff(Add(Pow(x, 2), Mul(C(3), x)), "z")) == C(0)


def test_derivative_of_a_constant_expression_is_zero():
    assert simplify2(diff(Add(Mul(C(2), C(3)), C(4)), "x")) == C(0)


def test_second_derivative():
    """d2/dx2 x^4 = 12x^2"""
    d1 = simplify2(diff(Pow(x, 4), "x"))
    d2 = simplify2(diff(d1, "x"))
    assert d2 == Mul(C(12), Pow(x, 2))


# ==========================================================================
# C. PROPERTIES - invariants over random expressions
# ==========================================================================
# Depth and exponents are kept small on purpose: with expansion enabled,
# (x+y)^n blows up exponentially, so large random powers would time out.
# That is a complexity limit, not a termination bug (see TERMINATION.md).
def _rand_expr(depth: int, rng: random.Random) -> Expression:
    if depth <= 0 or rng.random() < 0.35:
        return rng.choice([x, y, z, C(0), C(1), C(2), C(3), C(-1)])
    match rng.choice(["add", "mul", "pow", "add", "mul"]):
        case "add": return Add(_rand_expr(depth-1, rng), _rand_expr(depth-1, rng))
        case "mul": return Mul(_rand_expr(depth-1, rng), _rand_expr(depth-1, rng))
        case _:     return Pow(_rand_expr(depth-1, rng), rng.choice([0, 1, 2, 3]))


def _corpus(n: int = 200) -> list[Expression]:
    rng = random.Random(2024)
    return [_rand_expr(rng.randint(1, 3), rng) for _ in range(n)]


def _points(n: int = 12) -> list[dict[str, float]]:
    rng = random.Random(7)
    return [{"x": rng.uniform(-2, 2), "y": rng.uniform(-2, 2), "z": rng.uniform(-2, 2)}
            for _ in range(n)]


@pytest.mark.parametrize("e", _corpus())
def test_simplify2_preserves_value(e):
    """The most important property: rewriting must never change what the
    expression MEANS. Checked by evaluating before and after at random points."""
    s = simplify2(e)
    for p in _points():
        try:
            before, after = ev(e, p), ev(s, p)
        except (ZeroDivisionError, OverflowError, ValueError):
            continue                     # undefined at this point, not a rewriting bug
        assert math.isclose(before, after, rel_tol=1e-6, abs_tol=1e-6)


@pytest.mark.parametrize("e", _corpus())
def test_simplify2_is_idempotent(e):
    """A fixed point must actually BE a fixed point."""
    s = simplify2(e)
    assert simplify2(s) == s


@pytest.mark.parametrize("e", _corpus())
def test_diff_matches_numeric_derivative(e):
    """Validate diff() against a central finite difference. This checks the
    differentiator INDEPENDENTLY of the rewriting machinery: if diff and
    simplify2 were both wrong in compensating ways, this would still catch it."""
    d = simplify2(diff(e, "x"))
    h = 1e-5
    for p in _points(6):
        lo, hi = dict(p), dict(p)
        lo["x"], hi["x"] = p["x"] - h, p["x"] + h
        try:
            numeric = (ev(e, hi) - ev(e, lo)) / (2 * h)
            symbolic = ev(d, p)
        except (ZeroDivisionError, OverflowError, ValueError):
            continue
        assert math.isclose(numeric, symbolic, rel_tol=1e-3, abs_tol=1e-3)


def _main() -> int:
    import inspect, sys, traceback

    passed = failed = 0
    for name, fn in sorted(globals().items()):
        if not (name.startswith("test_") and callable(fn)):
            continue
        cases = []
        for m in getattr(fn, "pytestmark", []):
            if m.name != "parametrize":
                continue
            names = m.args[0].replace(" ", "").split(",")
            for a in m.args[1]:
                values = a if len(names) > 1 else (a,)
                cases.append(dict(zip(names, values)))
        for kwargs in (cases or [{}]):
            try:
                fn(**kwargs)
                passed += 1
            except Exception:
                failed += 1
                print(f"FAIL {name}{kwargs or ''}")
                traceback.print_exc(limit=1)

    print(f"\n{'-' * 40}\npassed {passed} / {passed + failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())
