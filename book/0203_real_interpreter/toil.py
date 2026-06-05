class Scanner:
    def __init__(self, src):
        self._src = src
        self._start_pos = 0
        self._current_pos = 0
        self._tokens = []

    def tokenize(self):
        while True:
            self._start_pos = self._current_pos
            match self._current_char():
                case "$EOF":
                    self._tokens.append("$EOF")
                    break
                case c if c.isdecimal(): self._number()
                case invalid:
                    assert False, f"Invalid character @ tokenize(): {invalid}"

        return self._tokens

    def _number(self):
        while self._current_char().isdecimal(): self._advance()
        self._tokens.append(int(self._lexeme()))

    def _lexeme(self):
        return self._src[self._start_pos:self._current_pos]

    def _advance(self): self._current_pos += 1

    def _current_char(self):
        if self._current_pos < len(self._src):
            return self._src[self._current_pos]
        else:
            return "$EOF"


class Parser:
    def __init__(self, tokens):
        self._tokens = tokens
        self._pos = 0

    def parse(self):
        expr = self._expression()
        assert self._current_token() == "$EOF", \
            f"Extra token @ parse(): {self._current_token()}"
        return expr

    def _expression(self): return self._primary()

    def _primary(self):
        match self._current_token():
            case int(): return self._current_and_advance()
            case invalid:
                assert False, f"Invalid token @ _primary(): {invalid}"

    def _current_token(self): return self._tokens[self._pos]

    def _current_and_advance(self):
        self._pos += 1
        return self._tokens[self._pos - 1]


class Environment:
    def __init__(self, parent=None):
        self._parent = parent
        self._vars = {}

    def define(self, name, val):
        self._vars[name] = val
        return val

    def assign(self, name, val):
        if name in self._vars:
            self._vars[name] = val
            return val
        elif self._parent:
            return self._parent.assign(name, val)
        else:
            assert False, f"Undefined variable @ assign(): {name}"

    def val(self, name):
        if name in self._vars: return self._vars[name]
        elif self._parent:
            return self._parent.val(name)
        else:
            assert False, f"Undefined variable @ val(): {name}"


class Evaluator:
    def eval(self, expr, env):
        match expr:
            case None | bool() | int(): return expr
            case ("func", [params, body_expr]):
                return ("closure", [params, body_expr, env])
            case str(name): return env.val(name)
            case ("scope", [body_expr]):
                return self.eval(body_expr, Environment(env))
            case ("define", [name, expr]):
                return env.define(name, self.eval(expr, env))
            case ("assign", [name, expr]):
                return env.assign(name, self.eval(expr, env))
            case ("seq", exprs): return self._seq(exprs, env)
            case ("if", [cond_expr, then_expr, else_expr]):
                return self._if(cond_expr, then_expr, else_expr, env)
            case ("while", [cond_expr, body_expr]):
                return self._while(cond_expr, body_expr, env)
            case (op_expr, args_expr):
                return self._op(op_expr, args_expr, env)
            case _:
                assert False, f"Unexpected expression @ eval(): {expr}"

    def _seq(self, exprs, env):
        val = None
        for expr in exprs: val = self.eval(expr, env)
        return val

    def _if(self, cond_expr, then_expr, else_expr, env):
        if self.eval(cond_expr, env):
            return self.eval(then_expr, env)
        else:
            return self.eval(else_expr, env)

    def _while(self, cond_expr, body_expr, env):
        val = None
        while self.eval(cond_expr, env): val = self.eval(body_expr, env)
        return val

    def _op(self, op_expr, args_expr, env):
        op_val = self.eval(op_expr, env)
        args_val = [self.eval(arg, env) for arg in args_expr]
        match op_val:
            case c if callable(c):
                return op_val(args_val)
            case ("closure", [params, body_expr, closure_env]):
                new_env = Environment(closure_env)
                for param, arg in zip(params, args_val):
                    new_env.define(param, arg)
                return self.eval(body_expr, new_env)
            case _:
                assert False, f"Invalid operator @ _op(): {op_val}"


class Interpreter:
    def __init__(self):
        self._env = Environment()
        self._builtins()

    def _builtins(self):
        self._env.define("add", lambda args: args[0] + args[1])
        self._env.define("sub", lambda args: args[0] - args[1])
        self._env.define("mul", lambda args: args[0] * args[1])
        self._env.define("div", lambda args: args[0] // args[1])
        self._env.define("mod", lambda args: args[0] % args[1])
        self._env.define("equal", lambda args: args[0] == args[1])
        self._env.define("less", lambda args: args[0] < args[1])
        self._env.define("greater", lambda args: args[0] > args[1])
        self._env.define("print", lambda args: print(*args))

        self._env = Environment(self._env)

    def scan(self, src):
        return Scanner(src).tokenize()

    def parse(self, tokens):
        return Parser(tokens).parse()

    def ast(self, src):
        return self.parse(self.scan(src))

    def eval(self, expr):
        return Evaluator().eval(expr, self._env)

    def walk(self, src):
        return self.eval(self.ast(src))


if __name__ == "__main__":

    toil = Interpreter()

    # Example

    print("Scan numbers:")

    print(toil.scan(r""""""))  # -> ['$EOF']
    print(toil.scan(r"""2"""))  # -> [2, '$EOF']
    print(toil.scan(r"""02"""))  # -> [2, '$EOF']
    print(toil.scan(r"""23"""))  # -> [23, '$EOF']

    # print(toil.scan(r"""$"""))  # -> Invalid character
    # print(toil.scan(r"""2$"""))  # -> Invalid character

    print("Parse numbers:")

    print(toil.parse([2, "$EOF"])) # -> 2
    print(toil.parse([23, "$EOF"])) # -> 23

    # print(toil.parse([2, 34, "$EOF"])) # -> Extra token
    # print(toil.parse(['$EOF'])) # -> Invalid token

    print("AST:")

    print(toil.ast(r"""2"""))  # -> 2
    print(toil.ast(r"""23"""))  # -> 23

    print("Interpret numbers:")

    print(toil.walk(r"""2"""))  # -> 2
    print(toil.walk(r"""02"""))  # -> 2
    print(toil.walk(r"""23"""))  # -> 23

    # print(toil.walk(r"""$"""))  # -> Invalid character
    # print(toil.walk(r"""2$"""))  # -> Invalid character
    # print(toil.walk(r""""""))  # -> Invalid token
