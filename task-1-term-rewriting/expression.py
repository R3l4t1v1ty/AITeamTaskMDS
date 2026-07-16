from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

class Expression(ABC):
    @abstractmethod
    def __str__(self) -> str: ...
    @abstractmethod
    def key(self) -> tuple: ...
    @abstractmethod
    def diff(self, wrt) -> Expression: ...
    @abstractmethod
    def simplify(self) -> Expression: ...
    @abstractmethod
    def simplify2(self) -> Expression: ...


@dataclass(frozen=True)
class Const(Expression):
    value: float
    rank: ClassVar[int] = 0

    def __str__(self) -> str:
        return f'{self.value}' if self.value.is_integer() else f'{self.value:.2f}'

    def key(self) -> tuple:
        return tuple([self.rank,repr(self)])

    def diff(self, wrt: str) -> Expression:
        return Const(0)

    def simplify(self) -> Expression:
        return self

    def simplify2(self) -> Expression:
        return self


@dataclass(frozen=True)
class Var(Expression):
    name: str
    rank: ClassVar[int] = 1

    def __str__(self) -> str:
        return self.name

    def key(self) -> tuple:
        return tuple([self.rank,repr(self)])

    def diff(self, wrt) -> Expression:
        return Const(1) if self.name == wrt else Const(0)

    def simplify(self) -> Expression:
        return self

    def simplify2(self) -> Expression:
        return self


@dataclass(frozen=True)
class Pow(Expression):
    f: Expression
    n: float
    rank: ClassVar[int] = 2

    def __str__(self) -> str:
        return f'({self.f})^{self.n}'

    def key(self) -> tuple:
        return self.f.key() + (self.rank, self.n)

    def diff(self, wrt: str) -> Expression:

        return Mul(Mul(Const(self.n),Pow(self.f,self.n-1)),self.f.diff(wrt))# if self.n != 0 else Const(0)

    def simplify(self) -> Expression:
        simp_f = self.f.simplify()

        match Pow(simp_f,self.n):
            case Pow(x,1):
                return x
            case Pow(x,0):
                return Const(1)
            case Pow(Const(x),n) if not (x == 0 and n < 0):
                return Const(x**n)
            case other:
                return other

    def simplify2(self) -> Expression:

        simp_f = self.f.simplify2()

        match Pow(simp_f,self.n):
            case Pow(x,1):
                return x
            case Pow(x,0):
                return Const(1)
            case Pow(Const(x),n) if not (x == 0 and n < 0):
                return Const(x**n)
            case Pow(Var(x),n):
                return Pow(Var(x),n)
            case Pow(x,n) if n > 1:
                return Mul(x,Pow(x,n-1))
            case other:
                return other


@dataclass(frozen=True)
class Mul(Expression):
    f: Expression
    g: Expression
    rank: ClassVar[int] = 3

    def __str__(self) -> str:
        return f'({self.f}*{self.g})'

    def key(self) -> tuple:
        if isinstance(self.f,Const):
            return self.g.key() + (1,)
        return tuple([self.rank,repr(self)])

    def diff(self, wrt: str) -> Expression:

        return Add(Mul(self.f.diff(wrt),self.g),Mul(self.f,self.g.diff(wrt)))

    def simplify(self) -> Expression:

        simp_f, simp_g = self.f.simplify(), self.g.simplify()

        match Mul(simp_f,simp_g):
            case Mul(Const(0),_) | Mul(_,Const(0)):
                return Const(0)
            case Mul(x,Const(1)) | Mul(Const(1),x):
                return x
            case Mul(Const(a),Const(b)):
                return Const(a*b)
            case other:
                return other

    def simplify2(self) -> Expression:

        simp_f, simp_g = self.f.simplify2(), self.g.simplify2()

        match Mul(simp_f,simp_g):
            case Mul(Const(0),_): #reduce
                return Const(0)
            case Mul(Const(1),x): #reduce
                return x
            case Mul(Const(a),Const(b)): #reduce
                return Const(a*b)
            case Mul(a,b) if b.key() < a.key(): #reorder
                return Mul(b,a)
            case Mul(Var(a),Pow(Var(b),n)) if a==b: #reduce
                return Pow(Var(a),n+1)
            case Mul(Pow(Var(a),n),Pow(Var(b),m)) if a==b: #reduce
                return Pow(Var(a),n+m)
            case Mul(Mul(a,b),c): #reorder
                return Mul(a,Mul(b,c))
            case Mul(a,Mul(b,c)) if b.key() < a.key(): #reorder
                return Mul(b,Mul(a,c))
            case Mul(Const(a),Mul(Const(b),c)): #reduce
                return Mul(Const(a*b),c)
            case Mul(Var(a),Mul(Var(b),c)) if a==b: #reduce
                return Mul(Pow(Var(a),2),c)
            case Mul(Var(a),Var(b)) if a==b: #reduce
                return Pow(Var(a),2)
            case Mul(Var(a), Mul(Pow(Var(b),n), c)) if a == b: #reduce
                return Mul(Pow(Var(a), n + 1), c)
            case Mul(Pow(Var(a), n), Mul(Pow(Var(b), m), c)) if a == b: #reduce
                return Mul(Pow(Var(a), n + m), c)
            case Mul(Add(a,b),Add(c,d)):
                return Add(Mul(a,c),Add(Mul(a,d),Add(Mul(b,c),Mul(b,d))))
            case Mul(a,Add(b,c)):
                return Add(Mul(a,b),Mul(a,c))
            case other:
                return other


