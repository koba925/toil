from toil import Interpreter

i = Interpreter().init_env()

i.eval(("define", "cons", ("func", ["a", "d"],
    ("func", ["s"], ("if", ("equal", ["s", 0]), "a", "d"))
)))
i.eval(("define", "car", ("func", ["c"], ("c", [0]))))
i.eval(("define", "cdr", ("func", ["c"], ("c", [1]))))


i.eval(("define", "eval", ("func", ["expr", "env"],
    ("if", ("equal", [("type", ["expr"]), ("quote", "NoneType")]), "expr",
    ("if", ("equal", [("type", ["expr"]), ("quote", "bool")]), "expr",
    ("if", ("equal", [("type", ["expr"]), ("quote", "int")]), "expr", None))))
))

i.eval(("define", "env", None))
i.eval(("define", "walk", ("func", ["expr"], ("eval", ["expr", "env"]))))

if __name__ == "__main__":

    print(i.eval(("type", [None])))
    print(i.eval(("type", [True])))
    print(i.eval(("type", [2])))

    print(i.eval(("walk", [None])))
    print(i.eval(("walk", [True])))
    print(i.eval(("walk", [2])))
