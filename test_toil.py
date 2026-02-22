import pytest
from toil import Interpreter


class TestBase:
    @pytest.fixture(autouse=True)
    def set_interpreter(self):
        self.i = Interpreter().init_env()


class TestScan(TestBase):
    def test_number(self):
        assert self.i.scan("""2""") == [2, "$EOF"]
        assert self.i.scan(""" 3 """) == [3, "$EOF"]
        assert self.i.scan(""" \t4\n5\n """) == [4, 5, "$EOF"]
        assert self.i.scan("""  """) == ["$EOF"]

    def test_operator(self):
        assert self.i.scan(""" 1 + 2 """) == [1, "+", 2, "$EOF"]
        assert self.i.scan(""" 1 * 2 """) == [1, "*", 2, "$EOF"]
        assert self.i.scan(""" 1 / 2 """) == [1, "/", 2, "$EOF"]

    def test_bool_none_ident(self):
        assert self.i.scan(""" True """) == [True, "$EOF"]
        assert self.i.scan(""" False """) == [False, "$EOF"]
        assert self.i.scan(""" None """) == [None, "$EOF"]
        assert self.i.scan(""" a """) == ["a", "$EOF"]

    def test_define_assign(self):
        assert self.i.scan(""" a := 2 """) == ["a", ":=", 2, "$EOF"]
        assert self.i.scan(""" a = 2 """) == ["a", "=", 2, "$EOF"]

class TestParse(TestBase):
    def test_comparison(self):
        assert self.i.ast(""" 2 == 3 == 4 """) == (
            "equal", [("equal", [2, 3]), 4]
        )

    def test_add_sub(self):
        assert self.i.ast(""" 2 + 3 """) == ("add", [2, 3])
        assert self.i.ast(""" 2 - 3 """) == ("sub", [2, 3])
        assert self.i.ast(""" 2 + 3 * 4 """) == ("add", [2, ("mul", [3, 4])])
        assert self.i.ast(""" 2 * 3 + 4 """) == ("add", [("mul", [2, 3]), 4])

    def test_mul_div(self):
        assert self.i.ast(""" 2 * 3 """) == ("mul", [2, 3])
        assert self.i.ast(""" 2 / 3 """) == ("div", [2, 3])
        assert self.i.ast(""" 2 * 3 / 4 """) == ("div", [("mul", [2, 3]), 4])

    def test_not(self):
        assert self.i.ast(""" not True """) == ("not", [True])
        assert self.i.ast(""" not not False """) == ("not", [("not", [False])])

    def test_neg(self):
        assert self.i.ast(""" -2 """) == ("neg", [2])
        assert self.i.ast(""" --3 """) == ("neg", [("neg", [3])])

    def test_number(self):
        assert self.i.ast(""" 2 """) == 2

    def test_bool_none(self):
        assert self.i.ast(""" True """) is True
        assert self.i.ast(""" False """) is False
        assert self.i.ast(""" None """) is None

    def test_paren(self):
        assert self.i.ast(""" (1 + 2) """) == ("add", [1, 2])
        assert self.i.ast(""" (1 + 2) * 3 """) == ("mul", [("add", [1, 2]), 3])

    def test_seq(self):
        assert self.i.ast(""" 2; 3 """) == ("seq", [2, 3])
        assert self.i.ast(""" not True; False """) == ("seq", [("not", [True]), False])

    def test_if(self):
        assert self.i.ast(""" if True then 2 else 3 end """) == \
            ("if", True, 2, 3)
        assert self.i.ast(""" if not True then 2 + 3 else 4; 5 end """) == \
            ("if", ('not', [True]), ('add', [2, 3]), ('seq', [4, 5]))

    def test_define(self):
        assert self.i.ast(""" a := not True """) == ("define", "a", ("not", [True]))
        assert self.i.ast(""" a := b := 2 """) == ("define", "a", ("define", "b", 2))

    def test_assign(self):
        assert self.i.ast(""" a = 1 """) == ("assign", "a", 1)
        assert self.i.ast(""" a = b = 2 """) == ("assign", "a", ("assign", "b", 2))
        assert self.i.ast(""" a := b = 2 """) == ("define", "a", ("assign", "b", 2))
        assert self.i.ast(""" a := b = c := 3 """) == ("define", "a", ("assign", "b", ("define", "c", 3)))

    def test_call(self):
        assert self.i.ast(""" print() """) == ("print", [])
        assert self.i.ast(""" neg(2) """) == ("neg", [2])
        assert self.i.ast(""" add(2, mul(3, 4)) """) == ("add", [2, ("mul", [3, 4])])

    def test_func(self):
        assert self.i.ast(""" func do 2 end """) == ("func", [], 2)
        assert self.i.ast(""" func a do a + 2 end """) == ("func", ["a"], ("add", ["a", 2]))
        assert self.i.ast(""" func a, b do a + b end """) == ("func", ["a", "b"], ("add", ["a", "b"]))

        with pytest.raises(AssertionError, match="Expected `do`"):
            self.i.ast(""" func a 2 end """)
        with pytest.raises(AssertionError, match="Expected `end`"):
            self.i.ast(""" func a do 2 """)

    def test_no_token(self):
        with pytest.raises(AssertionError):
            self.i.ast("""  """)

    def test_extra_token(self):
        with pytest.raises(AssertionError):
            self.i.ast(""" 2 3 """)

