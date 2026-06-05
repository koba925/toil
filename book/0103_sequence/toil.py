class Evaluator:
    def eval(self, expr):
        match expr:
            case None | bool() | int(): return expr
            case ("seq", exprs): return self._seq(exprs)
            case ("add", [a, b]): return self.eval(a) + self.eval(b)
            case ("equal", [a, b]): return self.eval(a) == self.eval(b)
            case ("print", [a]): return print(self.eval(a))
            case _:
                assert False, f"Unexpected expression @ eval(): {expr}"

    def _seq(self, exprs):
        val = None
        for expr in exprs: val = self.eval(expr)
        return val


if __name__ == "__main__":

    toil = Evaluator()

    # Example

    print("Sequence:")

    print(toil.eval(("seq", []))) # -> None
    print(toil.eval(("seq", [("add", [2, 3])]))) # -> 5
    print(toil.eval(("seq", [("print", [2]), 3]))) # -> 2\n3
    print(toil.eval(("seq", [("print", [2]), ("seq", [("print", [3]), 4])])))
    # -> 2\n3\n4
