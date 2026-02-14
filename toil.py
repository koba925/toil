class Scanner():
    def __init__(self, src):
        self._src = src
        self._pos = 0
        self._token = ""

    def next_token(self):
        self._token = ""

        match self._current_char():
            case "$EOF": return "$EOF"
            case c if c.isnumeric():
                self._append_char()
                while self._current_char().isnumeric():
                    self._append_char()
                return int(self._token)
            case invalid:
                assert False, f"Invalid Character @ next_token(): {invalid}"

    def _advance(self):
        self._pos += 1

    def _current_char(self):
        if self._pos < len(self._src):
            return self._src[self._pos]
        else:
            return "$EOF"

    def _append_char(self):
        self._token += self._current_char()
        self._advance()


class Parser:
    def __init__(self, src):
        self._scanner = Scanner(src)

    def parse(self):
        expr = self._scanner.next_token()
        assert self._scanner.next_token() == "$EOF", \
            f"Unexpected token at end @ parse()"
        return expr


class Environment:
    def __init__(self, parent=None):
        self._parent = parent
        self._vars = {}

    def __repr__(self):
        content = "__builtins__" if "__builtins__" in self._vars else \
                  ", ".join(self._vars)
        return f"[{content}]" + (f" < {self._parent}" if self._parent else "")

    def define(self, name, val):
        self._vars[name] = val
        return val

    def lookup(self, name):
        if name in self._vars:
            return self._vars[name]
        elif self._parent is not None:
            return self._parent.lookup(name)
        else:
            assert False, f"Undefined variable @ lookup(): {name}"

class Evaluator:
    def evaluate(self, expr, env):
        match expr:
            case None | bool() | int():
                return expr
            case str(name):
                return env.lookup(name)
            case ("define", str(name), val):
                return env.define(name, self.evaluate(val, env))
            case ("seq", exprs):
                return self._evaluate_seq(exprs, env)
            case ("if", cond_expr, then_expr, else_expr):
                return self._evaluate_if(cond_expr, then_expr, else_expr, env)
            case ("func", params, body):
                return ("closure", params, body, env)
            case ("scope", expr):
                return self.evaluate(expr, Environment(env))
            case (op_expr, args_expr):
                return self._eval_op(op_expr, args_expr, env)
            case unexpected:
                assert False, f"Unexpected expression @ evaluate(): {unexpected}"

    def _evaluate_seq(self, exprs, env):
        val = None
        for expr in exprs:
            val = self.evaluate(expr, env)
        return val

    def _evaluate_if(self, cond_expr, then_expr, else_expr, env):
        if self.evaluate(cond_expr, env):
            return self.evaluate(then_expr, env)
        else:
            return self.evaluate(else_expr, env)

    def _eval_op(self, op_expr, args_expr, env):
        op_val = self.evaluate(op_expr, env)
        args_val = [self.evaluate(arg, env) for arg in args_expr]

        match op_val:
            case c if callable(c):
                return c(args_val)
            case ("closure", params, body, closure_env):
                new_env = Environment(closure_env)
                for param, arg in zip(params, args_val):
                    new_env.define(param, arg)
                return self.evaluate(body, new_env)
            case _:
                assert False, f"Illegal operator @ eval_op(): {op_val}"

class Interpreter:
    def __init__(self):
        self._env = Environment()

    def init_env(self):
        self._env.define("__builtins__", None)
        self._env.define("add", lambda args: args[0] + args[1])
        self._env.define("sub", lambda args: args[0] - args[1])
        self._env.define("mul", lambda args: args[0] * args[1])
        self._env.define("equal", lambda args: args[0] == args[1])
        self._env.define("print", lambda args: print(*args))

        self._env = Environment(self._env)
        return self

    def evaluate(self, expr):
        return Evaluator().evaluate(expr, self._env)

    def go(self, src):
        return self.evaluate(Parser(src).parse())


if __name__ == "__main__":
    i = Interpreter().init_env()

    print(i.go("2")) # -> 2
    print(i.go("23")) # -> 23
    print(i.go("a")) # -> Error
