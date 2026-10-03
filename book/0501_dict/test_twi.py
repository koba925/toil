import pytest
from toil import Interpreter

@pytest.fixture(autouse=True)
def setup_toil():
    global toil
    toil = Interpreter()
    toil.stdlib()

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

    def test_and_or(self, capsys):
        assert toil.walk(r""" True and False """) is False
        assert toil.walk(r""" False and True """) is False
        assert toil.walk(r""" True or False """) is True
        assert toil.walk(r""" False or True """) is True

        assert toil.walk(r""" True and 2 """) == 2
        assert toil.walk(r""" 0 and 2 / 0 """) == 0
        assert toil.walk(r""" False or 2 """) == 2
        assert toil.walk(r""" 1 or 2 / 0 """) == 1

        assert toil.walk(r""" print(2) and 3 """) is None
        assert capsys.readouterr().out == "2\n"
        assert toil.walk(r""" not print(2) or 3 """) is True
        assert capsys.readouterr().out == "2\n"

        assert toil.walk(r""" True or False and False """) is False  # (True or False) and False
        assert toil.walk(r""" False and False or True """) is True   # (False and False) or True
        assert toil.walk(r""" not True and False """) is False       # (not True) and False
        assert toil.walk(r""" False or not False """) is True        # False or (not False)

        assert toil.walk(r""" a := True and False """) is False      # a := (True and False)
        assert toil.walk(r""" a """) is False

    def test_not(self):
        assert toil.walk(r""" not 2 == 2 """) is False
        assert toil.walk(r""" not not 2 == 2 """) is True
        assert toil.walk(r""" a := not 2 == 2 """) is False

    def test_unary_minus(self):
        assert toil.walk(r""" -2 """) == -2
        assert toil.walk(r""" --2 """) == 2
        assert toil.walk(r""" 3--2 """) == 5
        assert toil.walk(r""" -add(2, 3) * 4 """) == -20

    def test_comparison(self):
        assert toil.walk(r""" 2 == 2 """) is True
        assert toil.walk(r""" 2 == 3 """) is False
        assert toil.walk(r""" None == None """) is True
        assert toil.walk(r""" None == True """) is False
        assert toil.walk(r""" True == True """) is True
        assert toil.walk(r""" True == False """) is False
        assert toil.walk(r""" False == False """) is True

        assert toil.walk(r""" 2 != 2 """) is False
        assert toil.walk(r""" 2 != 3 """) is True

        assert toil.walk(r""" 2 < 2 """) is False
        assert toil.walk(r""" 2 < 3 """) is True
        assert toil.walk(r""" 2 > 2 """) is False
        assert toil.walk(r""" 3 > 2 """) is True

        assert toil.walk(r""" 3 <= 2 """) is False
        assert toil.walk(r""" 2 <= 2 """) is True
        assert toil.walk(r""" 2 <= 3 """) is True
        assert toil.walk(r""" 2 >= 3 """) is False
        assert toil.walk(r""" 2 >= 2 """) is True
        assert toil.walk(r""" 3 >= 2 """) is True

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

        assert toil.walk(r""" if True then 2 end """) == 2
        assert toil.walk(r""" if False then 2 end """) is None
        assert toil.walk(r""" if True then 2 else 3 end """) == 2
        assert toil.walk(r""" if False then 2 else 3 end """) == 3
        assert toil.walk(r""" if True then 2 elif True then 3 end """) == 2
        assert toil.walk(r""" if False then 2 elif True then 3 end """) == 3
        assert toil.walk(r""" if False then 2 elif False then 3 end """) is None
        assert toil.walk(r""" if False then 2 elif True then 3 else 4 end """) == 3
        assert toil.walk(r""" if True then 2 elif True then 3 else 4 end """) == 2
        assert toil.walk(r""" if False then 2 elif False then 3 else 4 end """) == 4
        assert toil.walk(r""" if False then 2 elif False then 3 elif True then 4 else 5 end """) == 4

        with pytest.raises(AssertionError, match="Expected then"):
            toil.walk(r""" if True 2 end """)
        with pytest.raises(AssertionError, match="Expected end"):
            toil.walk(r""" if True then 2 """)
        with pytest.raises(AssertionError, match="Expected then"):
            toil.walk(r""" if then 2 else 3 end """)
        with pytest.raises(AssertionError, match="Expected then"):
            toil.walk(r""" if True 2 else 3 end """)
        with pytest.raises(AssertionError, match="Expected end"):
            toil.walk(r""" if True then else 3 end """)
        with pytest.raises(AssertionError, match="Expected end"):
            toil.walk(r""" if True then 2 3 end """)
        with pytest.raises(AssertionError, match="Expected end"):
            toil.walk(r""" if True then 2 else end """)
        with pytest.raises(AssertionError, match="Expected end"):
            toil.walk(r""" if True then 2 else 3 """)
        with pytest.raises(AssertionError, match="Expected then"):
            toil.walk(r""" if False then 2 elif True 3 end """)
        with pytest.raises(AssertionError, match="Expected end"):
            toil.walk(r""" if False then 2 elif True then 3 """)

    def test_while(self, capsys):
        assert toil.walk(r""" i := 1; while i < 3 do i = i + 1 end """) is None
        assert toil.walk(r""" i := 1; while i < 3 do break end """) is None

        assert toil.walk(r""" i := 1; while i < 3 do i = i + 1 then i else 0 end """) == 3
        assert toil.walk(r""" i := 1; while i < 3 do break then i else 0 end """) == 0

        assert toil.walk(r""" i := 1; while i < 3 do i = i + 1 then i end """) == 3
        assert toil.walk(r""" i := 1; while i < 3 do break then i end """) is None

        assert toil.walk(r""" i := 1; while i < 3 do i = i + 1 else 0 end """) is None
        assert toil.walk(r""" i := 1; while i < 3 do break else 0 end """) == 0

        assert toil.walk(r"""
            sum := 0; i := 1;
            while i < 4 do
                sum = sum + i;
                i = i + 1
            then sum end
        """) == 6

        toil.walk(r"""
            i := 1; while i < 3 do
                j := 1; while j < 3 do print(i, j); j = j + 1 end;
                i = i + 1
            end
        """)
        assert capsys.readouterr().out == "1 1\n1 2\n2 1\n2 2\n"

        assert toil.walk(r""" while False do 1/0 then 3 else 4 end """) == 3

        with pytest.raises(AssertionError, match="Expected do"):
            toil.walk(r""" while do 2 then 3 else 4 end """)
        with pytest.raises(AssertionError, match="Expected do"):
            toil.walk(r""" while True 2 then 3 else 4 end """)
        with pytest.raises(AssertionError, match="Expected end"):
            toil.walk(r""" while True do then 3 else 4 end """)
        with pytest.raises(AssertionError, match="Expected end"):
            toil.walk(r""" while True do 2 3 else 4 end """)
        with pytest.raises(AssertionError, match="Expected end"):
            toil.walk(r""" while True do 2 then else 4 end """)
        with pytest.raises(AssertionError, match="Expected end"):
            toil.walk(r""" while True do 2 then 3 4 end """)
        with pytest.raises(AssertionError, match="Expected end"):
            toil.walk(r""" while True do 2 then 3 else end """)
        with pytest.raises(AssertionError, match="Expected end"):
            toil.walk(r""" while True do 2 then 3 else 4 """)

    def test_break_and_continue(self, capsys):
        assert toil.walk(r""" while True do break end """) is None

        assert toil.walk(r"""
            i := 0; while i < 4 do
                if i == 1 then i = 2; continue end;
                print(i);
                if i == 3 then break end;
                i = i + 1
            end
        """) is None
        assert capsys.readouterr().out == "0\n2\n3\n"

        assert toil.walk(r"""
            i := 0; while i < 4 do
                if i == 1 then i = 2; continue end;
                print(i);
                i = i + 1
            then i end
        """) == 4
        assert capsys.readouterr().out == "0\n2\n3\n"

        toil.walk(r"""
            i := 1; while i < 4 do
                j := 1; while j < 4 do
                    if i == 2 and j == 2 then break end;
                    print(i, j);
                    j = j + 1
                else break end;
                i = i + 1
            end
        """)
        assert capsys.readouterr().out == "1 1\n1 2\n1 3\n2 1\n"

        assert toil.walk(r"""
            def check_and_quit(i) do
                if i == 2 then break end
            end;
            i := 0; while True do
                check_and_quit(i);
                print(i);
                i := i + 1
            end
        """) is None
        assert capsys.readouterr().out == "0\n1\n"

        with pytest.raises(AssertionError, match="Break at top level"):
            toil.walk(r""" break """)
        with pytest.raises(AssertionError, match="Continue at top level"):
            toil.walk(r""" continue """)

    def test_for(self, capsys):
        assert toil.walk(r""" for i in [0, 1, 2] do print(i) end """) is None
        assert capsys.readouterr().out == "0\n1\n2\n"
        assert toil.walk(r""" for i in tuple(0, 1, 2) do print(i) end """) is None
        assert capsys.readouterr().out == "0\n1\n2\n"

        assert toil.walk(r"""
            a := [];
            for i in [0, 1, 2] do push(a, i) then a else 1/0 end
        """) == [0, 1, 2]

        assert toil.walk(r"""
            a := [];
            for i in [0, 1, 2] do
                if i == 2 then break end;
                push(a, i)
            else a end
        """) == [0, 1]

        assert toil.walk(r"""
            a := [];
            for i in [0, 1, 2] do
                if i == 1 then continue end;
                push(a, i)
            then a end
        """) == [0, 2]

        assert toil.walk(r""" for i in [] do 1/0 then 2 end """) == 2

        assert toil.walk(r"""
            sum := 0;
            for i in [1, 2, 3] do
                sum = sum + i
            then sum end
        """) == 6

        with pytest.raises(AssertionError, match="Invalid loop target"):
            toil.walk(r""" for i in 2 do i end """)
        with pytest.raises(AssertionError, match="Expected in"):
            toil.walk(r""" for in a do i end """)
        with pytest.raises(AssertionError, match="Expected in"):
            toil.walk(r""" for i a do i end """)
        with pytest.raises(AssertionError, match="Expected do"):
            toil.walk(r""" for i in do i end """)
        with pytest.raises(AssertionError, match="Expected do"):
            toil.walk(r""" for i in a i end """)
        with pytest.raises(AssertionError, match="Expected end"):
            toil.walk(r""" for i in a do end """)
        with pytest.raises(AssertionError, match="Expected end"):
            toil.walk(r""" for i in a do i """)

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

    def test_def(self):
        toil.walk(r""" def f do 2 end """)
        assert toil.walk(r""" f() """) == 2

        toil.walk(r""" def f() do 3 end """)
        assert toil.walk(r""" f() """) == 3

        toil.walk(r""" def f(a) do a + 2 end """)
        assert toil.walk(r""" f(3) """) == 5

        toil.walk(r""" def f(a, b) do a + b end """)
        assert toil.walk(r""" f(2, 3) """) == 5

        assert toil.walk(r"""
            a := 2;
            def f do a end;
            def g do a := 3; f() end;
            g()
        """) == 2

        with pytest.raises(AssertionError, match="Expected do"):
            toil.walk(r""" def do a end """)
        with pytest.raises(AssertionError, match="Expected do"):
            toil.walk(r""" def f(a) a end """)
        with pytest.raises(AssertionError, match="Expected end"):
            toil.walk(r""" def f(a) do end """)
        with pytest.raises(AssertionError, match="Expected end"):
            toil.walk(r""" def f(a) do a """)
        with pytest.raises(AssertionError, match="Invalid def syntax"):
            toil.walk(r""" def 2 do a end """)

    def test_return(self):
        toil.walk(r"""
            def f(a) do
                if a == 2 then return end;
                if a == 3 then return(4) end;
                5
            end
        """)
        assert toil.walk(r""" f(2) """) is None
        assert toil.walk(r""" f(3) """) == 4
        assert toil.walk(r""" f(4) """) == 5

        assert toil.walk(r""" return(2) """) == 2
        assert toil.walk(r""" return; 3 """) is None
        assert toil.walk(r""" return(2); 3 """) == 2

    def test_tuple(self):
        assert toil.walk(r""" tuple() """) == ()
        assert toil.walk(r""" tuple(2) """) == (2,)
        assert toil.walk(r""" tuple(2, 3) """) == (2, 3)

        toil.walk(r""" t := tuple(2, 3, 4) """)
        assert toil.walk(r""" index(t, 0) """) == 2
        assert toil.walk(r""" index(t, 2) """) == 4

        toil.walk(r""" t := tuple(2, 3, 4) """)
        assert toil.walk(r""" t[1] """) == 3
        assert toil.walk(r""" t[-1] """) == 4

        assert toil.walk(r""" t := tuple(2, 3, tuple(4, 5)) """) == (2, 3, (4, 5))
        assert toil.walk(r""" t[2] """) == (4, 5)
        assert toil.walk(r""" t[2][0] """) == 4

        toil.walk(r""" f := func do tuple(add, sub) end """)
        assert toil.walk(r""" f()[0](2, 3) """) == 5

        assert toil.walk(r""" len(tuple(2, 3)) """) == 2
        assert toil.walk(r""" slice(tuple(2, 3, 4, 5), 1, 3) """) == (3, 4)
        assert toil.walk(r""" slice(tuple(2, 3, 4, 5), None, 3) """) == (2, 3, 4)
        assert toil.walk(r""" slice(tuple(2, 3, 4, 5), 1, None) """) == (3, 4, 5)

        assert toil.walk(r""" tuple(2, 3) == tuple(2, 3) """) is True
        assert toil.walk(r""" tuple(2, 3) == tuple(2, 4) """) is False
        assert toil.walk(r""" tuple(2, 3) + tuple(4, 5) """) == (2, 3, 4, 5)

        with pytest.raises(AssertionError, match=r"Expected \]"):
            toil.walk(r""" t[2 """)
        with pytest.raises(AssertionError, match="Extra token"):
            toil.walk(r""" 2] """)

    def test_array(self):
        assert toil.walk(r""" list() """) == []
        assert toil.walk(r""" list(2) """) == [2]
        assert toil.walk(r""" list(2, 3) """) == [2, 3]

        toil.walk(r""" l := list(2, 3, 4) """)
        assert toil.walk(r""" index(l, 0) """) == 2
        assert toil.walk(r""" index(l, 2) """) == 4

        assert toil.walk(r""" len(list(2, 3)) """) == 2
        assert toil.walk(r""" slice(list(2, 3, 4, 5), 1, 3) """) == [3, 4]
        assert toil.walk(r""" slice(list(2, 3, 4, 5), None, 3) """) == [2, 3, 4]
        assert toil.walk(r""" slice(list(2, 3, 4, 5), 1, None) """) == [3, 4, 5]

        toil.walk(r""" l := list(2, 3, 4) """)
        assert toil.walk(r""" l[1] """) == 3
        assert toil.walk(r""" l[-1] """) == 4

        assert toil.walk(r""" l := list(2, 3, list(4, 5)) """) == [2, 3, [4, 5]]
        assert toil.walk(r""" l[2] """) == [4, 5]
        assert toil.walk(r""" l[2][0] """) == 4

        assert toil.walk(r""" push(l, 6) """) is None
        assert toil.walk(r""" l """) == [2, 3, [4, 5], 6]
        assert toil.walk(r""" pop(l) """) == 6
        assert toil.walk(r""" l """) == [2, 3, [4, 5]]
        assert toil.walk(r""" pop(l, 1) """) == 3
        assert toil.walk(r""" l """) == [2, [4, 5]]

        assert toil.walk(r""" [] """) == []
        assert toil.walk(r""" [2 + 3] """) == [5]
        assert toil.walk(r""" [2, 3] """) == [2, 3]
        assert toil.walk(r""" [2, 3, [4, 5]] """) == [2, 3, [4, 5]]

        assert toil.walk(r""" [2, 3][1] """) == 3

        assert toil.walk(r""" [2, 3] == [2, 3] """) is True
        assert toil.walk(r""" [2, 3] == [2, 4] """) is False
        assert toil.walk(r""" [2, 3] + [4, 5] """) == [2, 3, 4, 5]

        with pytest.raises(AssertionError, match=r"Expected \]"):
            toil.walk(r""" [2 """)
        with pytest.raises(AssertionError, match="Extra token"):
            toil.walk(r""" 2] """)

    def test_assign_elem(self):
        assert toil.walk(r""" arr := [2, 3, 4]; arr[2] = 5 """) == 5
        assert toil.walk(r""" arr """) == [2, 3, 5]
        assert toil.walk(r""" arr[-1] = 6; arr """) == [2, 3, 6]

        assert toil.walk(r""" arr2 := [[2, 3], 4]; arr2[0][1] = 5; arr2 """) == [[2, 5], 4]
        assert toil.walk(r""" a := [2, 3]; b := [4, 5]; a[0] = b[1] = 6; [a, b] """) == [[6, 3], [4, 6]]

        with pytest.raises(AssertionError, match="Invalid index assignment"):
            toil.walk(r""" tpl := tuple(2, 3, 4); tpl[2] = 5 """)
        with pytest.raises(AssertionError, match="Invalid index assignment"):
            toil.walk(r""" arr := [2, 3]; arr[None] = 4 """)
        assert toil.walk(r""" arr := [2, 3]; arr[True] = 4; arr """) == [2, 4]

    def test_raw_string(self, capsys):
        assert toil.walk(r""" ['abc'] """) == ["abc"]
        assert toil.walk(r""" [''] """) == [""]
        assert toil.walk(r""" ['if ; #"\n'] """) == ["if ; #\"\\n"]
        assert toil.walk(r""" ['a
b'] """) == ["a\nb"]

        assert toil.walk(r""" [join(['a', 'b', 'c'], ' ')] """) == ["a b c"]
        assert toil.walk(r""" [format('Age: {}', 25)] """) == ["Age: 25"]

        assert toil.walk(r""" len('abc') """) == 3
        assert toil.walk(r""" ['abc' + 'def'] """) == ["abcdef"]
        assert toil.walk(r""" ['abc'[2]] """) == ["c"]
        assert toil.walk(r""" [slice('abcdef', 2, 4)] """) == ["cd"]
        assert toil.walk(r""" for c in 'abc' do print(c) end """) is None
        assert capsys.readouterr().out == "a\nb\nc\n"

        with pytest.raises(AssertionError, match="Unterminated string"):
            toil.walk(r""" ' """)
        with pytest.raises(AssertionError, match="Invalid index assignment"):
            toil.walk(r""" s := 'abc'; s[2] = 'd' """)

        assert toil.walk(r""" print('hello, world') """) is None
        assert capsys.readouterr().out == "hello, world\n"

    def test_string(self):
        assert toil.walk(r""" ["abc"] """) == ["abc"]
        assert toil.walk(r""" [""] """) == [""]
        assert toil.walk(r""" ["if ; #'"] """) == ["if ; #'"]
        assert toil.walk(r""" ["a
b"] """) == ["a\nb"]

        assert toil.walk(r""" ["a\nc"] """) == ["a\nc"]
        assert toil.walk(r""" ["a\\c"] """) == ["a\\c"]
        assert toil.walk(r""" ["a\"c"] """) == ["a\"c"]
        assert toil.walk(r""" ["a\xc"] """) == ["axc"]

        with pytest.raises(AssertionError, match="Unterminated string"):
            toil.walk(r""" " """)
        with pytest.raises(AssertionError, match="Unterminated escape sequence"):
            toil.walk(""" "a\\""")

    def test_stdlib(self):
        assert toil.walk(r"""
            sum := 0;
            n := 10;
            for i in range(1, n + 1, 1) do
                sum = sum + i
            then sum end
        """) == 55

        assert toil.walk(r""" a := range(2, 10, 1) """) == [2, 3, 4, 5, 6, 7, 8, 9]
        assert toil.walk(r""" b := range(2, 10, 3) """) == [2, 5, 8]

        assert toil.walk(r""" first(a) """) == 2
        assert toil.walk(r""" rest(a) """) == [3, 4, 5, 6, 7, 8, 9]
        assert toil.walk(r""" last(a) """) == 9

        assert toil.walk(r""" first(tuple(2, 3, 4)) """) == 2
        assert toil.walk(r""" rest(tuple(2, 3, 4)) """) == (3, 4)

        assert toil.walk(r""" map(a, func n do n * 2 end) """) == [4, 6, 8, 10, 12, 14, 16, 18]

        assert toil.walk(r""" filter(a, func n do n % 2 == 0 end) """) == [2, 4, 6, 8]

        assert toil.walk(r""" reverse(a) """) == [9, 8, 7, 6, 5, 4, 3, 2]
        assert toil.walk(r""" reverse([]) """) == []

        assert toil.walk(r""" zip(a, [4, 5, 6]) """) == [[2, 4], [3, 5], [4, 6]]

        assert toil.walk(r""" enumerate(a) """) == [
            [0, 2], [1, 3], [2, 4], [3, 5], [4, 6], [5, 7], [6, 8], [7, 9]
        ]

        assert toil.walk(r""" all([True, True], func x do x end) """) is True
        assert toil.walk(r""" all([True, False], func x do x end) """) is False
        assert toil.walk(r""" any([False, True], func x do x end) """) is True
        assert toil.walk(r""" any([False, False], func x do x end) """) is False

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


