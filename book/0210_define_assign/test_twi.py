import pytest
from toil import Interpreter

@pytest.fixture(autouse=True)
def setup_toil():
    global toil
    toil = Interpreter()

class TestTreeWalkInterpreter:
    # Ensure test independence
    def test_env_isolation_step1(self):
        assert toil.walk(r""" a := 2 """) == 2
    def test_env_isolation_step2(self):
        with pytest.raises(AssertionError, match="Undefined variable"):
            toil.walk(r""" a """)

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

    def test_define_assign(self):
        assert toil.walk(r""" a := 2 """) == 2
        assert toil.walk(r""" a """) == 2

        assert toil.walk(r""" a = 3 """) == 3
        assert toil.walk(r""" a """) == 3

        assert toil.walk(r""" b := c := 4 """) == 4
        assert toil.walk(r""" b """) == 4
        assert toil.walk(r""" c """) == 4

        assert toil.walk(r""" b = c = 5 """) == 5
        assert toil.walk(r""" b """) == 5
        assert toil.walk(r""" c """) == 5

        assert toil.walk(r""" a := 2 == 2 """) is True
        assert toil.walk(r""" a """) is True

        with pytest.raises(AssertionError, match="Undefined variable"):
            toil.walk(r""" not_defined = 3 """)
        with pytest.raises(AssertionError, match="Invalid token"):
            toil.walk(r""" a = = 3 """)
        with pytest.raises(AssertionError, match="Invalid token"):
            toil.walk(r""" a = """)
        with pytest.raises(AssertionError, match="Invalid token"):
            toil.walk(r""" = a """)

    def test_comparison(self):
        assert toil.walk(r""" 2 == 2 """) is True
        assert toil.walk(r""" 2 == 3 """) is False
        assert toil.walk(r""" None == None """) is True
        assert toil.walk(r""" None == True """) is False
        assert toil.walk(r""" True == True """) is True
        assert toil.walk(r""" True == False """) is False
        assert toil.walk(r""" False == False """) is True

        assert toil.walk(r""" 2 < 2 """) is False
        assert toil.walk(r""" 2 < 3 """) is True
        assert toil.walk(r""" 2 > 2 """) is False
        assert toil.walk(r""" 3 > 2 """) is True

        assert toil.walk(r""" 2 == 2 == 2 """) is False
        assert toil.walk(r""" 2 == 2 == True """) is True
        assert toil.walk(r""" 2 + 3 == 5 """) is True
        assert toil.walk(r""" 2 < 3 == True """) is True

        with pytest.raises(AssertionError, match="Invalid token"):
            toil.walk(r""" 2 == == 2 """)
        with pytest.raises(AssertionError, match="Invalid token"):
            toil.walk(r""" == 2 """)
        with pytest.raises(AssertionError, match="Invalid token"):
            toil.walk(r""" 2 == """)

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

    def test_mul_div_mod(self):
        assert toil.walk(r""" 2 * 3 """) == 6
        assert toil.walk(r""" 6 / 2 """) == 3
        assert toil.walk(r""" 7 % 3 """) == 1
        assert toil.walk(r""" 2 * 3 * 4 """) == 24
        assert toil.walk(r""" 24 / 4 / 2 """) == 3
        assert toil.walk(r""" 4 * 3 / 2 """) == 6
        assert toil.walk(r""" 2 + 3 * 4 """) == 14
        assert toil.walk(r""" 2 * 3 + 4 """) == 10

        with pytest.raises(AssertionError, match="Invalid token"):
            toil.walk(r""" 2 * * 3 """)
        with pytest.raises(AssertionError, match="Invalid token"):
            toil.walk(r""" / 3 """)

    def test_numbers(self):
        assert toil.walk(r""" 2 """) == 2
        assert toil.walk(r""" 02 """) == 2
        assert toil.walk(r""" 23 """) == 23

    def test_identifiers(self):
        assert toil.walk(r""" None """) is None
        assert toil.walk(r""" True """) is True
        assert toil.walk(r""" False """) is False

        with pytest.raises(AssertionError, match="Undefined variable .* a2"):
            toil.walk(r""" a2 """)
        with pytest.raises(AssertionError, match="Extra token"):
            toil.walk(r""" 2a """)
        with pytest.raises(AssertionError, match="Undefined variable .* _a"):
            toil.walk(r""" _a """)
        with pytest.raises(AssertionError, match="Undefined variable .* a_b"):
            toil.walk(r""" a_b """)
        with pytest.raises(AssertionError, match="Undefined variable .* True_"):
            toil.walk(r""" True_ """)
        with pytest.raises(AssertionError, match="Undefined variable .* true"):
            toil.walk(r""" true """)

    def test_paren(self):
        assert toil.walk(r""" (2 + 3) * 4 """) == 20
        assert toil.walk(r""" 2 * (3 + 4) """) == 14
        assert toil.walk(r""" (2 + 3) """) == 5
        assert toil.walk(r""" (2) """) == 2
        assert toil.walk(r""" (5 - (4 - 2)) * 2 """) == 6
        assert toil.walk(r""" (2 + 3) * (4 + 5) """) == 45

        with pytest.raises(AssertionError, match="Extra token"):
            toil.walk(r""" 2 + 3) """)
        with pytest.raises(AssertionError, match="Invalid token"):
            toil.walk(r""" (+) """)
        with pytest.raises(AssertionError, match=r"Expected \)"):
            toil.walk(r""" (2 + 3 """)
        with pytest.raises(AssertionError, match="Invalid token"):
            toil.walk(r""" () """)

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
