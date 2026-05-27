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

if __name__ == "__main__":
    pytest.main([__file__])
