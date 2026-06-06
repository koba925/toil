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
                end;
                result
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
                end;
                a
            end
        """)
        assert toil.walk(r""" fib_iter(0) """) == 0
        assert toil.walk(r""" fib_iter(1) """) == 1
        assert toil.walk(r""" fib_iter(6) """) == 8

        toil.walk(r"""
            def fib_rec(n) do
                if n == 0 then 0
                else if n == 1 then 1
                else fib_rec(n - 1) + fib_rec(n - 2) end end
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
                end;
                a
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
            def node(val, left, right) do
                func op do
                    if op == 1 then val
                    else if op == 2 then left
                    else right end end
                end
            end
        """)
        toil.walk(r""" n1 := node(2, 3, 4) """)
        assert toil.walk(r""" n1(1) """) == 2
        assert toil.walk(r""" n1(2) """) == 3
        assert toil.walk(r""" n1(3) """) == 4

        toil.walk(r"""
            def bst_put(bst, val) do
                if bst == None then node(val, None, None)
                else
                    cur_val := bst(1);
                    if val == cur_val then
                        bst
                    else if val < cur_val then
                        node(cur_val, bst_put(bst(2), val), bst(3))
                    else
                        node(cur_val, bst(2), bst_put(bst(3), val))
                    end end
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
                    bst_walk(bst(2)); print(bst(1)); bst_walk(bst(3))
                end
            end
        """)
        toil.walk(r"""
            def bst_find(bst, val) do
                if bst == None then False
                else
                    cur_val := bst(1);
                    if val == cur_val then val
                    else if val < cur_val then bst_find(bst(2), val)
                    else bst_find(bst(3), val)
                    end end
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
        assert "AST:\n('print', [('add', [2, 3])])" in out
        assert "Output:\n5\n" in out
        assert "Result:\nNone\n" in out
        assert e.value.code == 0


if __name__ == "__main__":
    pytest.main([__file__])
