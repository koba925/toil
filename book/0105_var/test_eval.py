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

    def test_pseudo_func(self, capsys):
        assert toil.eval(("add", [2, 3])) == 5

        assert toil.eval(("equal", [2, 2])) == True
        assert toil.eval(("equal", [2, 3])) == False

        assert toil.eval(("print", [2])) == None
        assert capsys.readouterr().out == "2\n"

        toil.eval(("print", [("equal", [("add", [2, 3]), 5])]))
        assert capsys.readouterr().out == "True\n"

        with pytest.raises(AssertionError, match="Unexpected expression"):
            toil.eval(("sub", [3, 2]))

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

if __name__ == "__main__":
    pytest.main([__file__])
