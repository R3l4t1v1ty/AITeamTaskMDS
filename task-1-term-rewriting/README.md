# Task 1 — Symbolic differentiation and expression simplification

A symbolic differentiator and simplifier over the expression language

```
Expr ::= Const(value)
       | Var(name)
       | Add(left, right)
       | Mul(left, right)
       | Pow(base, exponent)
```

There is no parser, expressions are build in code.

## Files

| file | contents |
|---|---|
| `expression.py` | the expression classes, `diff`, `simplify`, `simplify2` |
| `test_expression.py` | test suite |
| `TERMINATION.md` | proof that `simplify` and `simplify2` always terminate |

## Running

```
python expression.py                # demo: differentiates a few expressions
pytest test_expression.py           # run the tests
```

Requires Python 3.14+. 

## Design

Every node is a frozen dataclass implementing an abstract `Expression` base class.
That gives us the following:

- expressions are immutable, so subexpressions can be shared safely between steps
- `__eq__` is generated automatically, and it compares trees structurally
- `diff`, `simplify` and `simplify2` are methods on the nodes rather than free functions with a type
switch, so each node knows its own rule and applies it through polymorphism. 

The module-level methods `diff`, `simplify`, `simplify2` exist
and are thin wrappers over them (`simplify` and `simplify2` handle stopping when
fixed point is reached).

Rules are expressed with structural pattern matching ( `match` / `case`), which lets
each rewrite rule be written close to the notation it is specified in:

```
case Add(x, Const(0)) | Add(Const(0), x):
    return x
```

## Part A - `diff(expr, wrt)`

Recursively applies the differentiation rules. 

```
diff(Pow(x, 3), "x")  # Mul(Mul(Const(3), Pow(x, 2)), Const(1))
```

## Part B - `simplify(expr)`

Recursively applies the required rewrite rules until a fixed point is reached. 
The driver loop compares the expression before and after each pass
and stops when nothing changes.

## Additional Part - `simplify2(expr)`

`simplify` applies only local rewrites. It cannot collect terms that are not siblings in the tree:

```
simplify(x**2 + x + x**2)      # unchanged: the two x^2 terms are in different branches
```

`simplify2` is an extension that adds:

- **commutativity**, as *ordered rewriting*: a swap that's happening only to bring
expression to lexicographically lower state in regard to key() member method of each expression.
- **associativity**, oriented to the right.
- **distributivity** and **expansion of powers of sums**, so the output is a fully expanded
  polynomial.

## Tests

`test_expression.py` has three layers:

- **spec** — the rules required by the task, plus a check that `diff` does not simplify;
- **mathematics** — the binomial theorem, the difference of squares, product rule combined
  with chain rule, partial derivatives, second derivatives;
- **properties** — invariants checked over randomly generated expressions:
  1. `simplify2` **preserves the value** of an expression (verified by numeric evaluation);
  2. `simplify2` is **idempotent**;
  3. `diff` agrees with a **numeric derivative**

## Assumptions

- The exponent of `Pow` is a plain number, not an `Expr`. 
- `wrt` is a variable name (a string), not a `Var` node.
- The language has no subtraction or division.
