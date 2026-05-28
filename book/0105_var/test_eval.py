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

    def test_sequence(self):
        assert toil.eval(("seq", [])) is None
        assert toil.eval(("seq", [2])) == 2
        assert toil.eval(("seq", [2, 3])) == 3
        assert toil.eval(("seq", [2, ("seq", [3, 4])])) == 4

    def test_if(self):
        assert toil.eval(("if", [True, 2, 3])) == 2
        assert toil.eval(("if", [False, 2, 3])) == 3
        assert toil.eval(("if", [("seq", [False, True]), 2, 3])) == 2
        assert toil.eval(("if", [True, ("seq", [2, 3]), 4])) == 3
        assert toil.eval(("if", [False, 2, ("if", [True, 3, 4])])) == 3

if __name__ == "__main__":
    pytest.main([__file__])
