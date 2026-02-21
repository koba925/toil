import pytest
from toil import Interpreter


class TestBase:
    @pytest.fixture(autouse=True)
    def set_interpreter(self):
        self.i = Interpreter().init_env()

    def parse_from_src(self, src):
        return self.i.parse(self.i.scan(src))


class TestScan(TestBase):
    def test_number(self):
        assert self.i.scan("""2""") == [2, "$EOF"]
        assert self.i.scan(""" 3 """) == [3, "$EOF"]
        assert self.i.scan("""\t4\n5\n""") == [4, 5, "$EOF"]
        assert self.i.scan(""" """) == ["$EOF"]

    def test_operator(self):
        assert self.i.scan("""1 + 2""") == [1, "+", 2, "$EOF"]
        assert self.i.scan("""1 * 2""") == [1, "*", 2, "$EOF"]
        assert self.i.scan("""1 / 2""") == [1, "/", 2, "$EOF"]

    def test_bool_none_ident(self):
        assert self.i.scan("True") == [True, "$EOF"]
        assert self.i.scan("False") == [False, "$EOF"]
        assert self.i.scan("None") == [None, "$EOF"]
        assert self.i.scan("a") == ["a", "$EOF"]

    def test_define(self):
        assert self.i.scan("a := 2") == ["a", ":=", 2, "$EOF"]

