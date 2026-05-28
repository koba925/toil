class Evaluator:
    def eval(self, expr):
        match expr:
            case None | bool() | int(): return expr
            case ("add", [a, b]): return self.eval(a) + self.eval(b)
            case ("equal", [a, b]): return self.eval(a) == self.eval(b)
            case ("print", [a]): return print(self.eval(a))
            case _:
                assert False, f"Unexpected expression @ eval(): {expr}"

if __name__ == "__main__":

    e = Evaluator()

    # Example

    print("Pseudo Functions:")

    print(e.eval(("add", [2, 3])))
    # -> 5

    print(e.eval(("equal", [2, 2])))
    # -> True

    print(e.eval(("equal", [2, 3])))
    # -> False

    print(e.eval(("print", [2])))
    # -> 2\nNone

    e.eval(("print", [("equal", [("add", [2, 3]), 5])]))
    # -> True

    # e.eval(("sub", [3, 2]))
    # -> Unexpected expression
