class Evaluator:
    def eval(self, expr):
        match expr:
            case None | bool() | int(): return expr
            case _:
                assert False, f"Unexpected expression @ eval(): {expr}"

if __name__ == "__main__":

    e = Evaluator()

    # Example

    print("Constants:")

    print(e.eval(None))
    # -> None

    print(e.eval(True))
    # -> True

    print(e.eval(False))
    # -> False

    print(e.eval(2))
    # -> 2

    print(e.eval([]))
    # -> Unexpected expression