class TestParse(TestBase):
    def test_comparison(self):
        assert self.parse_from_src("2 == 3 == 4") == (
            "equal", [("equal", [2, 3]), 4]
        )

    def test_add_sub(self):
        assert self.parse_from_src("1 + 2") == ("add", [1, 2])
        assert self.parse_from_src("1 - 2") == ("sub", [1, 2])
        assert self.parse_from_src("1 + 2 * 3") == ("add", [1, ("mul", [2, 3])])
        assert self.parse_from_src("1 * 2 + 3") == ("add", [("mul", [1, 2]), 3])

    def test_mul_div(self):
        assert self.parse_from_src("1 * 2") == ("mul", [1, 2])
        assert self.parse_from_src("1 / 2") == ("div", [1, 2])
        assert self.parse_from_src("1 * 2 / 3") == ("div", [("mul", [1, 2]), 3])

    def test_not(self):
        assert self.parse_from_src("not True") == ("not", [True])
        assert self.parse_from_src("not not False") == ("not", [("not", [False])])

    def test_neg(self):
        assert self.parse_from_src("-2") == ("neg", [2])
        assert self.parse_from_src("--3") == ("neg", [("neg", [3])])

    def test_number(self):
        assert self.parse_from_src("2") == 2

    def test_bool_none(self):
        assert self.parse_from_src("True") is True
        assert self.parse_from_src("False") is False
        assert self.parse_from_src("None") is None

    def test_paren(self):
        assert self.parse_from_src("(1 + 2)") == ("add", [1, 2])
        assert self.parse_from_src("(1 + 2) * 3") == ("mul", [("add", [1, 2]), 3])

    def test_seq(self):
        assert self.parse_from_src("2; 3") == ("seq", [2, 3])
        assert self.parse_from_src("not True; False") == ("seq", [("not", [True]), False])

    def test_if(self):
        assert self.parse_from_src("if True then 2 else 3 end") == \
            ("if", True, 2, 3)
        assert self.parse_from_src("if not True then 2 + 3 else 4; 5 end") == \
            ("if", ('not', [True]), ('add', [2, 3]), ('seq', [4, 5]))

    def test_define(self):
        assert self.parse_from_src("a := not True") == ("define", "a", ("not", [True]))
        assert self.parse_from_src("a := b := 2") == ("define", "a", ("define", "b", 2))

    def test_call(self):
        assert self.parse_from_src("print()") == ("print", [])
        assert self.parse_from_src("neg(2)") == ("neg", [2])
        assert self.parse_from_src("add(2, mul(3, 4))") == ("add", [2, ("mul", [3, 4])])

    def test_no_token(self):
        with pytest.raises(AssertionError):
            self.parse_from_src("")

    def test_extra_token(self):
        with pytest.raises(AssertionError):
            self.parse_from_src("2 3")

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
        assert self.i.go(""" 3""") == 3
        assert self.i.go("""4 \t""") == 4
        assert self.i.go("""56\n""") == 56

    def test_comparison(self):
        assert self.i.go("2 + 5 == 3 + 4") is True
        assert self.i.go("2 + 3 == 3 + 4") is False
        assert self.i.go("2 + 5 != 3 + 4") is False
        assert self.i.go("2 + 3 != 3 + 4") is True

        assert self.i.go("2 + 4 < 3 + 4") is True
        assert self.i.go("2 + 5 < 3 + 4") is False
        assert self.i.go("2 + 5 < 2 + 4") is False
        assert self.i.go("2 + 4 > 3 + 4") is False
        assert self.i.go("2 + 5 > 3 + 4") is False
        assert self.i.go("2 + 5 > 2 + 4") is True

        assert self.i.go("2 + 4 <= 3 + 4") is True
        assert self.i.go("2 + 5 <= 3 + 4") is True
        assert self.i.go("2 + 5 <= 2 + 4") is False
        assert self.i.go("2 + 4 >= 3 + 4") is False
        assert self.i.go("2 + 5 >= 3 + 4") is True
        assert self.i.go("2 + 5 >= 2 + 4") is True

        assert self.i.go("2 == 2 == 2") is False

    def test_add_sub(self):
        assert self.i.go("""2 + 3""") == 5
        assert self.i.go("""5 - 3""") == 2
        assert self.i.go("""2 + 3 - 4 + 5""") == 6

    def test_mul_div_mod(self):
        assert self.i.go("""2 * 3""") == 6
        assert self.i.go("""6 / 3""") == 2
        assert self.i.go("""7 % 3""") == 1
        assert self.i.go("""2 * 3 / 2""") == 3
        assert self.i.go("""2 * 3 + 4""") == 10
        assert self.i.go("""2 + 3 * 4""") == 14

    def test_not(self):
        assert self.i.go("not True") is False
        assert self.i.go("not False") is True
        assert self.i.go("not not True") is True
        assert self.i.go("not 2 == 3") is True

    def test_neg(self):
        assert self.i.go("-2") == -2
        assert self.i.go("--2") == 2
        assert self.i.go("-2 * 3") == -6

    def test_number(self):
        assert self.i.go("""2""") == 2

        with pytest.raises(AssertionError):
            self.i.go("""a""")

    def test_bool_none(self):
        assert self.i.go("True") is True
        assert self.i.go("False") is False
        assert self.i.go("None") is None

    def test_paren(self):
        assert self.i.go("(2 + 3) * 4") == 20
        assert self.i.go("2 * (3 + 4)") == 14
        assert self.i.go("2 * (3 + 4 * 5)") == 46

    def test_seq(self):
        assert self.i.go("2; 3") == 3
        assert self.i.go("2; 3; 4") == 4
        assert self.i.go("True; not True") is False

    def test_if(self):
        assert self.i.go("if True then 2 else 3 end") == 2
        assert self.i.go("if not True then 2 + 3 else 4; 5 end") == 5

        with pytest.raises(AssertionError):
            self.i.go(""" if True then 2 else 3 """)
        with pytest.raises(AssertionError):
            self.i.go(""" if True then 2 end """)
        with pytest.raises(AssertionError):
            self.i.go(""" if True else 2 end """)

    def test_var_define(self):
        assert self.i.go("a := not True") == False
        assert self.i.go("a") == False
        assert self.i.go("a := b := not False") == True
        assert self.i.go("a") == True
        assert self.i.go("b") == True

    def test_call(self, capsys):
        assert self.i.go("add(2, 3)") == 5
        assert self.i.go("add(2, mul(3, 4))") == 14
        self.i.go("print(5)")
        assert capsys.readouterr().out == "5\n"
        self.i.go("print(6, 7)")
        assert capsys.readouterr().out == "6 7\n"
        self.i.go("print()")
        assert capsys.readouterr().out == "\n"

    def test_no_code(self):
        with pytest.raises(AssertionError):
            self.i.go(""" """)

    def test_extra_token(self):
        with pytest.raises(AssertionError):
            self.i.go("""7 8""")
