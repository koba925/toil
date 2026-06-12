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

    def bind(self, params, args):
        for param, arg in zip(params, args):
            self.define(param, arg)


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
            case f if callable(f): return f(args_val)
            case ("closure", [params, body_expr, closure_env]):
                new_env = Environment(closure_env)
                new_env.bind(params, args_val)
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

    def eval(self, expr):
        return Evaluator().eval(expr, self._env)


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
