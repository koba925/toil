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
                return env.define(name, expr)
            case ("seq", exprs): return self._seq(exprs, env)
            case ("if", [cond_expr, then_expr, else_expr]):
                return self._if(cond_expr, then_expr, else_expr, env)
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

    print(toil.eval(("define", ["a", True])))
    # -> True

    print(toil.eval("a"))
    # -> True

    print(toil.eval(("if", ["a", 2, 3])))
    # -> 2
