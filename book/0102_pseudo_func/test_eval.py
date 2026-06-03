import pytest
from toil import Evaluator

toil = Evaluator()

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


if __name__ == "__main__":
    pytest.main([__file__])