@dataclass(frozen=True)
class Add(Expression):
    f: Expression
    g: Expression
    rank: ClassVar[int] = 4

    def __str__(self) -> str:
        return f'({self.f}+{self.g})'

    def key(self) -> tuple:
        return tuple([self.rank,repr(self)])

    def diff(self, wrt: str) -> Expression:

        return Add(self.f.diff(wrt), self.g.diff(wrt))

    def simplify(self) -> Expression:

        simp_f, simp_g = self.f.simplify(), self.g.simplify()

        match Add(simp_f,simp_g):
            case Add(x,Const(0)) | Add(Const(0),x):
                return x
            case Add(Const(a),Const(b)):
                return Const(a+b)
            case Add(a,b) if a==b:
                return Mul(Const(2),a)
            case other:
                return other

    def simplify2(self) -> Expression:

        simp_f, simp_g = self.f.simplify2(), self.g.simplify2()

        match Add(simp_f,simp_g):
            case Add(Const(a),Const(b)): # reduce
                return Const(a+b)
            case Add(Const(0),x): # reduce
                return x
            case Add(a,b) if a==b: # reduce
                return Mul(Const(2),a)
            case Add(a,b) if b.key() < a.key(): # reorder
                return Add(b,a)
            case Add(a,Add(b,c)) if b.key() < a.key(): # reorder
                return Add(b,Add(a,c))
            case Add(Mul(Const(n),x),Mul(Const(m),y)) if x==y: #reduce
                return Mul(Const(n+m),x)
            case Add(x,Mul(Const(n),y)) if x==y: # reduce
                return Mul(Const(n+1),x)
            case Add(Const(a),Add(Const(b),c)): # reduce
                return Add(Const(a+b),c)
            case Add(a,Add(b,c)) if a==b: # reduce
                return Add(Mul(Const(2),a),c)
            case Add(a,Add(Mul(Const(n),b),c)) if a==b: # reduce
                return Add(Mul(Const(n+1),a),c)
            case Add(Mul(Const(n), a), Add(Mul(Const(m), b), c)) if a == b:
                return Add(Mul(Const(n + m), a), c)
            case other:
                return other


def diff(expr: Expression, wrt: str) -> Expression:

    return expr.diff(wrt)


def simplify(expr: Expression) -> Expression:
    prev = expr
    curr = expr.simplify()
    while prev != curr:
        prev = curr
        curr = curr.simplify()
    return curr


def simplify2(expr: Expression) -> Expression:
    prev = expr
    curr = expr.simplify2()
    while prev != curr:
        prev = curr
        curr = curr.simplify2()
    return curr



def main() -> None:
    x, y, z = Var("x"), Var("y"), Var("z")
    c0,c1,c2,c3,c4,c5 = Const(0), Const(1), Const(2), Const(3),Const(4),Const(5)

    # 2x^2+4x+1
    e1 = Add(Mul(c2,Pow(x,2)),Add(Mul(c4,x),c1))

    # (2x^2+4x+1)^2
    e2 = Pow(e1,2)

    # x^2*(x+1)^3
    e3 = Mul(Pow(x,2),Pow(Add(x,Const(1)),3))

    # 


    print(simplify2(diff(e1,'x')))
    print(simplify2(diff(e2,'x')))
    print(simplify2(diff(e3,'x')))
    print(simplify2(diff(Add(Mul(Const(2),x),Add(Mul(Const(3),x),Mul(Const(4),x))),'x')))

if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
