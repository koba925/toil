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


if __name__ == "__main__":
    i = Interpreter().init_env()

    i.evaluate(("print", [
        ("define", "add2", ("func",["a"], ("add", ["a", 2]))
    )])) # -> ('closure', ...)
    i.evaluate(("print", [("add2", [3])])) # -> 5

    i.evaluate(("define", "sum3", ("func", ["a", "b", "c"],
            ("add", ["a", ("add", ["b", "c"])]))
    ))
    i.evaluate(("print", [("sum3", [2, 3, 4])])) # -> 9

    i.evaluate(("define", "fac", ("func",["n"],
        ("if", ("equal", ["n", 1]),
            1,
            ("mul", ["n", ("fac", [("sub", ["n", 1])])])
        )
    )))
    i.evaluate(("print", [("fac", [1])])) # -> 1
    i.evaluate(("print", [("fac", [3])])) # -> 6
    i.evaluate(("print", [("fac", [5])])) # -> 120

    i.evaluate(("define", "make_adder", ("func", ["x"],
        ("func", ["y"], ("add", ["x", "y"]))
    )))
    i.evaluate(("define", "add10", ("make_adder", [10])))
    i.evaluate(("print", [("add10", [5])])) # -> 15
