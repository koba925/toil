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
    def eval(self, expr, env):
        match expr:
            case None | bool() | int():
                return expr
            case str(name):
                return env.lookup(name)
            case ("quote", expr):
                return expr
            case ("define", str(name), val):
                return env.define(name, self.eval(val, env))
            case ("seq", exprs):
                return self._seq(exprs, env)
            case ("if", cond_expr, then_expr, else_expr):
                return self._if(cond_expr, then_expr, else_expr, env)
            case ("func", params, body):
                return ("closure", params, body, env)
            case ("scope", expr):
                return self.eval(expr, Environment(env))
            case (op_expr, args_expr):
                return self._op(op_expr, args_expr, env)
            case unexpected:
                assert False, f"Unexpected expression @ evaluate(): {unexpected}"

    def _seq(self, exprs, env):
        val = None
        for expr in exprs:
            val = self.eval(expr, env)
        return val

    def _if(self, cond_expr, then_expr, else_expr, env):
        if self.eval(cond_expr, env):
            return self.eval(then_expr, env)
        else:
            return self.eval(else_expr, env)

    def _op(self, op_expr, args_expr, env):
        op_val = self.eval(op_expr, env)
        args_val = [self.eval(arg, env) for arg in args_expr]

        match op_val:
            case c if callable(c):
                return c(args_val)
            case ("closure", params, body, closure_env):
                new_env = Environment(closure_env)
                for param, arg in zip(params, args_val):
                    new_env.define(param, arg)
                return self.eval(body, new_env)
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

        self._env.define("type", lambda args: type(args[0]).__name__)

        self._env.define("print", lambda args: print(*args))

        self._env = Environment(self._env)
        return self

    def eval(self, expr):
        return Evaluator().eval(expr, self._env)


if __name__ == "__main__":
    i = Interpreter().init_env()

    i.eval(("print", [
        ("define", "add2", ("func",["a"], ("add", ["a", 2]))
    )])) # -> ('closure', ...)
    i.eval(("print", [("add2", [3])])) # -> 5

    i.eval(("define", "sum3", ("func", ["a", "b", "c"],
            ("add", ["a", ("add", ["b", "c"])]))
    ))
    i.eval(("print", [("sum3", [2, 3, 4])])) # -> 9

    i.eval(("define", "fac", ("func",["n"],
        ("if", ("equal", ["n", 1]),
            1,
            ("mul", ["n", ("fac", [("sub", ["n", 1])])])
        )
    )))
    i.eval(("print", [("fac", [1])])) # -> 1
    i.eval(("print", [("fac", [3])])) # -> 6
    i.eval(("print", [("fac", [5])])) # -> 120

    i.eval(("define", "make_adder", ("func", ["x"],
        ("func", ["y"], ("add", ["x", "y"]))
    )))
    i.eval(("define", "add10", ("make_adder", [10])))
    i.eval(("print", [("add10", [5])])) # -> 15