class TestEvaluate(TestBase):
    def test_evaluate_value(self):
        assert self.i.evaluate(None) is None
        assert self.i.evaluate(5) == 5
        assert self.i.evaluate(True) is True
        assert self.i.evaluate(False) is False

    def test_seq(self, capsys):
        self.i.evaluate(("seq", [
            ("print", [2]),
            ("print", [3])
        ]))
        assert capsys.readouterr().out == "2\n3\n"

    def test_evaluate_if(self):
        assert self.i.evaluate(("if", True, 2, 3)) == 2
        assert self.i.evaluate(("if", False, 2, 3)) == 3
        assert self.i.evaluate(("if", ("if", True, True, False), 2, 3)) == 2
        assert self.i.evaluate(("if", True, ("if", True, 2, 3), 4)) == 2
        assert self.i.evaluate(("if", False, 2, ("if", False, 3, 4))) == 4

    def test_evaluate_variable(self):
        assert self.i.evaluate(("define", "a", 2)) == 2
        assert self.i.evaluate("a") == 2

        assert self.i.evaluate(("define", "b", True)) == True
        assert self.i.evaluate(("if", "b", 2, 3)) == 2

        assert self.i.evaluate(("define", "c", ("if", False, 2, 3))) == 3
        assert self.i.evaluate("c") == 3

    def test_evaluate_undefined_variable(self):
        with pytest.raises(AssertionError):
            self.i.evaluate("a")

    def test_evaluate_assign(self):
        self.i.evaluate(("define", "a", 1))
        assert self.i.evaluate(("assign", "a", 2)) == 2
        assert self.i.evaluate("a") == 2
        with pytest.raises(AssertionError):
            self.i.evaluate(("assign", "b", 2))

    def test_evaluate_scope(self, capsys):
        self.i.evaluate(("define", "a", 2))
        assert self.i.evaluate("a") == 2
        assert self.i.evaluate(("scope", "a")) == 2

        assert self.i.evaluate(("scope", ("seq", [
            ("print", ["a"]),
            ("define", "a", 3),
            ("print", ["a"]),
            ("define", "b", 4),
            ("print", ["b"]),
            "b"
        ]))) == 4
        assert capsys.readouterr().out == "2\n3\n4\n"

        assert self.i.evaluate("a") == 2

        with pytest.raises(AssertionError):
            self.i.evaluate("b")

    def test_builtin_functions(self, capsys):
        assert self.i.evaluate(("add", [2, 3])) == 5
        assert self.i.evaluate(("sub", [5, 3])) == 2
        assert self.i.evaluate(("mul", [2, 3])) == 6

        assert self.i.evaluate(("equal", [2, 2])) is True
        assert self.i.evaluate(("equal", [2, 3])) is False

        assert self.i.evaluate(("add", [2, ("mul", [3, 4])])) == 14

        self.i.evaluate(("print", [2, 3]))
        assert capsys.readouterr().out == "2 3\n"

        self.i.evaluate(("print", [("add", [5, 5])]))
        assert capsys.readouterr().out == "10\n"

    def test_user_func(self):
        self.i.evaluate(("define", "add2", ("func", ["a"],
            ("add", ["a", 2])
        )))
        assert self.i.evaluate(("add2", [3])) == 5

        self.i.evaluate(("define", "sum3", ("func",["a", "b", "c"],
            ("add", ["a", ("add", ["b", "c"])])
        )))
        assert self.i.evaluate(("sum3", [2, 3, 4])) == 9

    def test_recursion(self):
        self.i.evaluate(("define", "fac", ("func",["n"],
            ("if", ("equal", ["n", 1]),
                1,
                ("mul", ["n", ("fac", [("sub", ["n", 1])])])
            )
        )))
        assert self.i.evaluate(("fac", [1])) == 1
        assert self.i.evaluate(("fac", [3])) == 6
        assert self.i.evaluate(("fac", [5])) == 120

    def test_scope_leak(self):
        self.i.evaluate(("define", "x", 2))
        self.i.evaluate(("define", "f", ("func", ["x"], 3)))
        self.i.evaluate(("f", [4]))
        assert self.i.evaluate("x") == 2

    def test_closure(self):
        self.i.evaluate(("define", "x", 2))
        self.i.evaluate(("define", "return_x", ("func", [], "x")))
        assert self.i.evaluate(("return_x", [])) == 2
        assert self.i.evaluate(("scope", ("seq", [
            ("define", "x", 3),
            ("return_x", [])
        ]))) == 2
        assert self.i.evaluate("x") == 2

    def test_adder(self):
        self.i.evaluate(("define", "make_adder", ("func", ["n"],
            ("func", ["m"], ("add", ["n", "m"]))
        )))
        self.i.evaluate(("define", "add2", ("make_adder", [2])))
        self.i.evaluate(("define", "add3", ("make_adder", [3])))

        assert self.i.evaluate(("add2", [3])) == 5
        assert self.i.evaluate(("add3", [4])) == 7

    def test_shadowing(self):
        self.i.evaluate(("define", "make_shadow", ("func", ["x"],
            ("func", [],
                ("seq", [
                    ("define", "x", 3),
                    "x"
                ])
            )
        )))
        self.i.evaluate(("define", "g", ("make_shadow", [2])))
        assert self.i.evaluate(("g", [])) == 3

