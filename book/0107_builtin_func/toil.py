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

    def _op(self, op_expr, args_expr, env):
        op_val = self.eval(op_expr, env)
        args_val = [self.eval(arg, env) for arg in args_expr]
        return op_val(args_val)


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
        self._env.define("print", lambda args: print(*args))

        self._env = Environment(self._env)

    def eval(self, expr):
        return Evaluator().eval(expr, self._env)


if __name__ == "__main__":

    toil = Interpreter()

    # Example

    print("Built-in functions:")

    print(toil.eval("add"))
    # -> <function Interpreter._builtins.<locals>.<lambda> at ....>

    print(toil.eval(("add", [2, 3])))
    # -> 5

    print(toil.eval(("sub", [3, 2])))
    # -> 1

    print(toil.eval(("mul", [2, 3])))
    # -> 6

    print(toil.eval(("div", [6, 3])))
    # -> 2

    print(toil.eval(("mod", [7, 3])))
    # -> 1

    print(toil.eval(("equal", [2, 2])))
    # -> True

    print(toil.eval(("equal", [2, 3])))
    # -> False

    print(toil.eval(("less", [2, 2])))
    # -> False

    print(toil.eval(("less", [2, 3])))
    # -> True

    print(toil.eval(("print", [2])))
    # -> 2\nNone

    print(toil.eval(("print", [2, 3])))
    # -> 2 3\nNone

    toil.eval(("print", [("equal", [("add", [2, 3]), 5])]))
    # -> True

    toil.eval(("define", ["myadd", "add"]))
    print(toil.eval(("myadd", [2, 3])))
    # -> 5

    # toil.eval(("not_defined", []))
    # -> Undefined variable
