class Environment:
    def __init__(self):
        self._vars = {}

    def define(self, name, val):
        self._vars[name] = val
        return val

    def val(self, name):
        return self._vars[name]


class Evaluator:
    def eval(self, expr, env):
        match expr:
            case None | bool() | int(): return expr
            case str(name): return env.val(name)
            case ("define", [name, expr]):
                return env.define(name, self.eval(expr, env))
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

    print("Variable:")

    print(toil.eval(("define", ["a", ("add", [2, 3])])))
    # -> 5

    print(toil.eval("a"))
    # -> 5

    print(toil.eval(("if", [("equal", ["a", 5]), 2, 3])))
    # -> 2

    print(toil.eval(("define", ["a", 6])))
    # -> 6

    print(toil.eval("a"))
    # -> 6

