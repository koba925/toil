import pytest
from toil import Interpreter

toil = Interpreter()

class TestEvaluator:
    def test_constants(self):
        assert toil.eval(None) is None
        assert toil.eval(True) is True
        assert toil.eval(False) is False
        assert toil.eval(2) == 2

        with pytest.raises(AssertionError, match="Unexpected expression"):
            toil.eval([])

    def test_sequence(self, capsys):
        assert toil.eval(("seq", [])) is None
        assert toil.eval(("seq", [("add", [2, 3])])) == 5

        assert toil.eval(("seq", [("print", [2]), 3])) == 3
        assert capsys.readouterr().out == "2\n"

        assert toil.eval(("seq", [("print", [2]), ("seq", [("print", [3]), 4])])) == 4
        assert capsys.readouterr().out == "2\n3\n"

    def test_if(self):
        assert toil.eval(("if", [("equal", [2, 2]), 3, 4])) == 3
        assert toil.eval(("if", [("equal", [2, 3]), 4, 5])) == 5
        assert toil.eval(("if", [True, ("seq", [2, 3]), 4])) == 3
        assert toil.eval(("if", [False, 2, ("if", [True, 3, 4])])) == 3

    def test_variable(self):
        assert toil.eval(("define", ["a", ("add", [2, 3])])) == 5
        assert toil.eval("a") == 5
        assert toil.eval(("if", [("equal", ["a", 5]), 2, 3])) == 2
        assert toil.eval(("define", ["a", 6])) == 6
        assert toil.eval("a") == 6

    def test_scope_and_assign(self, capsys):
        toil.eval(("define", ["a", 2]))
        assert toil.eval(("assign", ["a", 3])) == 3
        assert toil.eval("a") == 3

        with pytest.raises(AssertionError, match="Undefined variable"):
            toil.eval(("assign", ["b", 2]))

        assert toil.eval(("scope", ["a"])) == 3

        toil.eval(("scope", [("seq", [
            ("define", ["a", 4]),
            ("print", ["a"])
        ])]))
        assert capsys.readouterr().out == "4\n"

        assert toil.eval("a") == 3

        toil.eval(("scope", [("seq", [
            ("assign", ["a", 4]),
            ("print", ["a"])
        ])]))
        assert capsys.readouterr().out == "4\n"

        assert toil.eval("a") == 4

        toil.eval(("scope", [("seq", [
            ("define", ["b", 2]),
            ("print", ["b"])
        ])]))
        assert capsys.readouterr().out == "2\n"

        with pytest.raises(AssertionError, match="Undefined variable"):
            toil.eval("b")

    def test_builtins(self, capsys):
        assert toil.eval(("add", [2, 3])) == 5
        assert toil.eval(("sub", [3, 2])) == 1
        assert toil.eval(("mul", [2, 3])) == 6
        assert toil.eval(("div", [6, 3])) == 2
        assert toil.eval(("mod", [7, 3])) == 1

        assert toil.eval(("equal", [2, 2])) is True
        assert toil.eval(("equal", [2, 3])) is False

        assert toil.eval(("less", [2, 2])) is False
        assert toil.eval(("less", [2, 3])) is True

        assert toil.eval(("greater", [2, 2])) is False
        assert toil.eval(("greater", [3, 2])) is True

        assert toil.eval(("print", [2])) is None
        assert capsys.readouterr().out == "2\n"

        assert toil.eval(("print", [2, 3])) is None
        assert capsys.readouterr().out == "2 3\n"

        assert toil.eval(("print", [("equal", [("add", [2, 3]), 5])])) is None
        assert capsys.readouterr().out == "True\n"

        assert callable(toil.eval("add"))
        toil.eval(("define", ["myadd", "add"]))
        assert toil.eval(("myadd", [2, 3])) == 5

        with pytest.raises(AssertionError, match=r"Undefined variable @ val\(\): not_defined"):
            toil.eval(("not_defined", []))

if __name__ == "__main__":
    pytest.main([__file__])
