import pytest
from toil import Interpreter

@pytest.fixture(autouse=True)
def setup_toil():
    global toil
    toil = Interpreter()

class TestIntermediateCodeInterpreter:
    # Ensure test independence
    def test_env_isolation_step1(self):
        assert toil.run(r""" a := 2 """) == 2
    def test_env_isolation_step2(self):
        with pytest.raises(AssertionError, match="Undefined variable"):
            toil.run(r""" a """)

    def test_constants(self):
        assert toil.run(r""" 2 """) == 2
        assert toil.run(r""" None """) is None
        assert toil.run(r""" True """) is True
        assert toil.run(r""" False """) is False

    def test_variable_definition(self):
        assert toil.run(r""" a := 2 """) == 2
        assert toil.run(r""" a """) == 2

        assert toil.run(r""" a := b := 2 == 2 """) is True
        assert toil.run(r""" a """) is True
        assert toil.run(r""" b """) is True

        assert toil.run(r""" a := 2; b := 3; a * b """) == 6

        with pytest.raises(AssertionError, match="Undefined variable"):
            toil.run(r""" c """)

    def test_sequence(self, capsys):
        assert toil.run(r""" 2; 3; 4 """) == 4

        assert toil.run(r""" print(2); print(3) """) is None
        assert capsys.readouterr().out == "2\n3\n"

        with pytest.raises(Exception, match="Empty sequence"):
            toil.compile(("seq", []))

    def test_assignment_scope(self):
        assert toil.run(r""" a := 2; a = 3 + 4 """) == 7
        assert toil.run(r""" a """) == 7

        assert toil.run(r""" a := 2; b := 3; a = b = 4 """) == 4
        assert toil.run(r""" a """) == 4
        assert toil.run(r""" b """) == 4

        assert toil.run(r""" a := 2; scope a + 3 end """) == 5

        assert toil.run(r""" a := 2; scope scope a + 3 end end """) == 5

        assert toil.run(r""" a := 2; scope a := 3 end """) == 3
        assert toil.run(r""" a """) == 2

        assert toil.run(r""" a := 2; scope a = 3 end """) == 3
        assert toil.run(r""" a """) == 3

        with pytest.raises(AssertionError, match="Undefined variable"):
            toil.run(r""" scope d = 3 end """)
        with pytest.raises(AssertionError, match="Undefined variable"):
            toil.run(r""" scope c := 2 end; c """)

    def test_if(self):
        assert toil.run(r""" if 2 == 2 then 4 + 5 else 6 + 7 end """) == 9
        assert toil.run(r""" if 2 == 3 then 4 + 5 else 6 + 7 end """) == 13
        assert toil.run(r""" if True then 3 else 4 end * 5 """) == 15
        assert toil.run(r""" if True then if True then 3 else 4 end else 5 end """) == 3
        assert toil.run(r""" if True then if False then 3 else 4 end else 5 end """) == 4
        assert toil.run(r""" if False then 3 else if True then 4 else 5 end end """) == 4
        assert toil.run(r""" if False then 3 else if False then 4 else 5 end end """) == 5

    def test_while(self, capsys):
        assert toil.run(r""" i := 1; while i < 3 do i = i + 1 end """) == 3

        assert toil.run(r"""
            sum := 0;
            i := 1; while i < 4 do sum = sum + i; i = i + 1 end;
            sum
        """) == 6

        toil.run(r"""
            i := 1; while i < 3 do
                j := 1; while j < 3 do print(i); print(j); j = j + 1 end;
                i = i + 1
            end
        """)
        assert capsys.readouterr().out == "1\n1\n1\n2\n2\n1\n2\n2\n"

        assert toil.run(r""" while False do 1/0 end """) is None

    def test_builtins(self, capsys):
        assert toil.run(r""" add(2, 3) """) == 5

        assert toil.run(r""" 2 + 3 """) == 5
        assert toil.run(r""" 3 - 2 """) == 1
        assert toil.run(r""" 2 * 3 """) == 6
        assert toil.run(r""" 6 / 3 """) == 2
        assert toil.run(r""" 7 % 3 """) == 1

        assert toil.run(r""" 2 + 3 * 4 """) == 14
        assert toil.run(r""" (2 + 3) * 4 """) == 20
        assert toil.run(r""" 2 + 3 == 2 * 3 """) is False
        assert toil.run(r""" 2 + 3 < 2 * 3 """) is True

        assert toil.run(r""" 2 == 2 """) is True
        assert toil.run(r""" 2 == 3 """) is False

        assert toil.run(r""" 2 < 2 """) is False
        assert toil.run(r""" 2 < 3 """) is True

        assert toil.run(r""" 2 > 2 """) is False
        assert toil.run(r""" 3 > 2 """) is True

        assert toil.run(r""" print() """) is None
        assert capsys.readouterr().out == "\n"

        assert toil.run(r""" print(2) """) is None
        assert capsys.readouterr().out == "2\n"

        assert toil.run(r""" print(2, 3) """) is None
        assert capsys.readouterr().out == "2 3\n"

        assert toil.run(r""" print(2 + 3 == 5) """) is None
        assert capsys.readouterr().out == "True\n"

        assert toil.run(r""" myadd := add; myadd(2, 3) """) == 5

        with pytest.raises(AssertionError, match="Undefined variable"):
            toil.run(r""" not_defined() """)

    def test_func(self):
        assert toil.run(r""" func do 2 end () """) == 2
        assert toil.run(r""" func a do a + 2 end (3) """) == 5
        assert toil.run(r""" func a, b do a + b end (2, 3) """) == 5

        assert toil.run(r"""
            twice := func f, x do f(f(x)) end;
            double := func x do x * 2 end;
            twice(double, 3)
        """) == 12

        assert toil.run(r"""
            a := 2;
            f := func do a end;
            g := func do a := 3; f() end;
            g()
        """) == 2

        assert toil.run(r""" func a do func b do a + b end end (2)(3) """) == 5

        with pytest.raises(AssertionError, match="Invalid operator"):
            toil.run(r""" 2(3) """)

    def test_def(self):
        toil.run(r""" def f do 2 end """)
        assert toil.run(r""" f() """) == 2

        toil.run(r""" def f(a) do a + 2 end """)
        assert toil.run(r""" f(3) """) == 5

        toil.run(r""" def f(a, b) do a + b end """)
        assert toil.run(r""" f(2, 3) """) == 5

    def test_invalid_expression(self):
        with pytest.raises(Exception, match="Invalid stack state"):
            toil.execute([('ret',)]) # ->
        with pytest.raises(Exception, match="Invalid stack state"):
            toil.execute([('const', 2), ('const', 3), ('ret',)])
        with pytest.raises(Exception, match="Invalid instruction"):
            toil.execute([('not_op',), ('halt',)])
        with pytest.raises(Exception, match="Unsupported expression"):
            toil.compile((2, 3, 4))


