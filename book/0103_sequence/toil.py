class Evaluator:
    def eval(self, expr):
        match expr:
            case None | bool() | int(): return expr
            case ("seq", exprs): return self._seq(exprs)
            case _:
                assert False, f"Unexpected expression @ eval(): {expr}"

    def _seq(self, exprs):
        val = None
        for expr in exprs: val = self.eval(expr)
        return val

if __name__ == "__main__":

    e = Evaluator()

    # Example

    print("Sequence:")

    print(e.eval(("seq", [])))
    # -> None

    print(e.eval(("seq", [2])))
    # -> 2

    print(e.eval(("seq", [2, 3])))
    # -> 3

    print(e.eval(("seq", [2, ("seq", [3, 4])])))
    # -> 4

