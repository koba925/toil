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

    def eval(self, expr):
        return Evaluator().eval(expr, self._env)


if __name__ == "__main__":

    toil = Interpreter()

    # Example

    print("While:")

    print(toil.eval(("seq", [
        ("define", ["i", 1]),
        ("while", [
            ("less", ["i", 4]),
            ("seq", [
                ("print", ["i"]),
                ("assign", ["i", ("add", ["i", 1])])
            ])
        ])
    ])))
    # -> 1\n2\n3\n4

    print(toil.eval(("seq", [
        ("define", ["i", 1]), ("define", ["sum", 0]),
        ("while", [
            ("less", ["i", 4]),
            ("seq", [
                ("assign", ["sum", ("add", ["sum", "i"])]),
                ("assign", ["i", ("add", ["i", 1])])
            ])
        ]),
        "sum"
    ])))
    # -> 6

    print(toil.eval(("while", [False, ("div", [1, 0])])))
    # -> None

    print(toil.eval(("seq", [
        ("define", ["i", 0]),
        ("while", [
            ("less", ["i", 2]),
            ("seq", [
                ("define", ["j", 0]),
                ("while", [
                    ("less", ["j", 3]),
                    ("seq", [
                        ("print", ["i", "j"]),
                        ("assign", ["j", ("add", ["j", 1])])
                    ])
                ]),
                ("assign", ["i", ("add", ["i", 1])])
            ])
        ])
    ])))
    # -> 0 0\n0 1\n0 2\n1 0\n1 1\n1 2\n2
