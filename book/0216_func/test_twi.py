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

    def test_sequence(self, capsys):
        assert toil.walk(r""" print(2); print(3) """) is None
        assert capsys.readouterr().out == "2\n3\n"

        assert toil.walk(r""" 2 + 3; 4 + 5; 6 + 7 """) == 13

        with pytest.raises(AssertionError, match="Invalid token"):
            toil.walk(r""" 2; """)
        with pytest.raises(AssertionError, match="Invalid token"):
            toil.walk(r""" ;2 """)
        with pytest.raises(AssertionError, match="Invalid token"):
            toil.walk(r""" 2;;3 """)

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

    def test_call(self, capsys):
        assert toil.walk(r""" add(2, 3) """) == 5
        assert toil.walk(r""" add(2 + 3, add(4, 5)) """) == 14
        assert toil.walk(r""" add(2, 3) * 4 """) == 20

        toil.walk(r""" myadd := add """)
        assert toil.walk(r""" myadd(2, 3) """) == 5

        toil.walk(r""" print() """)
        assert capsys.readouterr().out == "\n"
        toil.walk(r""" print(2) """)
        assert capsys.readouterr().out == "2\n"
        toil.walk(r""" print(2, 3) """)
        assert capsys.readouterr().out == "2 3\n"

        with pytest.raises(AssertionError, match="Invalid token"):
            toil.walk(r""" print( """)
        with pytest.raises(AssertionError, match=r"Expected \)"):
            toil.walk(r""" print(2 """)
        with pytest.raises(AssertionError, match=r"Expected \)"):
            toil.walk(r""" print(2 3) """)
        with pytest.raises(AssertionError, match="Invalid token"):
            toil.walk(r""" print(2,) """)
        with pytest.raises(AssertionError, match="Invalid token"):
            toil.walk(r""" print(, 3) """)
        with pytest.raises(AssertionError, match="Undefined variable"):
            toil.walk(r""" not_defined_func(2) """)
        with pytest.raises(AssertionError, match="Invalid operator"):
            toil.walk(r""" 2(3) """)

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

    def test_scope(self):
        assert toil.walk(r""" a := 2; scope a end """) == 2
        assert toil.walk(r""" a := 2; scope scope a end end """) == 2

        assert toil.walk(r""" a := 2; scope a := 3 end """) == 3
        assert toil.walk(r""" a """) == 2

        assert toil.walk(r""" a := 2; scope a = 3 end """) == 3
        assert toil.walk(r""" a """) == 3

        with pytest.raises(AssertionError, match="Undefined variable"):
            toil.walk(r""" a := 2; scope d = 3 end """)
        with pytest.raises(AssertionError, match="Expected end"):
            toil.walk(r""" scope 2 """)
        with pytest.raises(AssertionError, match="Expected end"):
            toil.walk(r""" scope end """)

    def test_if(self):
        assert toil.walk(r""" if 2 == 2 then 3 + 3 else 4 + 4 end """) == 6
        assert toil.walk(r""" if 2 == 3 then 3 + 3 else 4 + 4 end """) == 8

        assert toil.walk(r""" if True then 3 else 4 end * 5 """) == 15

        assert toil.walk(r""" if True then if True then 3 else 4 end else 5 end """) == 3
        assert toil.walk(r""" if True then if False then 3 else 4 end else 5 end """) == 4
        assert toil.walk(r""" if False then 3 else if True then 4 else 5 end end """) == 4
        assert toil.walk(r""" if False then 3 else if False then 4 else 5 end end """) == 5

        with pytest.raises(AssertionError, match="Expected then"):
            toil.walk(r""" if then 2 else 3 end """)
        with pytest.raises(AssertionError, match="Expected then"):
            toil.walk(r""" if True 2 else 3 end """)
        with pytest.raises(AssertionError, match="Expected else"):
            toil.walk(r""" if True then else 3 end """)
        with pytest.raises(AssertionError, match="Expected else"):
            toil.walk(r""" if True then 2 3 end """)
        with pytest.raises(AssertionError, match="Expected end"):
            toil.walk(r""" if True then 2 else end """)
        with pytest.raises(AssertionError, match="Expected end"):
            toil.walk(r""" if True then 2 else 3 """)

    def test_while(self, capsys):
        assert toil.walk(r""" i := 1; while i < 3 do i = i + 1 end """) == 3
        assert toil.walk(r""" i := 1; while i < 3 do i = i + 1; i * 10 end """) == 30

        assert toil.walk(r"""
            sum := 0;
            i := 1; while i < 4 do sum = sum + i; i = i + 1 end;
            sum
        """) == 6

        toil.walk(r"""
            i := 1; while i < 3 do
                j := 1; while j < 3 do print(i, j); j = j + 1 end;
                i = i + 1
            end
        """)
        assert capsys.readouterr().out == "1 1\n1 2\n2 1\n2 2\n"

        assert toil.walk(r""" while False do 1/0 end """) is None

        with pytest.raises(AssertionError, match="Expected do"):
            toil.walk(r""" while do 2 end """)
        with pytest.raises(AssertionError, match="Expected do"):
            toil.walk(r""" while True 2 end """)
        with pytest.raises(AssertionError, match="Expected end"):
            toil.walk(r""" while True do end """)
        with pytest.raises(AssertionError, match="Expected end"):
            toil.walk(r""" while True do 2 """)

    def test_func(self):
        assert toil.walk(r"""func do 2 end ()""") == 2
        assert toil.walk(r"""func a do a + 2 end (3)""") == 5
        assert toil.walk(r"""func a, b do a + b end (2, 3)""") == 5

        assert toil.walk(r"""
            twice := func f, x do f(f(x)) end;
            double := func x do x * 2 end;
            twice(double, 3)
        """) == 12

        assert toil.walk(r"""
            a := 2;
            f := func do a end;
            g := func do a := 3; f() end;
            g()
        """) == 2

        assert toil.walk(r"""
            func a do func b do a + b end end (2)(3)
        """) == 5

        with pytest.raises(AssertionError, match="Expected do"):
            toil.walk(r""" func a, b a + b end """)
        with pytest.raises(AssertionError, match="Expected end"):
            toil.walk(r""" func a, b do end """)
        with pytest.raises(AssertionError, match="Expected end"):
            toil.walk(r""" func a, b do a + b """)
        with pytest.raises(AssertionError, match="Expected do"):
            toil.walk(r""" func a, do a + b end """)
        with pytest.raises(AssertionError, match="Invalid token"):
            toil.walk(r""" func , b do a + b end """)

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
