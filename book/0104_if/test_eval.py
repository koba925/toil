import pytest
from toil import Evaluator

e = Evaluator()

class TestEvaluator:
    def test_constants(self):
        assert e.eval(None) is None
        assert e.eval(True) is True
        assert e.eval(False) is False
        assert e.eval(2) == 2

        with pytest.raises(AssertionError, match="Unexpected expression"):
            e.eval([])

    def test_pseudo_func(self, capsys):
        assert e.eval(("add", [2, 3])) == 5

        assert e.eval(("equal", [2, 2])) == True
        assert e.eval(("equal", [2, 3])) == False

        assert e.eval(("print", [2])) == None
        assert capsys.readouterr().out == "2\n"

        e.eval(("print", [("equal", [("add", [2, 3]), 5])]))
        assert capsys.readouterr().out == "True\n"

        with pytest.raises(AssertionError, match="Unexpected expression"):
            e.eval(("sub", [3, 2]))

    def test_sequence(self, capsys):
        assert e.eval(("seq", [])) is None
        assert e.eval(("seq", [("add", [2, 3])])) == 5

        assert e.eval(("seq", [("print", [2]), 3])) == 3
        assert capsys.readouterr().out == "2\n"

        assert e.eval(("seq", [("print", [2]), ("seq", [("print", [3]), 4])])) == 4
        assert capsys.readouterr().out == "2\n3\n"

    def test_if(self):
        assert e.eval(("if", [("equal", [2, 2]), 3, 4])) == 3
        assert e.eval(("if", [("equal", [2, 3]), 4, 5])) == 5
        assert e.eval(("if", [True, ("seq", [2, 3]), 4])) == 3
        assert e.eval(("if", [False, 2, ("if", [True, 3, 4])])) == 3

if __name__ == "__main__":
    pytest.main([__file__])
