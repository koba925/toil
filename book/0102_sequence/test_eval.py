import pytest
from toil import Evaluator

e = Evaluator()

class TestEvaluator:
    def test_constants(self):
        assert e.eval(None) is None
        assert e.eval(True) is True
        assert e.eval(False) is False
        assert e.eval(2) == 2

    def test_sequence(self):
        assert e.eval(("seq", [])) is None
        assert e.eval(("seq", [2])) == 2
        assert e.eval(("seq", [2, 3])) == 3
        assert e.eval(("seq", [2, ("seq", [3, 4])])) == 4

if __name__ == "__main__":
    pytest.main([__file__])
