import pytest
from toil import Interpreter

toil = Interpreter()

class TestTreeWalkInterpreter:
    def test_numbers(self):
        assert toil.walk(r""" 2 """) == 2
        assert toil.walk("""\n2\n""") == 2
        assert toil.walk(r""" 02 """) == 2
        assert toil.walk(r""" 23 """) == 23

        with pytest.raises(AssertionError, match="Invalid character"):
            toil.walk(r""" a """)
        with pytest.raises(AssertionError, match="Invalid character"):
            toil.walk(r""" 2a """)
        with pytest.raises(AssertionError, match="Invalid token"):
            toil.walk(r"""""")
        with pytest.raises(AssertionError, match="Invalid token"):
            toil.walk(r""" """)
        with pytest.raises(AssertionError, match="Extra token"):
            toil.walk(r""" 2 34 """)

if __name__ == "__main__":
    pytest.main([__file__])
