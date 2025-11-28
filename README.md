# SHABLANG: a little stack-based programming language

A very simple stack-based language, for learning about iterpreters, bytecode, etc.

## The language

The syntax is very simple: the code is split on whitespace, and whatever is left are the tokens.

The interpreter evaluates tokens one at a time, except for square brackets `[ ... ]`, which will
be described below.

Comments start with `#` and go until the end of the line.

Here are the valid tokens and their effects:

* Integer literals: `123`, `-26`, etc. These push the indicated value onto the stack.
* Boolean literals: `true`, `false`. Push the indicated value onto the stack.
* Function literal: `[` ...etc... `]`. Pushes a function (which is just a Python list of tokens, i.e. strings) onto the stack.
* Binary operators: `+`, `-`, `*`, `==`, `!=`, `<`, `&`, `|`, etc.
  Pops 2 values of the stack, pushes a result.
* Unary operators: `~`, `!`, etc. Pops 1 value from stack, pushes a result.
    * NOTE: `~` is negation, e.g. `3 ~` is equivalent to `-3`.
* Variable assignment: `=x`, `=my_variable`, etc. These pop a value off the stack & store it
  in the indicated variable. All variables are global.
* Variable reference: `x`, `my_variable`, etc. Pushes the indicated variable's value onto the stack.
* Function call: `@` pops a function off the top of the stack and executes it.
* Named function call: `@f`, `@my_function`, etc. Syntactic sugar for `f @`, `my_function @`, etc.
* Special commands:
    * `print`: pops a value & outputs it.
    * BOOL BODY `if`: if BOOL is truthy, executes BODY.
    * BOOL BODY1 BODY2 `ifelse`: if BOOL is truthy, executes BODY1, else executes BODY2.
    * COND BODY `while`: in a loop, execute COND, then pop a value from top of stack; if it's truthy,
      execute BODY and repeat; otherwise, exit the loop.

## Examples

### Math

This example results in a 3 on the stack:
```
1 2 +
```

### Variables

This example results in a 6 on the stack:
```
3 =x
x x +
```

### Conditionals

This example results in 200 being printed:
```
1 2 + 3 + =x
x 5 == [ 100 print ] if
x 6 == [ 200 print ] if
```

This example also results in 200 being printed:
```
1 2 + 3 + =x
x 6 == [ 200 print ] [ 100 print ] ifelse
```

This example results in 3, then 2, then 1 being printed:
```
3 =x
[ x 0 > ] [ x print  x 1 - =x ] while
```

### Functions

This example results in a 12 and a 9 on the stack:
```
[ 2 * ] =double
[ @double @double ] =quadruple
[ =x x x * ] =square

3 @quadruple
3 @square
```

Here's a classic recursive fibonacci implementation:
```
[ =x
    x 1 <= [ 1 ] [ x 1 - @fib x 2 - @fib + ] ifelse
] =fib

0 =i
[ i 6 <= ] [
    i @fib print
    i 1 + =i
] while
```

...its output is:
```
1
1
2
3
5
8
13
```

...wheeee!

## How to run it

I recommend using a fresh virtualenv, and ipython:
```
python3 -m venv venv
. venv/bin/activate
pip install ipython
ipython
```

The way to run code is with `shablang.eval`, which you should pass a string of code to be evaluated.
The stack is returned.
You can also pass `debug=True` to see an execution trace.

```python
In [1]: from shablang import *

In [2]: eval('1 2 + =x   x x * =y   x y')
Out[2]: [3, 9]

In [3]: eval('[ 2 * ] =double    3 @double 4 @double +', debug=True)
=== Stack: 
=== Executing: [...]
=== Stack: ['2', '*']
=== Executing: =double
=== Stack: 
=== Executing: 3
=== Stack: 3
=== Executing: @double
===   Stack: 3
===   Executing: 2
===   Stack: 3 2
===   Executing: *
===   Stack: 6
===   Returning!..
=== Stack: 6
=== Executing: 4
=== Stack: 6 4
=== Executing: @double
===   Stack: 6 4
===   Executing: 2
===   Stack: 6 4 2
===   Executing: *
===   Stack: 6 8
===   Returning!..
=== Stack: 6 8
=== Executing: +
=== Stack: 14
=== Returning!..
Out[3]: [14]
```
