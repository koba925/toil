import pytest
from toil import Interpreter

toil = Interpreter()

class TestTreeWalkInterpreter:
    def test_whitespace(self):
        assert toil.walk(r""" 2 """) == 2
        assert toil.walk("""\n2\n""") == 2

    def test_comment(self):
        assert toil.walk(r""" 2 # Comment """) == 2
        assert toil.walk(r"""
            # Comment
            2
            # Comment
        """) == 2

    def test_add_sub(self):
        assert toil.walk(r""" 2+3 """) == 5
        assert toil.walk(r""" 5 - 3 """) == 2
        assert toil.walk(r""" 2 + 3 + 4 """) == 9
        assert toil.walk(r""" 9 - 4 - 3 """) == 2
        assert toil.walk(r""" 2 + 3 - 4 """) == 1
        assert toil.walk(r""" 2 - 5 """) == -3

        with pytest.raises(AssertionError, match="Invalid token"):
            toil.walk(r""" 2 + """)
        with pytest.raises(AssertionError, match="Invalid token"):
            toil.walk(r""" 2 - + 3 """)
        with pytest.raises(AssertionError, match="Invalid token"):
            toil.walk(r""" -2 """)

    def test_numbers(self):
        assert toil.walk(r""" 2 """) == 2
        assert toil.walk(r""" 02 """) == 2
        assert toil.walk(r""" 23 """) == 23

    def test_empty_source(self):
        with pytest.raises(AssertionError, match="Invalid token"):
            toil.walk(r"""""")
        with pytest.raises(AssertionError, match="Invalid token"):
            toil.walk(r""" """)

    def test_invalid_characters(self):
        with pytest.raises(AssertionError, match="Invalid character"):
            toil.walk(r""" $ """)
        with pytest.raises(AssertionError, match="Invalid character"):
            toil.walk(r""" 2$ """)

    def test_extra_token(self):
        with pytest.raises(AssertionError, match="Extra token"):
            toil.walk(r""" 2 34 """)


if __name__ == "__main__":
    pytest.main([__file__])
