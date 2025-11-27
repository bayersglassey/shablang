import re
from typing import List, Dict, Any
from math import pi


UNARY_OPERATORS = {
    '~': lambda x: -x, # '-' is a binary operator, so we use '~' for unary negation!
    '!': lambda x: not x,
    'abs': abs,
    # ...etc...
}

BINARY_OPERATORS = {
    '+': lambda x, y: x + y,
    '-': lambda x, y: x - y,
    '*': lambda x, y: x * y,
    '/': lambda x, y: x / y,
    '==': lambda x, y: x == y,
    '!=': lambda x, y: x != y,
    '<': lambda x, y: x < y,
    '>': lambda x, y: x > y,
    '<=': lambda x, y: x <= y,
    '>=': lambda x, y: x >= y,
    '&': lambda x, y: x & y,
    '|': lambda x, y: x | y,
    'min': min,
    'max': max,
    # ...etc...
}


# A token of our language, also used directly as its "bytecodes"
Token = str

# A value in our language is just any Python value
Value = Any

# A call stack is just a mapping from variable names to values
CallStackFrame = Dict[str, Value]


def parse(code: str) -> List[Token]:
    """Parses some code, returning tokens.
    For our simple language, tokens are also like "byte codes"!"""
    return code.split()


def eval(code: str):
    """Evaluate some code in our language.
    Starts with a fresh, empty value stack, runs the given code (tokens),
    and returns the value stack.

        >>> eval('1 2 + 3 ==')
        [True]

        >>> eval('''
        ...     1 2 + =x
        ...     x x * =y
        ...     x y
        ... ''')
        [3, 9]

        >>> eval('''
        ...     [ =x
        ...         x 1 <= [ 1 ] [ x 1 - @fib x 2 - @fib + ] ifelse
        ...     ] =fib
        ...
        ...     0 =i
        ...     [ i 6 <= ] [
        ...         i @fib print
        ...         i 1 + =i
        ...     ] while
        ... ''')
        1
        1
        2
        3
        5
        8
        13
        []

    """
    tokens = parse(code)

    # These are the state of our VM.
    # Values can be pushed onto / popped from a "value stack", and there is
    # a "call stack" of stack frames.
    # Each stack frame is a mapping from variable names to values.
    # When we call a function, it pushes a fresh stack frame.
    # When you refer to a variable, we search for it up the call stack.
    # When you assign to a variable, it is set in the latest stack frame.
    value_stack = []
    call_stack = []

    # Add the first stack frame, and add some default "global" values to it.
    global_frame = {}
    global_frame['pi'] = pi
    call_stack.append(global_frame)

    _eval_inner(tokens, value_stack, call_stack)
    return value_stack


def _eval_inner(tokens: List[Token], value_stack: List[Value], call_stack: List[CallStackFrame]):
    """The inner loop of our VM"""

    # If we got a string, assume it's code, and parse it
    if isinstance(tokens, str):
        tokens = parse(tokens)

    # Convert list to iterator, so we can grab the next token using `next(tokens)`
    tokens = iter(tokens)

    # When we're called recursively, these are passed in
    if value_stack is None:
        value_stack = []
    if call_stack is None:
        call_stack = []

    def getvar(varname: str) -> Value:
        for frame in reversed(call_stack):
            # we're searching up through the call stack...
            if varname in frame:
                return frame[varname]
        raise NameError(varname)

    def call_func(func: List[Token], new_frame: bool = True):
        if new_frame:
            # Push a fresh stack frame
            call_stack.append({})

        # Recursively call the VM's inner loop, with the given function
        # (i.e. the given list of tokens)
        _eval_inner(func, value_stack, call_stack)

        if new_frame:
            call_stack.pop()

    for token in tokens:
        if token.isdigit() or token[0] == '-' and token[1:].isdigit():
            # int literal
            value_stack.append(int(token))
        elif token in UNARY_OPERATORS:
            operator = UNARY_OPERATORS[token]
            x = value_stack.pop()
            value_stack.append(operator(x))
        elif token in BINARY_OPERATORS:
            operator = BINARY_OPERATORS[token]
            y = value_stack.pop()
            x = value_stack.pop()
            value_stack.append(operator(x, y))
        elif token == 'debug_print':
            print(f"Call stack: {call_stack}")
            print(f"Value stack: {value_stack}")
        elif token == 'print':
            value = value_stack.pop()
            print(value)
        elif token == 'if':
            if_branch = value_stack.pop()
            value = value_stack.pop()
            if value:
                call_func(if_branch, new_frame=False)
        elif token == 'ifelse':
            else_branch = value_stack.pop()
            if_branch = value_stack.pop()
            value = value_stack.pop()
            if value:
                call_func(if_branch, new_frame=False)
            else:
                call_func(else_branch, new_frame=False)
        elif token == 'while':
            body = value_stack.pop()
            condition = value_stack.pop()
            while True:
                call_func(condition, new_frame=False)
                value = value_stack.pop()
                if not value:
                    break
                call_func(body, new_frame=False)
        elif token == '@':
            # Call the function on top of value stack
            func = value_stack.pop()
            call_func(func)
        elif token[0] == '@':
            # Call a function
            # NOTE: just syntactic sugar... "@f" is equivalent to "f @"
            varname = token[1:]
            func = getvar(varname)
            call_func(func)
        elif token == '[':
            # Parse a list, and push it onto the value stack
            token_list = [] # the list we'll push onto the stack
            depth = 1
            while True:
                token = next(tokens)
                if token == '[':
                    depth += 1
                elif token == ']':
                    depth -= 1
                    if depth <= 0:
                        break
                token_list.append(token)
            value_stack.append(token_list)
        elif token[0] == '=':
            # set variable value
            # e.g. "3 =x" sets the value of the variable "x" to 3
            varname = token[1:]
            value = value_stack.pop()
            call_stack[-1][varname] = value
        else:
            # get variable value, push it onto the value stack
            varname = token
            value = getvar(varname)
            value_stack.append(value)

    return value_stack
