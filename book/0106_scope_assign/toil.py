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
            case ("add", [a, b]): return self.eval(a, env) + self.eval(b, env)
            case ("equal", [a, b]): return self.eval(a, env) == self.eval(b, env)
            case ("print", [a]): return print(self.eval(a, env))
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


class Interpreter:
    def __init__(self):
        self._env = Environment()

    def eval(self, expr):
        return Evaluator().eval(expr, self._env)


if __name__ == "__main__":

    toil = Interpreter()

    # Example

    print("Scope and assignment:")

    toil.eval(("define", ["a", 2]))
    print(toil.eval(("assign", ["a", 3])))
    # -> 3
    print(toil.eval("a"))
    # -> 3

    # print(toil.eval(("assign", ["b", 2])))
    # -> Undefined variable

    print(toil.eval(("scope", ["a"])))
    # -> 3

    toil.eval(("scope", [("seq", [
        ("define", ["a", 4]),
        ("print", ["a"])
    ])]))
    # -> 4

    print(toil.eval("a"))
    # -> 3

    toil.eval(("scope", [("seq", [
        ("assign", ["a", 4]),
        ("print", ["a"])
    ])]))
    # -> 4

    print(toil.eval("a"))
    # -> 4

    toil.eval(("scope", [("seq", [
        ("define", ["b", 2]),
        ("print", ["b"])
    ])]))
    # -> 2

    # print(toil.eval("b"))
    # -> Undefined variable