class TestExamples:
    def test_factorial(self):
        toil.walk(r"""
            def factorial_iter(n) do
                result := 1;
                while n > 0 do
                    result = result * n;
                    n = n - 1
                then result end
            end
        """)
        assert toil.walk(r""" factorial_iter(0) """) == 1
        assert toil.walk(r""" factorial_iter(1) """) == 1
        assert toil.walk(r""" factorial_iter(4) """) == 24

        toil.walk(r"""
            def factorial_rec(n) do
                if n == 0 then 1 else n * factorial_rec(n - 1) end
            end
        """)
        assert toil.walk(r""" factorial_rec(0) """) == 1
        assert toil.walk(r""" factorial_rec(1) """) == 1
        assert toil.walk(r""" factorial_rec(4) """) == 24

    def test_fibonacci(self):
        toil.walk(r"""
            def fib_iter(n) do
                a := 0; b := 1;
                while n > 0 do
                    tmp := b; b = a + b; a = tmp;
                    n = n - 1
                then a end
            end
        """)
        assert toil.walk(r""" fib_iter(0) """) == 0
        assert toil.walk(r""" fib_iter(1) """) == 1
        assert toil.walk(r""" fib_iter(6) """) == 8

        toil.walk(r"""
            def fib_rec(n) do
                if n == 0 then return(0) end;
                if n == 1 then return(1) end;
                fib_rec(n - 1) + fib_rec(n - 2)
            end
        """)
        assert toil.walk(r""" fib_rec(0) """) == 0
        assert toil.walk(r""" fib_rec(1) """) == 1
        assert toil.walk(r""" fib_rec(6) """) == 8

    def test_GCD(self):
        toil.walk(r"""
            def gcd_iter(a, b) do
                while b > 0 do
                    tmp := b; b = a % b; a = tmp
                then a end
            end
        """)
        assert toil.walk(r""" gcd_iter(12, 18) """) == 6

        toil.walk(r"""
            def gcd_rec(a, b) do
                if b == 0 then a else gcd_rec(b, a % b) end
            end
        """)
        assert toil.walk(r""" gcd_rec(12, 18) """) == 6

    def test_mutual_recursion(self):
        toil.walk(r"""
            def even(n) do if n == 0 then True else odd(n - 1) end end;
            def odd(n) do if n == 0 then False else even(n - 1) end end
        """)
        assert toil.walk(r""" even(2) """) is True
        assert toil.walk(r""" even(3) """) is False
        assert toil.walk(r""" odd(2) """) is False
        assert toil.walk(r""" odd(3) """) is True

    def test_counter(self):
        toil.walk(r"""
            def make_counter() do
                count := 0;
                func do count = count + 1 end
            end
        """)
        toil.walk(r""" c1 := make_counter() """)
        toil.walk(r""" c2 := make_counter() """)
        assert toil.walk(r""" c1() """) == 1
        assert toil.walk(r""" c1() """) == 2
        assert toil.walk(r""" c2() """) == 1
        assert toil.walk(r""" c2() """) == 2

    def test_binary_search_tree(self, capsys):
        toil.walk(r"""
            def bst_put(bst, val) do
                if bst == None then tuple(val, None, None)
                else
                    cur_val := bst[0];
                    if val == cur_val then
                        bst
                    elif val < cur_val then
                        tuple(cur_val, bst_put(bst[1], val), bst[2])
                    else
                        tuple(cur_val, bst[1], bst_put(bst[2], val))
                    end
                end
            end
        """)
        toil.walk(r""" bst := None """)
        toil.walk(r""" bst = bst_put(bst, 7) """)
        toil.walk(r""" bst = bst_put(bst, 3) """)
        toil.walk(r""" bst = bst_put(bst, 1) """)
        toil.walk(r""" bst = bst_put(bst, 9) """)
        toil.walk(r""" bst = bst_put(bst, 5) """)

        toil.walk(r"""
            def bst_walk(bst) do
                if bst == None then None
                else
                    bst_walk(bst[1]); print(bst[0]); bst_walk(bst[2])
                end
            end
        """)
        toil.walk(r"""
            def bst_find(bst, val) do
                if bst == None then False
                else
                    cur_val := bst[0];
                    if val == cur_val then val
                    elif val < cur_val then bst_find(bst[1], val)
                    else bst_find(bst[2], val)
                    end
                end
            end
        """)

        toil.walk(r""" bst_walk(bst) """)
        assert capsys.readouterr().out == "1\n3\n5\n7\n9\n"

        toil.walk(r"""
            i := 0;
            while i < 10 do
                print(bst_find(bst, i));
                i = i + 1
            end
        """)
        assert capsys.readouterr().out == "False\n1\nFalse\n3\nFalse\n5\nFalse\n7\nFalse\n9\n"

    def test_bubblesort(self):
        toil.walk(r"""
            def bubblesort(a) do
                n := len(a);
                for i in range(0, n, 1) do
                    for j in range(0, n - i - 1, 1) do
                        if a[j] > a[j + 1] then
                            tmp := a[j]; a[j] = a[j + 1]; a[j + 1] = tmp
                        end
                    end
                then a end
            end
        """)
        assert toil.walk(r""" bubblesort([5, 3, 8, 4, 2]) """) == [2, 3, 4, 5, 8]

    def test_quicksort(self):
        toil.walk(r"""
            def quicksort(a) do
                if len(a) <= 1 then a else
                    pivot := first(a); rem := rest(a);
                    left := filter(rem, func x do x < pivot end);
                    right := filter(rem, func x do x >= pivot end);
                    quicksort(left) + [pivot] + quicksort(right)
                end
            end
        """)
        assert toil.walk(r""" quicksort([5, 3, 8, 4, 2]) """) == [2, 3, 4, 5, 8]

    def test_is_prime(self):
        toil.walk(r"""
            def is_prime(n) do
                if n < 2 then return(False) end;
                i := 2;
                while i * i <= n do
                    if n % i == 0 then return(False) end;
                    i = i + 1
                then True end
            end
        """)
        assert toil.walk(r""" is_prime(1) """) is False
        assert toil.walk(r""" is_prime(2) """) is True
        assert toil.walk(r""" is_prime(4) """) is False
        assert toil.walk(r""" is_prime(7) """) is True
        assert toil.walk(r""" is_prime(15) """) is False

    def test_sieve(self):
        assert toil.walk(r"""
            def sieve(n) do
                s := [False, False] + [True] * (n - 2);
                i := 2; while i * i < n do
                    if s[i] then
                        j := i * i; while j < n do
                            s[j] = False;
                            j = j + i
                        end
                    end;
                    i = i + 1
                then map(filter(enumerate(s), last), first) end
            end;

            sieve(10)
        """) == [2, 3, 5, 7]


import os, sys, io, runpy

class TestCommandLine:
    def test_from_file(self, capsys, monkeypatch):
        toil_script = os.path.join(os.path.dirname(__file__), "toil.py")
        gcd_script = os.path.join(os.path.dirname(__file__), "gcd.toil")
        monkeypatch.setattr(sys, "argv", ["toil.py", "--walk", gcd_script])

        with pytest.raises(SystemExit) as e:
            runpy.run_path(toil_script, run_name="__main__")

        assert capsys.readouterr().out == "12\n"
        assert e.value.code == 0

    def test_repl(self, capsys, monkeypatch):
        toil_script = os.path.join(os.path.dirname(__file__), "toil.py")
        monkeypatch.setattr(sys, "argv", ["toil.py", "--repl"])
        monkeypatch.setattr(sys, "stdin", io.StringIO("print(2 + 3)\n"))

        with pytest.raises(SystemExit) as e:
            runpy.run_path(toil_script, run_name="__main__")

        out = capsys.readouterr().out
        assert "AST:\n(print, [(add, [2, 3])])" in out
        assert "Output:\n5\n" in out
        assert "Result:\nNone\n" in out
        assert e.value.code == 0


if __name__ == "__main__":
    pytest.main([__file__])
