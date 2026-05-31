import pytest
from toil import Interpreter

toil = Interpreter()

class TestTreeWalkInterpreter:
    def test_numbers(self):
        assert toil.walk(r"""2""") == 2
        assert toil.walk(r"""02""") == 2
        assert toil.walk(r"""23""") == 23

    def test_empty_source(self):
        with pytest.raises(AssertionError, match="Invalid token"):
            toil.walk(r"""""")

    def test_invalid_characters(self):
        with pytest.raises(AssertionError, match="Invalid character"):
            toil.walk(r"""$""")
        with pytest.raises(AssertionError, match="Invalid character"):
            toil.walk(r"""2$""")

if __name__ == "__main__":
    pytest.main([__file__])