class TestExamples:
    def test_factorial(self):
        toil.run(r"""
            def factorial_iter(n) do
                result := 1;
                while n > 0 do
                    result = result * n;
                    n = n - 1
                end;
                result
            end
        """)
        assert toil.run(r""" factorial_iter(0) """) == 1
        assert toil.run(r""" factorial_iter(1) """) == 1
        assert toil.run(r""" factorial_iter(4) """) == 24

        toil.run(r"""
            def factorial_rec(n) do
                if n == 0 then 1 else n * factorial_rec(n - 1) end
            end
        """)
        assert toil.run(r""" factorial_rec(0) """) == 1
        assert toil.run(r""" factorial_rec(1) """) == 1
        assert toil.run(r""" factorial_rec(4) """) == 24

    def test_fibonacci(self):
        toil.run(r"""
            def fib_iter(n) do
                a := 0; b := 1;
                while n > 0 do
                    tmp := b; b = a + b; a = tmp;
                    n = n - 1
                end;
                a
            end
        """)
        assert toil.run(r""" fib_iter(0) """) == 0
        assert toil.run(r""" fib_iter(1) """) == 1
        assert toil.run(r""" fib_iter(6) """) == 8

        toil.run(r"""
            def fib_rec(n) do
                if n == 0 then 0
                else if n == 1 then 1
                else fib_rec(n - 1) + fib_rec(n - 2) end end
            end
        """)
        assert toil.run(r""" fib_rec(0) """) == 0
        assert toil.run(r""" fib_rec(1) """) == 1
        assert toil.run(r""" fib_rec(6) """) == 8

    def test_GCD(self):
        toil.run(r"""
            def gcd_iter(a, b) do
                while b > 0 do
                    tmp := b; b = a % b; a = tmp
                end;
                a
            end
        """)
        assert toil.run(r""" gcd_iter(12, 18) """) == 6

        toil.run(r"""
            def gcd_rec(a, b) do
                if b == 0 then a else gcd_rec(b, a % b) end
            end
        """)
        assert toil.run(r""" gcd_rec(12, 18) """) == 6

    def test_mutual_recursion(self):
        toil.run(r"""
            def even(n) do if n == 0 then True else odd(n - 1) end end;
            def odd(n) do if n == 0 then False else even(n - 1) end end
        """)
        assert toil.run(r""" even(2) """) is True
        assert toil.run(r""" even(3) """) is False
        assert toil.run(r""" odd(2) """) is False
        assert toil.run(r""" odd(3) """) is True

    def test_counter(self):
        toil.run(r"""
            def make_counter() do
                count := 0;
                func do count = count + 1 end
            end
        """)
        toil.run(r""" c1 := make_counter() """)
        toil.run(r""" c2 := make_counter() """)
        assert toil.run(r""" c1() """) == 1
        assert toil.run(r""" c1() """) == 2
        assert toil.run(r""" c2() """) == 1
        assert toil.run(r""" c2() """) == 2

    def test_binary_search_tree(self, capsys):
        toil.run(r"""
            def node(val, left, right) do
                func op do
                    if op == 1 then val
                    else if op == 2 then left
                    else right end end
                end
            end
        """)
        toil.run(r""" n1 := node(2, 3, 4) """)
        assert toil.run(r""" n1(1) """) == 2
        assert toil.run(r""" n1(2) """) == 3
        assert toil.run(r""" n1(3) """) == 4

        toil.run(r"""
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
        toil.run(r""" bst := None """)
        toil.run(r""" bst = bst_put(bst, 7) """)
        toil.run(r""" bst = bst_put(bst, 3) """)
        toil.run(r""" bst = bst_put(bst, 1) """)
        toil.run(r""" bst = bst_put(bst, 9) """)
        toil.run(r""" bst = bst_put(bst, 5) """)

        toil.run(r"""
            def bst_walk(bst) do
                if bst == None then None
                else
                    bst_walk(bst(2)); print(bst(1)); bst_walk(bst(3))
                end
            end
        """)
        toil.run(r"""
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

        toil.run(r""" bst_walk(bst) """)
        assert capsys.readouterr().out == "1\n3\n5\n7\n9\n"

        toil.run(r"""
            i := 0;
            while i < 10 do
                print(bst_find(bst, i));
                i = i + 1
            end
        """)
        assert capsys.readouterr().out == "False\n1\nFalse\n3\nFalse\n5\nFalse\n7\nFalse\n9\n"


import os, sys, io, runpy

class TestCommandLine:
    def test_from_file(self, tmp_path, capsys, monkeypatch):
        script_file = tmp_path / "test.toil"
        script_file.write_text("0")

        toil_script = os.path.join(os.path.dirname(__file__), "toil.py")
        monkeypatch.setattr(sys, "argv", ["toil.py", "--run", str(script_file)])

        with pytest.raises(SystemExit) as e:
            runpy.run_path(toil_script, run_name="__main__")

        assert e.value.code == 0
        assert capsys.readouterr().out == ""

    def test_repl(self, capsys, monkeypatch):
        toil_script = os.path.join(os.path.dirname(__file__), "toil.py")
        monkeypatch.setattr(sys, "argv", ["toil.py", "--rcepl"])
        monkeypatch.setattr(sys, "stdin", io.StringIO("0\n"))

        with pytest.raises(SystemExit) as e:
            runpy.run_path(toil_script, run_name="__main__")

        out = capsys.readouterr().out
        assert "AST:\n0" in out
        assert "Code:" in out
        assert "Output:" in out
        assert "Result:\n0\n" in out
        assert e.value.code == 0


if __name__ == "__main__":
    pytest.main([__file__])
