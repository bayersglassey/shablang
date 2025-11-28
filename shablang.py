import sys
from typing import List, Dict, Union, Iterable


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

# Code we can evaluate
Code = Union[str, Iterable[Token]]

# A value in our language
Value = Union[int, bool, List[Token]]

# A call stack is just a mapping from variable names to values
CallStackFrame = Dict[str, Value]


def parse(code: str) -> List[Token]:
    """Parses some code, returning tokens.
    For our simple language, tokens are also like "byte codes"!"""
    lines = code.splitlines()
    tokens = []
    for line in lines:
        # Comments begin with '#' and go till the end of the line
        line = line.split('#', 1)[0]
        tokens.extend(line.split())
    return tokens


def eval(code: Code, *, debug=False):
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

    # These are the state of our VM.
    # Values can be pushed onto / popped from a "value stack", and there is
    # a "call stack" of stack frames.
    # Each stack frame is a mapping from variable names to values.
    # When we call a function, it pushes a fresh stack frame.
    # When you refer to a variable, we search for it up the call stack.
    # When you assign to a variable, it is set in the latest stack frame.
    value_stack = []
    call_stack = []

    # Add the first stack frame.
    # If we wanted some default global values, we could add them here.
    global_frame = {}
    call_stack.append(global_frame)

    _eval_inner(code, value_stack, call_stack, debug)
    return value_stack


def _eval_inner(code: Code, value_stack: List[Value], call_stack: List[CallStackFrame], debug, calldepth=0):
    """The inner loop of our VM"""

    # Get tokens from code
    if isinstance(code, str):
        tokens = parse(code)
    else:
        tokens = code

    # Convert e.g. list to iterator, so we can grab the next token using `next(tokens)`
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
        _eval_inner(func, value_stack, call_stack, debug, calldepth+1)

        if new_frame:
            call_stack.pop()

    def debug_print(msg, force=False):
        if debug or force:
            print('=== ' + '  ' * calldepth + msg)
    def debug_print_stack(force=False):
        debug_print(f"Stack: {' '.join(map(str, value_stack))}", force=force)

    for token in tokens:
        if token == '_end_of_line':
            # Included by the REPL at the end of each line of user input.
            # Just gives us a way to print the stack so user can see that
            # before typing more input.
            debug_print_stack(force=True)
            continue
        debug_print_stack()
        debug_print(f"Executing: {'[...]' if token == '[' else token}")
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
        elif token == '_debug_print':
            print(f"Call stack: {call_stack}")
            print(f"Value stack: {value_stack}")
        elif token == 'print':
            value = value_stack.pop()
            print(value)
        elif token == 'true':
            value_stack.append(True)
        elif token == 'false':
            value_stack.append(False)
        elif token == 'dup':
            value_stack.append(value_stack[-1])
        elif token == 'drop':
            value_stack.pop()
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
                if token == '_end_of_line':
                    continue
                elif token == '[':
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

    debug_print_stack()
    debug_print("Returning!..")

    return value_stack


def repl(debug=False):
    def iter_tokens():
        while True:
            line = input(': ')
            tokens = parse(line)
            if tokens:
                for token in tokens:
                    yield token
                yield '_end_of_line'
    try:
        eval(iter_tokens(), debug=debug)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    debug = False
    for arg in sys.argv[1:]:
        if arg == '--debug':
            debug = True
    repl(debug=debug)