class TestGo(TestBase):
    def test_whitespace(self):
        assert self.i.go("""  3 """) == 3
        assert self.i.go(""" 4 \t """) == 4
        assert self.i.go(""" 56\n """) == 56

    def test_comparison(self):
        assert self.i.go(""" 2 + 5 == 3 + 4 """) is True
        assert self.i.go(""" 2 + 3 == 3 + 4 """) is False
        assert self.i.go(""" 2 + 5 != 3 + 4 """) is False
        assert self.i.go(""" 2 + 3 != 3 + 4 """) is True

        assert self.i.go(""" 2 + 4 < 3 + 4 """) is True
        assert self.i.go(""" 2 + 5 < 3 + 4 """) is False
        assert self.i.go(""" 2 + 5 < 2 + 4 """) is False
        assert self.i.go(""" 2 + 4 > 3 + 4 """) is False
        assert self.i.go(""" 2 + 5 > 3 + 4 """) is False
        assert self.i.go(""" 2 + 5 > 2 + 4 """) is True

        assert self.i.go(""" 2 + 4 <= 3 + 4 """) is True
        assert self.i.go(""" 2 + 5 <= 3 + 4 """) is True
        assert self.i.go(""" 2 + 5 <= 2 + 4 """) is False
        assert self.i.go(""" 2 + 4 >= 3 + 4 """) is False
        assert self.i.go(""" 2 + 5 >= 3 + 4 """) is True
        assert self.i.go(""" 2 + 5 >= 2 + 4 """) is True

        assert self.i.go(""" 2 == 2 == 2 """) is False

    def test_add_sub(self):
        assert self.i.go(""" 2 + 3 """) == 5
        assert self.i.go(""" 5 - 3 """) == 2
        assert self.i.go(""" 2 + 3 - 4 + 5 """) == 6

    def test_mul_div_mod(self):
        assert self.i.go(""" 2 * 3 """) == 6
        assert self.i.go(""" 6 / 3 """) == 2
        assert self.i.go(""" 7 % 3 """) == 1
        assert self.i.go(""" 2 * 3 / 2 """) == 3
        assert self.i.go(""" 2 * 3 + 4 """) == 10
        assert self.i.go(""" 2 + 3 * 4 """) == 14

    def test_not(self):
        assert self.i.go(""" not True """) is False
        assert self.i.go(""" not False """) is True
        assert self.i.go(""" not not True """) is True
        assert self.i.go(""" not 2 == 3 """) is True

    def test_neg(self):
        assert self.i.go(""" -2 """) == -2
        assert self.i.go(""" --2 """) == 2
        assert self.i.go(""" -2 * 3 """) == -6

    def test_number(self):
        assert self.i.go(""" 2 """) == 2

        with pytest.raises(AssertionError):
            self.i.go(""" a """)

    def test_bool_none(self):
        assert self.i.go(""" True """) is True
        assert self.i.go(""" False """) is False
        assert self.i.go(""" None """) is None

    def test_paren(self):
        assert self.i.go(""" (2 + 3) * 4 """) == 20
        assert self.i.go(""" 2 * (3 + 4) """) == 14
        assert self.i.go(""" 2 * (3 + 4 * 5) """) == 46

    def test_seq(self):
        assert self.i.go(""" 2; 3 """) == 3
        assert self.i.go(""" 2; 3; 4 """) == 4
        assert self.i.go(""" True; not True """) is False

    def test_if(self):
        assert self.i.go(""" if True then 2 else 3 end """) == 2
        assert self.i.go(""" if not True then 2 + 3 else 4; 5 end """) == 5

        with pytest.raises(AssertionError):
            self.i.go(""" if True then 2 else 3 """)
        with pytest.raises(AssertionError):
            self.i.go(""" if True then 2 end """)
        with pytest.raises(AssertionError):
            self.i.go(""" if True else 2 end """)

    def test_var_define(self):
        assert self.i.go(""" a := not True """) == False
        assert self.i.go(""" a """) == False
        assert self.i.go(""" a := b := not False """) == True
        assert self.i.go(""" a """) == True
        assert self.i.go(""" b """) == True

    def test_assign(self):
        assert self.i.go(""" a := 1; a = 2; a """) == 2
        assert self.i.go(""" a := 1; b := 2; a = b = 3; a """) == 3
        assert self.i.go(""" a := 2; a = 3 """) == 3
        assert self.i.go(""" a := b := 2; a = b = 3 """) == 3

    def test_scope_assign(self, capsys):
        self.i.go("""
            a := b := 2;
            print(a, b);
            scope
                print(a, b);
                a := 3;
                b = 4;
                print(a, b);
                c := 5;
                print(a, b, c)
            end;
            print(a, b)
        """)
        assert capsys.readouterr().out == "2 2\n2 2\n3 4\n3 4 5\n2 4\n"

        with pytest.raises(AssertionError):
            self.i.go(""" c """)

    def test_call(self, capsys):
        assert self.i.go(""" add(2, 3) """) == 5
        assert self.i.go(""" add(2, mul(3, 4)) """) == 14
        self.i.go(""" print(5) """)
        assert capsys.readouterr().out == "5\n"
        self.i.go(""" print(6, 7) """)
        assert capsys.readouterr().out == "6 7\n"
        self.i.go(""" print() """)
        assert capsys.readouterr().out == "\n"

    def test_func(self):
        assert self.i.go(""" func do 2 end () """) == 2
        assert self.i.go(""" func a do a + 2 end (3) """) == 5
        assert self.i.go(""" func a, b do a + b end (2, 3) """) == 5

    def test_fac(self):
        assert self.i.go("""
            fac := func n do
                if n == 1 then 1 else n * fac(n - 1) end
            end;
            fac(5)
        """) == 120

    def test_fib(self):
        assert self.i.go("""
            fib := func n do
                if n < 2 then n else fib(n - 1) + fib(n - 2) end
            end;
            fib(7)
        """) == 13

    def test_gcd(self):
        assert self.i.go("""
            gcd := func a, b do
                if a == 0 then b else gcd(b % a, a) end
            end;
            gcd(24, 36)
        """) == 12

    def test_mutual_recursion(self):
        self.i.go("""
            is_even := func n do if n == 0 then True else is_odd(n - 1) end end;
            is_odd := func n do if n == 0 then False else is_even(n - 1) end end
        """)
        assert self.i.go(""" is_even(10) """) is True
        assert self.i.go(""" is_odd(10) """) is False

    def test_no_code(self):
        with pytest.raises(AssertionError):
            self.i.go("""  """)

    def test_extra_token(self):
        with pytest.raises(AssertionError):
            self.i.go(""" 7 8 """)

if __name__ == "__main__":
    pytest.main([__file__])
