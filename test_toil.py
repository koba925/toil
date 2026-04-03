import pytest
from toil import Interpreter

class TestToil:
    @pytest.fixture(autouse=True)
    def set_interpreter(self):
        self.i = Interpreter().init_env()

    def test_evaluate_value(self):
        assert self.i.eval(None) is None
        assert self.i.eval(5) == 5
        assert self.i.eval(True) is True
        assert self.i.eval(False) is False

    def test_seq(self, capsys):
        self.i.eval(("seq", [
            ("print", [2]),
            ("print", [3])
        ]))
        assert capsys.readouterr().out == "2\n3\n"

    def test_evaluate_if(self):
        assert self.i.eval(("if", True, 2, 3)) == 2
        assert self.i.eval(("if", False, 2, 3)) == 3
        assert self.i.eval(("if", ("if", True, True, False), 2, 3)) == 2
        assert self.i.eval(("if", True, ("if", True, 2, 3), 4)) == 2
        assert self.i.eval(("if", False, 2, ("if", False, 3, 4))) == 4

    def test_evaluate_variable(self):
        assert self.i.eval(("define", "a", 2)) == 2
        assert self.i.eval("a") == 2

        assert self.i.eval(("define", "b", True)) == True
        assert self.i.eval(("if", "b", 2, 3)) == 2

        assert self.i.eval(("define", "c", ("if", False, 2, 3))) == 3
        assert self.i.eval("c") == 3

    def test_evaluate_undefined_variable(self):
        with pytest.raises(AssertionError):
            self.i.eval("a")

    def test_evaluate_scope(self, capsys):
        self.i.eval(("define", "a", 2))
        assert self.i.eval("a") == 2
        assert self.i.eval(("scope", "a")) == 2

        assert self.i.eval(("scope", ("seq", [
            ("print", ["a"]),
            ("define", "a", 3),
            ("print", ["a"]),
            ("define", "b", 4),
            ("print", ["b"]),
            "b"
        ]))) == 4
        assert capsys.readouterr().out == "2\n3\n4\n"

        assert self.i.eval("a") == 2

        with pytest.raises(AssertionError):
            self.i.eval("b")

    def test_builtin_functions(self, capsys):
        assert self.i.eval(("add", [2, 3])) == 5
        assert self.i.eval(("sub", [5, 3])) == 2
        assert self.i.eval(("mul", [2, 3])) == 6

        assert self.i.eval(("equal", [2, 2])) is True
        assert self.i.eval(("equal", [2, 3])) is False

        assert self.i.eval(("add", [2, ("mul", [3, 4])])) == 14

        self.i.eval(("print", [2, 3]))
        assert capsys.readouterr().out == "2 3\n"

        self.i.eval(("print", [("add", [5, 5])]))
        assert capsys.readouterr().out == "10\n"

    def test_user_func(self):
        self.i.eval(("define", "add2", ("func", ["a"],
            ("add", ["a", 2])
        )))
        assert self.i.eval(("add2", [3])) == 5

        self.i.eval(("define", "sum3", ("func",["a", "b", "c"],
            ("add", ["a", ("add", ["b", "c"])])
        )))
        assert self.i.eval(("sum3", [2, 3, 4])) == 9

    def test_recursion(self):
        self.i.eval(("define", "fac", ("func",["n"],
            ("if", ("equal", ["n", 1]),
                1,
                ("mul", ["n", ("fac", [("sub", ["n", 1])])])
            )
        )))
        assert self.i.eval(("fac", [1])) == 1
        assert self.i.eval(("fac", [3])) == 6
        assert self.i.eval(("fac", [5])) == 120

    def test_scope_leak(self):
        self.i.eval(("define", "x", 2))
        self.i.eval(("define", "f", ("func", ["x"], 3)))
        self.i.eval(("f", [4]))
        assert self.i.eval("x") == 2

    def test_closure(self):
        self.i.eval(("define", "x", 2))
        self.i.eval(("define", "return_x", ("func", [], "x")))
        assert self.i.eval(("return_x", [])) == 2
        assert self.i.eval(("scope", ("seq", [
            ("define", "x", 3),
            ("return_x", [])
        ]))) == 2
        assert self.i.eval("x") == 2

    def test_adder(self):
        self.i.eval(("define", "make_adder", ("func", ["n"],
            ("func", ["m"], ("add", ["n", "m"]))
        )))
        self.i.eval(("define", "add2", ("make_adder", [2])))
        self.i.eval(("define", "add3", ("make_adder", [3])))

        assert self.i.eval(("add2", [3])) == 5
        assert self.i.eval(("add3", [4])) == 7

    def test_shadowing(self):
        self.i.eval(("define", "make_shadow", ("func", ["x"],
            ("func", [],
                ("seq", [
                    ("define", "x", 3),
                    "x"
                ])
            )
        )))
        self.i.eval(("define", "g", ("make_shadow", [2])))
        assert self.i.eval(("g", [])) == 3
