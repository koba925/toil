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

    def test_sequence(self):
        assert e.eval(("seq", [])) is None
        assert e.eval(("seq", [2])) == 2
        assert e.eval(("seq", [2, 3])) == 3
        assert e.eval(("seq", [2, ("seq", [3, 4])])) == 4

    def test_if(self):
        assert e.eval(("if", [True, 2, 3])) == 2
        assert e.eval(("if", [False, 2, 3])) == 3
        assert e.eval(("if", [("seq", [False, True]), 2, 3])) == 2
        assert e.eval(("if", [True, ("seq", [2, 3]), 4])) == 3
        assert e.eval(("if", [False, 2, ("if", [True, 3, 4])])) == 3

if __name__ == "__main__":
    pytest.main([__file__])
