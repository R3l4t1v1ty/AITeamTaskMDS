# simplify()
*base requirements of task*

Intuitively, all the base rules seem like they reduce an expression in some way. Either by literally reducing the number of nodes 
or by changing certain node in a way that brings it closer to the fixed point.

Now, mathematically we can define a certain positive integer weight W(expr) to each Expression and make
check what happens with that weight when we apply our rules. If that weight always
reduces after rule is applied, we have a proof that termination will always occur.

Atomic parts of our expression are constants and variables, we cannot transform
them in any way so they will have a minimum weight of 1:

`W(Const) = W(Var) = 1`

Pow and Mul have weight of their subexpressions + 1

`W(Pow(f,n)) = 1 + W(f)`

`W(Mul(f,g)) = 1 + W(f) + W(g)`

Finally, addition has weight of it's subexpressions + 2  


`W(Add(f,g)) = 2 + W(f) + W(g)`

*Addition cannot be 1 + W(f) + W(g) because it breaks the* `Add(x,x)` -> `Mul(2,x)` *rule*

#### Checking ruleset if it consistently reduces total weight of expression

| rule | W(left) → W(right)        |
|---|---------------------------|
| `Add(x,0)` → `x` | `3 + W(x)` → `W(x)`       |
| `Add(0,x)` → `x` | `3 + W(x)` → `W(x)`       |
| `Add(x,x)` → `Mul(2,x)` | `2 + 2·W(x)` → `2 + W(x)` |
| `Mul(x,1)` → `x` | `2 + W(x)` → `W(x)`       |
| `Mul(1,x)` → `x` | `2 + W(x)` → `W(x)`       |
| `Mul(x,0)` → `0` | `2 + W(x)` → `1`          |
| `Mul(0,x)` → `0` | `2 + W(x)` → `1`          |
| `Pow(x,1)` → `x` | `1 + W(x)` → `W(x)`       |
| `Pow(x,0)` → `1` | `1 + W(x)` → `1`          |
| `Add(c₁,c₂)` → `c₃` | `4` → `1`                 |
| `Mul(c₁,c₂)` → `c₃` | `3` → `1`                 |
| `Pow(c,n)` → `c′` | `2` → `1`                 |

As we can see, each rule strictly reduces weight of an expression. Because 
weight is defined as a positive integer, this means that after some finite 
number of rule application, the expression will reach it's stable point.

Now, the problem with this ruleset is that it cannot fully simplify every 
possible expression we can make, for example:

`x^2+x+x^2`

Won't be transformed into 

`2x^2+x`

Because there are no rules for commutativity (and associativity). This ruleset can merge terms of 
same degree only if they are adjacent to each other. 

This issue inspired me to write another simplify function, with additional
rules that add commutativity, associativity and distributivity. 

# simplify2()

Now addition of commutativity, associativity and distributivity required addition of
a lot more rules. 

### Lexicographical ordering
Problems with commutativity and associativity rules is that they cannot stop reordering expression.
For example:

`a+b` -> `b+a` -> `a+b` -> ...

To solve that issue, we need to introduce lexicographical order of our expressions.
That's done with Expression.key() method and the point of it is that it makes commutativity and associativity rules
essentially sort our expression. The lexicographically lower Expressions will be floated to the front of the expression.

This gives us variable I that measures inversions from perfectly sorted form. Whenever
any of the rules swaps two expressions, it brings our expression closer to 0 inversion state
meaning these rules reduce measure I.

### Association Left vs Right
I decided to make right association what our expression is going to strive to. That means
we can have some value L depicting how many nodes are still associated to the left. Whenever
our rules change one association from left to right, L will be reduced.

### New interpretation
Problems with distributivity rules is that they expand our expressions. From one simple power we can get 
100 new additions. This means we have to think of another way to give values to expressions.

`[Const] = [Var] = 2`

`[f+g] = [f]+[g]+1`

`[f*g] = [f]*[g]`

`[f^n]` = (`(n+1)*[f]^n` if `[f]>2 else` `[f]^n`) if `n > 0` else `[f]`

##### Distributivity

```
[left] = [a·(f+g)] = [a]·([f] + [g] + 1) = [a][f] + [a][g] + [a]
[right] = [a·f + a·g] = [a][f] + [a][g] + 1
[left] - [right] = [a] - 1 >= 1
```
This means every time distribution is used to unpack, interpretation of the left side will always be larger than the right side
because `[a] >= 2` meaning, distributivity always reduces total interpretation of expression. 

##### Power expansion
*power expansion only happens on non-atomic expressions*
```
[left] = [Pow(f,n)] = [f]^n · (n+1)
[right] = [Mul(f, Pow(f,n−1))] = [f] · [f]^(n−1) · n = [f]^n · n
[left] - [right] = [f]^n >= 1
```
This means every time power expansion is used, interpretation of the left side will always be larger than the right side
because `[f] >= 2` and `n > 1` meaning, power expansion always reduces total interpretation of expression. 

### The Measure

Now we can create a measure M that measures what's happening with our expression.

We will define it as a hierarchical tuple: 

`M(e) = ([e],W(e),L(e),I(e))`

Meaning that when comparing two M's we first compare the first place, if it's equal we compare
the second place etc...


### Every rule strictly decreases M

The number of rules are pretty large by now, so splitting them into groups that act similarly 
can help with the visual clarity.

| rule class | `[e]` | `W` | `L` | `I` |
|---|:---:|:---:|:---:|:---:|
| **distributivity** (grows the tree) | **↓** | ↑ | — | — |
| **power expansion** (grows the tree) | **↓** | ↑ | — | — |
| constant folding, coefficient merges, `x+0`, … | **↓** | | | |
| **atomic** power merges (`x·x → x²`) | = | **↓** | | |
| re-association | = | = | **↓** | |
| ordered swap | = | = | = | **↓** |

Because `[e]` is the primary component, the two expanding rules decrease `M` even though the tree grows, the later components are never consulted.

This means after each rule is applied, M always reduces. Because all values in M are non-negative integers, at some point M
will reach final stable point.