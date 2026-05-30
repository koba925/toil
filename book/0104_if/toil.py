class Evaluator:
    def eval(self, expr):
        match expr:
            case None | bool() | int(): return expr
            case ("seq", exprs): return self._seq(exprs)
            case ("if", [cond_expr, then_expr, else_expr]):
                return self._if(cond_expr, then_expr, else_expr)
            case ("add", [a, b]): return self.eval(a) + self.eval(b)
            case ("equal", [a, b]): return self.eval(a) == self.eval(b)
            case ("print", [a]): return print(self.eval(a))
            case _:
                assert False, f"Unexpected expression @ eval(): {expr}"

    def _seq(self, exprs):
        val = None
        for expr in exprs: val = self.eval(expr)
        return val

    def _if(self, cond_expr, then_expr, else_expr):
        if self.eval(cond_expr):
            return self.eval(then_expr)
        else:
            return self.eval(else_expr)


if __name__ == "__main__":

    e = Evaluator()

    # Example

    print("If:")

    print(e.eval(("if", [("equal", [2, 2]), 3, 4])))
    # -> 3

    print(e.eval(("if", [("equal", [2, 3]), 4, 5])))
    # -> 5

    print(e.eval(("if", [True, ("seq", [2, 3]), 4])))
    # -> 3

    print(e.eval(("if", [False, 2, ("if", [True, 3, 4])])))
    # -> 3
