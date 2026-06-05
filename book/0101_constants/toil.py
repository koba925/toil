class Evaluator:
    def eval(self, expr):
        match expr:
            case None | bool() | int(): return expr
            case _:
                assert False, f"Unexpected expression @ eval(): {expr}"


if __name__ == "__main__":

    toil = Evaluator()

    # Example

    print("Constants:")

    print(toil.eval(None)) # -> None
    print(toil.eval(True)) # -> True
    print(toil.eval(False)) # -> False
    print(toil.eval(2)) # -> 2

    # print(toil.eval([])) # -> Unexpected expression
