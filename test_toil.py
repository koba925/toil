import pytest
from toil import Interpreter, Ident


class TestBase:
    @pytest.fixture(autouse=True)
    def set_interpreter(self):
        self.i = Interpreter().init_env().stdlib()

    def scan(self, src): return self.i.scan(src)
    def parse(self, tokens): return self.i.parse(tokens)
    def ast(self, src): return self.i.ast(src)
    def eval(self, ast): return self.i.eval(ast)
    def walk(self, src): return self.i.walk(src)
    def go(self, src): return self.walk(src)


class TestScan(TestBase):
    def test_number(self):
        assert self.scan("""2""") == [2, Ident("$EOF")]
        assert self.scan(""" 3 """) == [3, Ident("$EOF")]
        assert self.scan(""" \t4\n5\n """) == [4, 5, Ident("$EOF")]
        assert self.scan("""  """) == [Ident("$EOF")]

    def test_operator(self):
        assert self.scan(""" 1 + 2 """) == [1, Ident("+"), 2, Ident("$EOF")]
        assert self.scan(""" 1 * 2 """) == [1, Ident("*"), 2, Ident("$EOF")]
        assert self.scan(""" 1 / 2 """) == [1, Ident("/"), 2, Ident("$EOF")]

    def test_bool_none_ident(self):
        assert self.scan(""" True """) == [True, Ident("$EOF")]
        assert self.scan(""" False """) == [False, Ident("$EOF")]
        assert self.scan(""" None """) == [None, Ident("$EOF")]
        assert self.scan(""" a """) == [Ident("a"), Ident("$EOF")]

    def test_define_assign(self):
        assert self.scan(""" a := 2 """) == [Ident("a"), Ident(":="), 2, Ident("$EOF")]
        assert self.scan(""" a = 2 """) == [Ident("a"), Ident("="), 2, Ident("$EOF")]

    def test_string(self):
        assert self.scan(""" 'hello' """) == ["hello", Ident("$EOF")]
        assert self.scan(""" "hello" """) == ["hello", Ident("$EOF")]
        assert self.scan(r""" "a\nb" """) == ["a\nb", Ident("$EOF")]

class TestParse(TestBase):
    def test_comparison(self):
        assert self.ast(""" 2 == 3 == 4 """) == (
            Ident("equal"), [(Ident("equal"), [2, 3]), 4]
        )

    def test_add_sub(self):
        assert self.ast(""" 2 + 3 """) == (Ident("add"), [2, 3])
        assert self.ast(""" 2 - 3 """) == (Ident("sub"), [2, 3])
        assert self.ast(""" 2 + 3 * 4 """) == (Ident("add"), [2, (Ident("mul"), [3, 4])])
        assert self.ast(""" 2 * 3 + 4 """) == (Ident("add"), [(Ident("mul"), [2, 3]), 4])

    def test_mul_div(self):
        assert self.ast(""" 2 * 3 """) == (Ident("mul"), [2, 3])
        assert self.ast(""" 2 / 3 """) == (Ident("div"), [2, 3])
        assert self.ast(""" 2 * 3 / 4 """) == (Ident("div"), [(Ident("mul"), [2, 3]), 4])

    def test_not(self):
        assert self.ast(""" not True """) == (Ident("not"), [True])
        assert self.ast(""" not not False """) == (Ident("not"), [(Ident("not"), [False])])

    def test_and_or(self):
        assert self.ast(""" True and False """) == (Ident('and'), [True, False])
        assert self.ast(""" True or False """) == (Ident('or'), [True, False])
        assert self.ast(""" True or False and True """) == (Ident('and'), [(Ident('or'), [True, False]), True])
        assert self.ast(""" a := False and not False """) == (Ident('define'), [Ident('a'), (Ident('and'), [False, (Ident('not'), [False])])])
        assert self.ast(""" a := False or not False """) == (Ident('define'), [Ident('a'), (Ident('or'), [False, (Ident('not'), [False])])])

    def test_neg(self):
        assert self.ast(""" -2 """) == (Ident("neg"), [2])
        assert self.ast(""" --3 """) == (Ident("neg"), [(Ident("neg"), [3])])

    def test_number(self):
        assert self.ast(""" 2 """) == 2

    def test_bool_none(self):
        assert self.ast(""" True """) is True
        assert self.ast(""" False """) is False
        assert self.ast(""" None """) is None

    def test_paren(self):
        assert self.ast(""" (1 + 2) """) == (Ident("add"), [1, 2])
        assert self.ast(""" (1 + 2) * 3 """) == (Ident("mul"), [(Ident("add"), [1, 2]), 3])

    def test_string(self):
        assert self.ast(""" 'hello' """) == "hello"
        assert self.ast(""" "hello" """) == "hello"
        assert self.ast(r""" "a\nb" """) == "a\nb"

    def test_seq(self):
        assert self.ast(""" 2; 3 """) == (Ident("seq"), [2, 3])
        assert self.ast(""" not True; False """) == (Ident("seq"), [(Ident("not"), [True]), False])

    def test_if(self):
        assert self.ast(""" if True then 2 else 3 end """) == (
            Ident("__core_if_macro"), [True, 2, [], [3]])
        assert self.ast(""" if not True then 2 + 3 else 4; 5 end """) == (
            Ident("__core_if_macro"), [(Ident('not'), [True]), (Ident('add'), [2, 3]), [], [(Ident("seq"), [4, 5])]])

        assert self.ast(""" if 1 then 10 end """) == (Ident('__core_if_macro'), [1, 10, [], []])
        assert self.ast(""" if 1 then 10 else 20 end """) == (Ident("__core_if_macro"), [1, 10, [], [20]])
        assert self.ast(""" if 1 then 10 elif 2 then 20 end """) == (Ident("__core_if_macro"), [1, 10, [[2, 20]], []])
        assert self.ast(""" if 1 then 10 elif 2 then 20 else 30 end """) == (Ident("__core_if_macro"), [1, 10, [[2, 20]], [30]])
        assert self.ast(""" if 1 then 10 elif 2 then 20 elif 3 then 30 else 40 end """) == (Ident("__core_if_macro"), [1, 10, [[2, 20], [3, 30]], [40]])

    def test_define(self):
        assert self.ast(""" a := not True """) == (Ident("define"), [Ident("a"), (Ident("not"), [True])])
        assert self.ast(""" a := b := 2 """) == (Ident("define"), [Ident("a"), (Ident("define"), [Ident("b"), 2])])

    def test_assign(self):
        assert self.ast(""" a = 1 """) == (Ident("assign"), [Ident("a"), 1])
        assert self.ast(""" a = b = 2 """) == (Ident("assign"), [Ident("a"), (Ident("assign"), [Ident("b"), 2])])
        assert self.ast(""" a := b = 2 """) == (Ident("define"), [Ident("a"), (Ident("assign"), [Ident("b"), 2])])
        assert self.ast(""" a := b = c := 3 """) == (Ident("define"), [Ident("a"), (Ident("assign"), [Ident("b"), (Ident("define"), [Ident("c"), 3])])])

    def test_list_assign(self):
        assert self.ast(""" a[0] = 1 """) == (Ident("assign"), [(Ident("index"), [Ident("a"), 0]), 1])
        assert self.ast(""" a[1][2] = 3 """) == (Ident("assign"), [(Ident("index"), [(Ident("index"), [Ident("a"), 1]), 2]), 3])
        assert self.ast(""" a[0] = b[1] = 2 """) == (Ident("assign"), [(Ident("index"), [Ident("a"), 0]), (Ident("assign"), [(Ident("index"), [Ident("b"), 1]), 2])])

    def test_call(self):
        assert self.ast(""" print() """) == (Ident("print"), [])
        assert self.ast(""" neg(2) """) == (Ident("neg"), [2])
        assert self.ast(""" add(2, mul(3, 4)) """) == (Ident("add"), [2, (Ident("mul"), [3, 4])])

    def test_index(self):
        assert self.ast(""" a[0] """) == (Ident("index"), [Ident("a"), 0])
        assert self.ast(""" a[1][2] """) == (Ident("index"), [(Ident("index"), [Ident("a"), 1]), 2])

    def test_func(self):
        assert self.ast(""" func do 2 end """) == (Ident("__core_func"), [[], 2])
        assert self.ast(""" func a do a + 2 end """) == (Ident("__core_func"), [[Ident("a")], (Ident("add"), [Ident("a"), 2])])
        assert self.ast(""" func a, b do a + b end """) == (Ident("__core_func"), [[Ident("a"), Ident("b")], (Ident("add"), [Ident("a"), Ident("b")])])

        with pytest.raises(AssertionError):
            self.ast(""" func a 2 end """)
        with pytest.raises(AssertionError):
            self.ast(""" func a do 2 """)

    def test_no_token(self):
        with pytest.raises(AssertionError):
            self.ast("""  """)

    def test_extra_token(self):
        with pytest.raises(AssertionError):
            self.ast(""" 2 3 """)

class TestEvaluate(TestBase):
    def test_evaluate_value(self):
        assert self.eval(None) is None
        assert self.eval(5) == 5
        assert self.eval(True) is True
        assert self.eval(False) is False

    def test_seq(self, capsys):
        self.eval((Ident("seq"), [
            (Ident("print"), [2]),
            (Ident("print"), [3])
        ]))
        assert capsys.readouterr().out == "2\n3\n"

    def test_evaluate_if(self):
        assert self.eval((Ident("__core_if"), [True, 2, 3])) == 2
        assert self.eval((Ident("__core_if"), [False, 2, 3])) == 3
        assert self.eval((Ident("__core_if"), [(Ident("__core_if"), [True, True, False]), 2, 3])) == 2
        assert self.eval((Ident("__core_if"), [True, (Ident("__core_if"), [True, 2, 3]), 4])) == 2
        assert self.eval((Ident("__core_if"), [False, 2, (Ident("__core_if"), [False, 3, 4])])) == 4

    def test_evaluate_variable(self):
        assert self.eval((Ident("define"), [Ident("a"), 2])) == 2
        assert self.eval(Ident("a")) == 2

        assert self.eval((Ident("define"), [Ident("b"), True])) == True
        assert self.eval((Ident("__core_if"), [Ident("b"), 2, 3])) == 2

        assert self.eval((Ident("define"), [Ident("c"), (Ident("__core_if"), [False, 2, 3])])) == 3
        assert self.eval(Ident("c")) == 3

    def test_evaluate_undefined_variable(self):
        with pytest.raises(AssertionError):
            self.eval(Ident("a"))

    def test_evaluate_assign(self):
        self.eval((Ident("define"), [Ident("a"), 1]))
        assert self.eval((Ident("assign"), [Ident("a"), 2])) == 2
        assert self.eval(Ident("a")) == 2
        with pytest.raises(AssertionError):
            self.eval((Ident("assign"), [Ident("b"), 2]))

    def test_evaluate_scope(self, capsys):
        self.eval((Ident("define"), [Ident("a"), 2]))
        assert self.eval(Ident("a")) == 2
        assert self.eval((Ident("__core_scope"), [Ident("a")])) == 2

        assert self.eval((Ident("__core_scope"), [(Ident("seq"), [
            (Ident("print"), [Ident("a")]),
            (Ident("define"), [Ident("a"), 3]),
            (Ident("print"), [Ident("a")]),
            (Ident("define"), [Ident("b"), 4]),
            (Ident("print"), [Ident("b")]),
            Ident("b")
        ])])) == 4
        assert capsys.readouterr().out == "2\n3\n4\n"

        assert self.eval(Ident("a")) == 2

        with pytest.raises(AssertionError):
            self.eval(Ident("b"))

    def test_builtin_functions(self, capsys):
        assert self.eval((Ident("add"), [2, 3])) == 5
        assert self.eval((Ident("sub"), [5, 3])) == 2
        assert self.eval((Ident("mul"), [2, 3])) == 6

        assert self.eval((Ident("equal"), [2, 2])) is True
        assert self.eval((Ident("equal"), [2, 3])) is False

        assert self.eval((Ident("add"), [2, (Ident("mul"), [3, 4])])) == 14

        self.eval((Ident("print"), [2, 3]))
        assert capsys.readouterr().out == "2 3\n"

        self.eval((Ident("print"), [(Ident("add"), [5, 5])]))
        assert capsys.readouterr().out == "10\n"

    def test_user_func(self):
        self.eval((Ident("define"), [Ident("add2"), (Ident("__core_func"),
            [[Ident("a")], (Ident("add"), [Ident("a"), 2])]
        )]))
        assert self.eval((Ident("add2"), [3])) == 5

        self.eval((Ident("define"), [Ident("sum3"), (Ident("__core_func"),
            [[Ident("a"), Ident("b"), Ident("c")],(Ident("add"), [Ident("a"), (Ident("add"), [Ident("b"), Ident("c")])])]
        )]))
        assert self.eval((Ident("sum3"), [2, 3, 4])) == 9

    def test_recursion(self):
        self.eval((Ident("define"), [Ident("fac"), (Ident("__core_func"), [
            [Ident("n")],
            (Ident("__core_if"), [
                (Ident("equal"), [Ident("n"), 1]),
                1,
                (Ident("mul"), [Ident("n"), (Ident("fac"), [(Ident("sub"), [Ident("n"), 1])])])
        ])
        ])]))
        assert self.eval((Ident("fac"), [1])) == 1
        assert self.eval((Ident("fac"), [3])) == 6
        assert self.eval((Ident("fac"), [5])) == 120

    def test_scope_leak(self):
        self.eval((Ident("define"), [Ident("x"), 2]))
        self.eval((Ident("define"), [Ident("f"), (Ident("__core_func"), [[Ident("x")], 3])]))
        self.eval((Ident("f"), [4]))
        assert self.eval(Ident("x")) == 2

    def test_closure(self):
        self.eval((Ident("define"), [Ident("x"), 2]))
        self.eval((Ident("define"), [Ident("return_x"), (Ident("__core_func"), [[], Ident("x")])]))
        assert self.eval((Ident("return_x"), [])) == 2
        assert self.eval((Ident("__core_scope"), [(Ident("seq"), [
            (Ident("define"), [Ident("x"), 3]),
            (Ident("return_x"), [])
        ])])) == 2
        assert self.eval(Ident("x")) == 2

    def test_adder(self):
        self.eval((Ident("define"), [Ident("make_adder"), (Ident("__core_func"), [
            [Ident("n")],
            (Ident("__core_func"), [[Ident("m")], (Ident("add"), [Ident("n"), Ident("m")])])
        ])]))
        self.eval((Ident("define"), [Ident("add2"), (Ident("make_adder"), [2])]))
        self.eval((Ident("define"), [Ident("add3"), (Ident("make_adder"), [3])]))

        assert self.eval((Ident("add2"), [3])) == 5
        assert self.eval((Ident("add3"), [4])) == 7

    def test_shadowing(self):
        self.eval((Ident("define"), [Ident("make_shadow"), (Ident("__core_func"), [
            [Ident("x")],
            (Ident("__core_func"), [
                [],
                (Ident("seq"), [
                    (Ident("define"), [Ident("x"), 3]),
                    Ident("x")
                ])
            ])
        ])]))
        self.eval((Ident("define"), [Ident("g"), (Ident("make_shadow"), [2])]))
        assert self.eval((Ident("g"), [])) == 3

    def test_list(self):
        self.eval((Ident("define"), [Ident("a"), [1, 2, 3]]))
        assert self.eval(Ident("a")) == [1, 2, 3]
        assert self.eval((Ident("index"), [Ident("a"), 0])) == 1
        assert self.eval((Ident("index"), [Ident("a"), 2])) == 3

        self.eval((Ident("assign"), [(Ident("index"), [Ident("a"), 1]), 4]))
        assert self.eval(Ident("a")) == [1, 4, 3]

    def test_list_nested(self):
        self.eval((Ident("define"), [Ident("a"), [
            [1, 2],
            [3, 4]
        ]]))
        assert self.eval((Ident("index"), [(Ident("index"), [Ident("a"), 0]), 1])) == 2
        assert self.eval((Ident("index"), [(Ident("index"), [Ident("a"), 1]), 0])) == 3

        self.eval((Ident("assign"), [(Ident("index"), [(Ident("index"), [Ident("a"), 1]), 0]), 5]))
        assert self.eval((Ident("index"), [(Ident("index"), [Ident("a"), 1]), 0])) == 5

    def test_list_push_pop(self):
        self.eval((Ident("define"), [Ident("a"), [1, 2]]))
        self.eval((Ident("push"), [Ident("a"), 3]))
        assert self.eval(Ident("a")) == [1, 2, 3]
        assert self.eval((Ident("pop"), [Ident("a")])) == 3
        assert self.eval(Ident("a")) == [1, 2]

    def test_list_funcs(self):
        self.eval((Ident("define"), [Ident("a"), [1, 2, 3]]))
        assert self.eval((Ident("len"), [Ident("a")])) == 3
        assert self.eval((Ident("slice"), [Ident("a"), 1, None])) == [2, 3]
        assert self.eval((Ident("slice"), [Ident("a"), 1, 2])) == [2]
        assert self.eval((Ident("slice"), [Ident("a"), None, 2])) == [1, 2]
        assert self.eval((Ident("slice"), [Ident("a"), None, None])) == [1, 2, 3]

    def test_list_error(self):
        self.eval((Ident("define"), [Ident("a"), [1, 2]]))

        with pytest.raises(AssertionError, match="Invalid indexing"):
            self.eval((Ident("assign"), [(Ident("index"), [None, 0]), 1]))

        with pytest.raises(AssertionError, match="Invalid indexing"):
            self.eval((Ident("assign"), [(Ident("index"), [Ident("a"), None]), 1]))

class TestGo(TestBase):
    def test_whitespace(self):
        assert self.go("""  3 """) == 3
        assert self.go(""" 4 \t """) == 4
        assert self.go(""" 56\n """) == 56

    def test_comparison(self):
        assert self.go(""" 2 + 5 == 3 + 4 """) is True
        assert self.go(""" 2 + 3 == 3 + 4 """) is False
        assert self.go(""" 2 + 5 != 3 + 4 """) is False
        assert self.go(""" 2 + 3 != 3 + 4 """) is True

        assert self.go(""" 2 + 4 < 3 + 4 """) is True
        assert self.go(""" 2 + 5 < 3 + 4 """) is False
        assert self.go(""" 2 + 5 < 2 + 4 """) is False
        assert self.go(""" 2 + 4 > 3 + 4 """) is False
        assert self.go(""" 2 + 5 > 3 + 4 """) is False
        assert self.go(""" 2 + 5 > 2 + 4 """) is True

        assert self.go(""" 2 + 4 <= 3 + 4 """) is True
        assert self.go(""" 2 + 5 <= 3 + 4 """) is True
        assert self.go(""" 2 + 5 <= 2 + 4 """) is False
        assert self.go(""" 2 + 4 >= 3 + 4 """) is False
        assert self.go(""" 2 + 5 >= 3 + 4 """) is True
        assert self.go(""" 2 + 5 >= 2 + 4 """) is True

        assert self.go(""" 2 == 2 == 2 """) is False

    def test_add_sub(self):
        assert self.go(""" 2 + 3 """) == 5
        assert self.go(""" 5 - 3 """) == 2
        assert self.go(""" 2 + 3 - 4 + 5 """) == 6

    def test_arrow_function(self):
        assert self.go(""" ([] -> 2)() """) == 2
        assert self.go(""" ([a] -> a + 2)(3) """) == 5
        assert self.go(""" (a -> a + 2)(3) """) == 5
        assert self.go(""" ([[a, b]] -> a + b)([2, 3]) """) == 5
        assert self.go(""" ([a, b] -> a + b)(2, 3) """) == 5
        with pytest.raises(AssertionError, match="Argument mismatch"):
            self.go(""" ([a, b] -> a + b)(2) """)

        assert self.go(""" ([a, *b] -> b)(2, 3, 4) """) == [3, 4]
        assert self.go(""" ({a} -> a + 2)({a: 3}) """) == 5
        with pytest.raises(AssertionError, match="Argument mismatch"):
            self.go(""" ({a} -> a + 2)({b: 3}) """)

        assert self.go(""" (int(a) -> a + 2)(3) """) == 5
        with pytest.raises(AssertionError, match="Argument mismatch"):
            self.go(""" (int(a) -> a + 2)("aaa") """)

        assert self.go(""" (x -> x or 2)(False) """) == 2
        assert self.go(""" (a -> b -> a + b)(2)(3) """) == 5

        assert self.go(""" inc := a -> a + 1; inc(2) """) == 3
        assert self.go(""" myadd := [a, b] -> a + b; myadd(2, 3) """) == 5

    def test_mul_div_mod(self):
        assert self.go(""" 2 * 3 """) == 6
        assert self.go(""" 6 / 3 """) == 2
        assert self.go(""" 7 % 3 """) == 1
        assert self.go(""" 2 * 3 / 2 """) == 3
        assert self.go(""" 2 * 3 + 4 """) == 10
        assert self.go(""" 2 + 3 * 4 """) == 14

    def test_not(self):
        assert self.go(""" not True """) is False
        assert self.go(""" not False """) is True
        assert self.go(""" not not True """) is True
        assert self.go(""" not 2 == 3 """) is True

    def test_and_or(self, capsys):
        assert self.go(""" True and False """) is False
        assert self.go(""" True or False """) is True
        assert self.go(""" False and True """) is False
        assert self.go(""" False or True """) is True

        assert self.go(""" True and 2 """) == 2
        assert self.go(""" 0 and 2 / 0 """) == 0
        assert self.go(""" False or 2 """) == 2
        assert self.go(""" 1 or 2 / 0 """) == 1

        assert self.go(""" print(2) and 3 """) is None
        assert capsys.readouterr().out == "2\n"
        assert self.go(""" not print(2) or 3 """) is True
        assert capsys.readouterr().out == "2\n"

    def test_neg(self):
        assert self.go(""" -2 """) == -2
        assert self.go(""" --2 """) == 2
        assert self.go(""" -2 * 3 """) == -6

    def test_number(self):
        assert self.go(""" 2 """) == 2

        with pytest.raises(AssertionError):
            self.go(""" a """)

    def test_bool_none(self):
        assert self.go(""" True """) is True
        assert self.go(""" False """) is False
        assert self.go(""" None """) is None

    def test_paren(self):
        assert self.go(""" (2 + 3) * 4 """) == 20
        assert self.go(""" 2 * (3 + 4) """) == 14
        assert self.go(""" 2 * (3 + 4 * 5) """) == 46

    def test_seq(self):
        assert self.go(""" 2; 3 """) == 3
        assert self.go(""" 2; 3; 4 """) == 4
        assert self.go(""" True; not True """) is False

    def test_if(self):
        assert self.go(""" if True then 2 else 3 end """) == 2
        assert self.go(""" if False then 2 else 3 end """) == 3

        assert self.go(""" if not True then 2 + 3 else 4; 5 end """) == 5

        assert self.go(""" if True then 2 end """) == 2
        assert self.go(""" if False then 2 end """) is None

        assert self.go(""" if False then 2 elif True then 3 else 4 end """) == 3
        assert self.go(""" if False then 2 elif False then 3 else 4 end """) == 4

        with pytest.raises(AssertionError):
            self.go(""" if True then 2 else 3 """)
        with pytest.raises(AssertionError):
            self.go(""" if True else 2 end """)

    def test_var_define(self):
        assert self.go(""" a := not True """) == False
        assert self.go(""" a """) == False
        assert self.go(""" a := b := not False """) == True
        assert self.go(""" a """) == True
        assert self.go(""" b """) == True

    def test_assign(self):
        assert self.go(""" a := 1; a = 2; a """) == 2
        assert self.go(""" a := 1; b := 2; a = b = 3; a """) == 3
        assert self.go(""" a := 2; a = 3 """) == 3
        assert self.go(""" a := b := 2; a = b = 3 """) == 3

    def test_scope_assign(self, capsys):
        self.go("""
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
            self.go(""" c """)

    def test_while(self):
        assert self.go("""
            a := [];
            i := 0; while i < 3 do push(a, i); i = i + 1 end;
            a
        """) == [0, 1, 2]

        assert self.go("""
            a := [];
            i := 0; while i < 3 do push(a, i); i = i + 1 then a else 1/0 end
        """) == [0, 1, 2]

        assert self.go("""
            a := [];
            i := 0; while i < 3 do push(a, i); i = i + 1 then a end
        """) == [0, 1, 2]

        assert self.go(""" while False do 1 / 0 then 3 else 4 end """) == 3

        with pytest.raises(AssertionError, match="Expected do"):
            self.go(""" while do 2 then 3 else 4 end """)
        with pytest.raises(AssertionError, match="Expected do"):
            self.go(""" while True 2 then 3 else 4 end """)
        with pytest.raises(AssertionError, match="Expected end"):
            self.go(""" while True do 2 3 else 4 end """)
        with pytest.raises(AssertionError, match="Expected end"):
            self.go(""" while True do 2 then 3 4 end """)
        with pytest.raises(AssertionError, match="Expected end"):
            self.go(""" while True do 2 then 3 else end """)
        with pytest.raises(AssertionError, match="Expected end"):
            self.go(""" while True do 2 then 3 else 4 """)

    def test_continue(self):
        assert self.go("""
            a := [];
            i := 0; while i < 3 do
                i = i + 1; if i == 2 then continue() end;
                push(a, i)
            then a end
        """) == [1, 3]

        assert self.go("""
            a := []; i := 0; while i < 2 do
                j := 0; while j < 3 do
                    j = j + 1; if j == 2 then continue() end;
                    push(a, [i, j])
                end;
                i = i + 1
            then a end
        """) == [[0, 1], [0, 3], [1, 1], [1, 3]]

        assert self.go("""
            a := []; for i in [0, 1, 2] do
                if i == 1 then continue() end;
                push(a, i)
            then a end
        """) == [0, 2]

        assert self.go("""
            a := []; for i in [0, 1] do
                for j in [0, 1, 2] do
                    if j == 1 then continue() end;
                    push(a, [i, j])
                end
            then a end
        """) == [[0, 0], [0, 2], [1, 0], [1, 2]]

        with pytest.raises(AssertionError, match="Continue at top level"):
            self.go(""" continue() """)

    def test_break(self):
        assert self.go("""
            a := [];
            i := 0; while i < 3 do
                if i == 1 then break() end;
                push(a, i); i = i + 1
            then 1/0 else a end
        """) == [0]

        assert self.go("""
            a := [];
            i := 0; while i < 3 do
                if i == 1 then break() end;
                push(a, i); i = i + 1
            else a end
        """) == [0]

        assert self.go("""
            a := [];
            i := 0; while i < 2 do
                j := 0; while j < 3 do
                    if i == 0 and j == 1 then break() end;
                    push(a, [i, j]);
                    j = j + 1
                end;
                i = i + 1
            then a end
        """) == [[0, 0], [1, 0], [1, 1], [1, 2]]

        assert self.go("""
            a := [];
            i := 0; while i < 2 do
                j := 0; while j < 3 do
                    if i == 1 and j == 1 then break() end;
                    push(a, [i, j]);
                    j = j + 1
                else break() end;
                i = i + 1
            else a end
        """) == [[0, 0], [0, 1], [0, 2], [1, 0]]

        assert self.go(""" while True do break() end """) is None
        assert self.go(""" while True do break() else 2 end """) == 2

        assert self.go("""
            a := []; for i in [0, 1, 2] do
                if i == 1 then break() end;
                push(a, i)
            then 1/0 else a end
        """) == [0]

        assert self.go("""
            a := []; for i in [0, 1, 2] do
                if i == 1 then break() end;
                push(a, i)
            else a end
        """) == [0]

        assert self.go("""
            a := [];
            for i in [0, 1] do
                for j in [0, 1, 2] do
                    if i == 0 and j == 1 then break() end;
                    push(a, [i, j])
                end
            then a end
        """) == [[0, 0], [1, 0], [1, 1], [1, 2]]

        assert self.go("""
            a := [];
            for i in [0, 1] do
                for j in [0, 1, 2] do
                    if i == 1 and j == 1 then break() end;
                    push(a, [i, j])
                else break() end
            else a end
        """) == [[0, 0], [0, 1], [0, 2], [1, 0]]

        with pytest.raises(AssertionError, match="Break at top level"):
            self.go(""" break() """)

    def test_for(self):
        assert self.go(""" a := []; for i in [0, 1, 2] do push(a, i) end; a """) == [0, 1, 2]

        assert self.go("""
            a := []; for i in [0, 1, 2] do push(a, i) then [i, a] else 1/0 end
        """) == [2, [0, 1, 2]]

        assert self.go("""
            a := []; for i in [0, 1, 2] do push(a, i) then a end
        """) == [0, 1, 2]

        assert self.go("""
            a := []; for [i, j] in [[1, 2], [3, 4]] do push(a, [i, j]) then a end
        """) == [[1, 2], [3, 4]]

        assert self.go("""
            a := [];
            for [k, v] in {"a": 2, "b": 3}.items() do push(a, [k, v]) then a end
        """) == [['a', 2], ['b', 3]]

        assert self.go(""" for i in [] do 1/0 then 2 end """) == 2

        with pytest.raises(AssertionError):
            self.go(""" for in [] do 2 then 3 else 4 end """)
        with pytest.raises(AssertionError):
            self.go(""" for i [] do 2 then 3 else 4 end """)
        with pytest.raises(AssertionError, match="Expected do"):
            self.go(""" for i in do 2 then 3 else 4 end """)
        with pytest.raises(AssertionError, match="Expected end"):
            self.go(""" for i in [] do then 3 else 4 end """)
        with pytest.raises(AssertionError, match="Expected end"):
            self.go(""" for i in [] do 2 3 else 4 end """)
        with pytest.raises(AssertionError, match="Expected end"):
            self.go(""" for i in [] do 2 then else 4 end """)
        with pytest.raises(AssertionError, match="Expected end"):
            self.go(""" for i in [] do 2 then 3 4 end """)
        with pytest.raises(AssertionError, match="Expected end"):
            self.go(""" for i in [] do 2 then 3 else end """)
        with pytest.raises(AssertionError, match="Expected end"):
            self.go(""" for i in [] do 2 then 3 else 4 """)


    def test_call(self, capsys):
        assert self.go(""" add(2, 3) """) == 5
        assert self.go(""" add(2, mul(3, 4)) """) == 14
        self.go(""" print(5) """)
        assert capsys.readouterr().out == "5\n"
        self.go(""" print(6, 7) """)
        assert capsys.readouterr().out == "6 7\n"
        self.go(""" print() """)
        assert capsys.readouterr().out == "\n"

    def test_func(self):
        assert self.go(""" func do 2 end () """) == 2
        assert self.go(""" func a do a + 2 end (3) """) == 5
        assert self.go(""" func a, b do a + b end (2, 3) """) == 5

    def test_def_usage(self):
        self.go(""" def two do 2 end """)
        assert self.go(""" two() """) == 2
        self.go(""" def add2(a) do a + 2 end """)
        assert self.go(""" add2(3) """) == 5
        self.go(""" def sum(a, b, c) do a + b + c end """)
        assert self.go(""" sum(2, 3, 4) """) == 9

    def test_fac(self):
        assert self.go("""
            def fac(n) do
                if n == 1 then 1 else n * fac(n - 1) end
            end;
            fac(5)
        """) == 120

    def test_fib(self):
        self.go("""
            def fib(n) do
                if n == 0 then 0
                elif n == 1 then 1
                else fib(n - 1) + fib(n - 2)
                end
            end
        """)
        assert self.go(""" fib(0) """) == 0
        assert self.go(""" fib(1) """) == 1
        assert self.go(""" fib(7) """) == 13
        assert self.go(""" fib(9) """) == 34

    def test_gcd_recursive(self):
        assert self.go("""
            def gcd(a, b) do
                if a == 0 then b else gcd(b % a, a) end
            end;
            gcd(24, 36)
        """) == 12

    def test_mutual_recursion(self):
        self.go("""
            def is_even(n) do if n == 0 then True else is_odd(n - 1) end end;
            def is_odd(n) do if n == 0 then False else is_even(n - 1) end end
        """)
        assert self.go(""" is_even(10) """) is True
        assert self.go(""" is_odd(10) """) is False

    def test_gcd_iterative(self):
        assert self.go("""
            def gcd(a, b) do
                while a != 0 do
                    [a, b] := [b % a, a]
                end;
                b
            end;
            gcd(24, 36)
        """) == 12

    def test_no_code(self):
        with pytest.raises(AssertionError):
            self.go("""  """)

    def test_extra_token(self):
        with pytest.raises(AssertionError):
            self.go(""" 7 8 """)

    def test_list(self):
        assert self.go(""" [] """) == []
        assert self.go(""" [2 + 3] """) == [5]
        assert self.go(""" [2][0] """) == 2
        assert self.go(""" [2, 3, [4, 5]] """) == [2, 3, [4, 5]]

        self.go(""" a := [2, 3, [4, 5]] """)
        assert self.go(""" a[2][0] """) == 4
        assert self.go(""" a[2][-1] """) == 5

        self.go(""" b := [2, 3, [4, 5]] """)
        self.go(""" b[0] = 6 """)
        assert self.go(""" b[0] """) == 6
        self.go(""" b[2][1] = 7 """)
        assert self.go(""" b[2][1] """) == 7
        assert self.go(""" b """) == [6, 3, [4, 7]]

        self.go(""" c := func do [add, sub] end """)
        assert self.go(""" c()[0](2, 3) """) == 5

        self.go(""" d := [2, 3, 4] """)
        assert self.go(""" len(d) """) == 3
        assert self.go(""" slice(d, 1, None) """) == [3, 4]
        assert self.go(""" slice(d, 1, 2) """) == [3]
        assert self.go(""" slice(d, None, 2) """) == [2, 3]
        assert self.go(""" slice(d, None, None) """) == [2, 3, 4]
        assert self.go(""" push(d, 5) """) is None
        assert self.go(""" d """) == [2, 3, 4, 5]
        assert self.go(""" pop(d) """) == 5
        assert self.go(""" d """) == [2, 3, 4]

        assert self.go(""" [2, 3] + [4, 5] """) == [2, 3, 4, 5]
        assert self.go(""" [2, 3] * 3 """) == [2, 3, 2, 3, 2, 3]

        self.go(""" e := [1] """)
        with pytest.raises(AssertionError):
            self.go(""" e[None] = 2 """)
        with pytest.raises(AssertionError):
            self.go(""" None[2] = 3 """)

    def test_stdlib(self):
        assert self.go(""" a := range(2, 10, 1) """) == [2, 3, 4, 5, 6, 7, 8, 9]
        assert self.go(""" b := range(2, 10, 3) """) == [2, 5, 8]
        assert self.go(""" first(a) """) == 2
        assert self.go(""" rest(a) """) == [3, 4, 5, 6, 7, 8, 9]
        assert self.go(""" last(a) """) == 9
        assert self.go(""" map(a, n -> n * 2) """) == [4, 6, 8, 10, 12, 14, 16, 18]
        assert self.go(""" filter(a, n -> n % 2 == 0) """) == [2, 4, 6, 8]
        assert self.go(""" reduce(a, add, 0) """) == 44
        assert self.go(""" reverse(a) """) == [9, 8, 7, 6, 5, 4, 3, 2]
        assert self.go(""" zip(a, [4, 5, 6]) """) == [[2, 4], [3, 5], [4, 6]]
        assert self.go(""" enumerate(a) """) == [[0, 2], [1, 3], [2, 4], [3, 5], [4, 6], [5, 7], [6, 8], [7, 9]]

    def test_list_sieve(self):
        assert self.go("""
            sieve := [False, False] + [True] * 98;
            i := 2; while i * i < 100 do
                if sieve[i] then
                    j := i * i; while j < 100 do
                        sieve[j] = False;
                        j = j + i
                    end
                end;
                i = i + 1
            end;

            map(filter(enumerate(sieve), last), first)
        """) == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]

    def test_string(self):
        assert self.go(""" 'Hello, world!' """) == "Hello, world!"
        assert self.go(""" '
multi
line
text
'       """) == "\nmulti\nline\ntext\n"
        assert self.go(""" 'Hello, world!'[1] """) == "e"
        assert self.go(""" 'Hello, ' + 'world!' """) == "Hello, world!"
        assert self.go(""" 'Hello, ' * 3 """) == "Hello, Hello, Hello, "

        assert self.go(""" len('Hello, world!') """) == 13
        assert self.go(""" first('Hello, world!') """) == "H"
        assert self.go(""" rest('Hello, world!') """) == "ello, world!"
        assert self.go(""" last('Hello, world!') """) == "!"

        assert self.go(""" join(['H', 'e', 'l', 'l', 'o'], ' ') """) == "H e l l o"
        assert self.go(""" ord('A') """) == 65
        assert self.go(""" chr(65) """) == "A"

        assert self.go(""" "Hello, world!" """) == "Hello, world!"
        assert self.go(r""" "Hello,\nworld!" """) == "Hello,\nworld!"
        assert self.go(r""" "Hello,\\world!" """) == "Hello,\\world!"
        assert self.go(r""" "Hello,\"world!" """) == 'Hello,"world!'

    def test_destructure_variable_and_literal(self):
        assert self.go(r""" a := 2; a """) == 2
        assert self.go(r""" _ := 2; _ """) == 2

        assert self.go(r""" a := 2; 2 := a """) == 2
        assert self.go(r""" None := None """) is None
        assert self.go(r""" True := True """) is True
        assert self.go(r""" "hello" := "hello" """) == "hello"

        with pytest.raises(AssertionError, match="Pattern mismatch"):
            self.go(r""" "hello" := "world" """)
        with pytest.raises(AssertionError, match="Pattern mismatch"):
            self.go(r""" a := 3; 2 := a """)

    def test_destructure_list(self):
        assert self.go(r""" [a, b] := [3, 4]; [a, b] """) == [3, 4]
        assert self.go(r""" [] := [] """) == []
        assert self.go(r""" [_, b, _] := [2, 3, 4]; b """) == 3

        with pytest.raises(AssertionError, match="Pattern mismatch"):
            self.go(r""" [a, b] := [2] """)
        with pytest.raises(AssertionError, match="Pattern mismatch"):
            self.go(r""" [a, b] := [4, 5, 6] """)
        with pytest.raises(AssertionError, match="Pattern mismatch"):
            self.go(r""" [] := [1] """)
        with pytest.raises(AssertionError, match="Pattern mismatch"):
            self.go(r""" [a] := 2 """)

        assert self.go(r""" [a, *b] := [2]; [a, b] """) == [2, []]
        assert self.go(r""" [a, *b] := [3, 4]; [a, b] """) == [3, [4]]
        assert self.go(r""" [a, *b] := [4, 5, 6]; [a, b] """) == [4, [5, 6]]
        assert self.go(r""" [*a] := [4, 5, 6]; a """) == [4, 5, 6]

        assert self.go(r""" [*a, b] := [2]; [a, b] """) == [[], 2]
        assert self.go(r""" [*a, b] := [2, 3]; [a, b] """) == [[2], 3]
        assert self.go(r""" [*a, b] := [2, 3, 4]; [a, b] """) == [[2, 3], 4]

        assert self.go(r""" [a, *b, c] := [3, 4]; [a, b, c] """) == [3, [], 4]
        assert self.go(r""" [a, *b, c] := [4, 5, 6]; [a, b, c] """) == [4, [5], 6]
        assert self.go(r""" [a, *b, c] := [5, 6, 7, 8]; [a, b, c] """) == [5, [6, 7], 8]

        with pytest.raises(AssertionError, match="Pattern mismatch"):
            self.go(r""" [a, *b] := [] """)
        with pytest.raises(AssertionError, match="Pattern mismatch"):
            self.go(r""" [*a, b] := [] """)
        with pytest.raises(AssertionError, match="Pattern mismatch"):
            self.go(r""" [a, *b, c] := [2] """)
        with pytest.raises(AssertionError, match="Pattern mismatch"):
            self.go(r""" [a, *b, *c, d] := [5, 6, 7, 8] """)

    def test_destructure_dict(self):
        assert self.go(r""" {a} := {a: 2, b: 3}; a """) == 2
        assert self.go(r""" {a, b} := {a: 2, b: 3}; [a, b] """) == [2, 3]
        assert self.go(r""" {a: c, b: d} := {a: 3, b: 4}; [c, d] """) == [3, 4]
        assert self.go(r""" {a} := {"a": 5, b: 6}; a """) == 5
        assert self.go(r""" {a: _, b} := {a: 2, b: 3}; b """) == 3
        assert self.go(r""" {} := {a: 2, b: 3} """) == {'a': 2, 'b': 3}

        assert self.go(r""" {a, *rest} := {a: 2}; [a, rest] """) == [2, {}]
        assert self.go(r""" {a, *rest} := {a: 2, b: 3}; [a, rest] """) == [2, {'b': 3}]
        assert self.go(r""" {a, *rest} := {a: 2, b: 3, c: 4}; [a, rest] """) == [2, {'b': 3, 'c': 4}]

        with pytest.raises(AssertionError, match="Pattern mismatch"):
            self.go(r""" {a} := {b: 2} """)
        with pytest.raises(AssertionError, match="Pattern mismatch"):
            self.go(r""" {a, b, c} := {a: 2, b: 3} """)
        with pytest.raises(AssertionError, match="Pattern mismatch"):
            self.go(r""" {a, *rest} := {b: 2} """)
        with pytest.raises(AssertionError, match="Pattern mismatch"):
            self.go(r""" {a} := 2 """)

    def test_destructure_ident_and_expr(self):
        assert str(self.go(r""" Ident("aaa") := Ident("aaa") """)) == "aaa"
        assert str(self.go(r""" Ident(a) := Ident("aaa"); a """)) == "aaa"

        with pytest.raises(AssertionError, match="Pattern mismatch"):
            self.go(r""" Ident("aaa") := Ident("bbb") """)
        with pytest.raises(AssertionError, match="Pattern mismatch"):
            self.go(r""" Ident(a) := "aaa" """)

        assert self.go(r""" tuple(Ident("add"), [int(a), int(b)]) := quote 2 + 3 end; [a, b] """) == [2, 3]
        assert self.go(r""" tuple(Ident("add"), [Ident(name1), Ident(name2)]) := quote a + b end; [name1, name2] """) == ['a', 'b']

        with pytest.raises(AssertionError, match="Pattern mismatch"):
            self.go(r""" tuple(Ident('add'), [Ident(name1), Ident(name2)]) := quote 2 + 3 end """)
        with pytest.raises(AssertionError, match="Pattern mismatch"):
            self.go(r""" tuple(Ident('add'), [Ident(name1), Ident(name2)]) := tuple(Ident('add')) """)

    def test_destructure_type(self):
        assert self.go(r""" int(a) := 2; a """) == 2
        assert self.go(r""" str(a) := "aaa"; a """) == "aaa"
        with pytest.raises(AssertionError, match="Pattern mismatch"):
            self.go(r""" int(a) := "2" """)
        with pytest.raises(AssertionError, match="Pattern mismatch"):
            self.go(r""" str(a) := [] """)

    def test_destructure_or(self):
        assert self.go(r""" int(a) or str(a) := 2; a """) == 2
        assert self.go(r""" int(a) or str(a) := "aaa"; a """) == "aaa"
        assert self.go(r""" int(a) or str(a) or list(a):= [2]; a """) == [2]
        with pytest.raises(AssertionError, match="Pattern mismatch"):
            self.go(r""" int(a) or str(a) := [2] """)

    def test_destructure_combination(self):
        assert self.go(r""" [{a: b}, c] := [{a: 2, b: 3}, 4]; [b, c] """) == [2, 4]
        assert self.go(r""" {a: [b, c]} := {a: [5, 6]}; [b, c] """) == [5, 6]

    def test_argument_destructuring(self, capsys):
        self.go(""" def f(a, [b, c]) do [a, b, c] end """)
        assert self.go(""" f(2, [3, 4]) """) == [2, 3, 4]

        self.go(""" def g(*a) do a end""")
        assert self.go(""" g() """) == []
        assert self.go(""" g(2 + 3) """) == [5]
        assert self.go(""" g(2, 3, 4) """) == [2, 3, 4]

        self.go(""" def h(a, *b) do [a, b] end """)
        assert self.go(""" h(2 + 3) """) == [5, []]
        assert self.go(""" h(2, 3, 4) """) == [2, [3, 4]]
        with pytest.raises(AssertionError, match="Argument mismatch"):
            self.go(""" h() """)

        assert self.go(r""" func {a: d, *rest}, e do [d, e, rest] end ({a: 2, b: 3, c: 4}, 5) """) == [2, 5, {'b': 3, 'c': 4}]

        self.go(r""" def foo(int(a), str(b)) do [a, b] end """)
        assert self.go(r""" foo(2, "a") """) == [2, "a"]

        with pytest.raises(AssertionError, match="Argument mismatch"):
            self.go(r""" foo(2, 3) """)
        with pytest.raises(AssertionError, match="Argument mismatch"):
            self.go(r""" func a, b do [a, b] end (2) """)
        with pytest.raises(AssertionError, match="Argument mismatch"):
            self.go(r""" func a do a end (2, 3) """)
        with pytest.raises(AssertionError, match="Argument mismatch"):
            self.go(r""" func do 2 end (2) """)

        assert self.go(r""" func do "ok" end () """) == "ok"

    def test_match(self):
        self.go("""
            f := func val do
                match val
                    case 2 then "two"
                    case "two" then 3
                    case [a] then a
                    case [a, 3] then -a
                    case [a, [3, b]] then (a + b) * 2
                    case [a, [b, c]] then a + b + c
                    case [a, b] then a + b
                    case _ then "not match"
                end
            end
        """)
        assert self.go(""" f(2) """) == "two"
        assert self.go(""" f("two") """) == 3
        assert self.go(""" f([2]) """) == 2
        assert self.go(""" f([2, 3]) """) == -2
        assert self.go(""" f([2, [3, 4]]) """) == 12
        assert self.go(""" f([2, [2, 4]]) """) == 8
        assert self.go(""" f([2, 4]) """) == 6
        assert self.go(""" f([2, 3, 4]) """) == "not match"

        with pytest.raises(AssertionError):
            self.go(""" a """)

    def test_match_syntax(self):
        assert self.go(r""" match 2 end """) is None

        with pytest.raises(AssertionError, match="Expected end"):
            self.go(r""" match end """)
        with pytest.raises(AssertionError, match="Expected end"):
            self.go(r""" match 2 case 2 then 3 """)
        with pytest.raises(AssertionError, match="Expected end"):
            self.go(r""" match 2 then 3 end """)
        with pytest.raises(AssertionError, match="Expected then"):
            self.go(r""" match 2 case then 3 end """)

    def test_match_variable_and_literal(self):
        assert self.go(r""" match 2 case a then a + 1 case _ then "no" end """) == 3
        assert self.go(r""" match 2 case 3 then "yes" end """) is None
        assert self.go(r""" match 2 case 2 then "yes" case _ then "no" end """) == "yes"
        assert self.go(r""" match 2 case 3 then "yes" case _ then "no" end """) == "no"
        assert self.go(r""" match [] case 3 then "yes" case _ then "no" end """) == "no"
        assert self.go(r""" match None case None then "yes" case _ then "no" end """) == "yes"
        assert self.go(r""" match 2 case None then "yes" case _ then "no" end """) == "no"
        assert self.go(r""" match True case True then "yes" case _ then "no" end """) == "yes"
        assert self.go(r""" match False case True then "yes" case _ then "no" end """) == "no"
        assert self.go(r""" match False case False then "yes" case _ then "no" end """) == "yes"
        assert self.go(r""" match True case False then "yes" case _ then "no" end """) == "no"
        assert self.go(r""" match "hello" case "hello" then "yes" case _ then "no" end """) == "yes"
        assert self.go(r""" match "world" case "hello" then "yes" case _ then "no" end """) == "no"

    def test_match_list(self):
        assert self.go(r""" match [] case [] then "yes" case _ then "no" end """) == "yes"
        assert self.go(r""" match 2 case [] then "yes" case _ then "no" end """) == "no"
        assert self.go(r""" match [2] case [a] then a + 1 case _ then "no" end """) == 3
        assert self.go(r""" match [2, 3] case [a] then a + 1 case _ then "no" end """) == "no"
        assert self.go(r""" match [2, 3] case [a, b] then a * b case _ then "no" end """) == 6
        assert self.go(r""" match [2] case [a, b] then a * b case _ then "no" end """) == "no"
        assert self.go(r""" match [] case [a, *b] then [a, b] case _ then "no" end """) == "no"
        assert self.go(r""" match [2] case [a, *b] then [a, b] case _ then "no" end """) == [2, []]
        assert self.go(r""" match [3, 4] case [a, *b] then [a, b] case _ then "no" end """) == [3, [4]]
        assert self.go(r""" match [4, 5, 6] case [a, *b] then [a, b] case _ then "no" end """) == [4, [5, 6]]
        assert self.go(r""" match [] case [*a, b] then [a, b] case _ then "no" end """) == "no"
        assert self.go(r""" match [2] case [*a, b] then [a, b] case _ then "no" end """) == [[], 2]
        assert self.go(r""" match [3, 4] case [*a, b] then [a, b] case _ then "no" end """) == [[3], 4]
        assert self.go(r""" match [4, 5, 6] case [*a, b] then [a, b] case _ then "no" end """) == [[4, 5], 6]
        assert self.go(r""" match [2] case [a, *b, c] then [a, b, c] case _ then "no" end """) == "no"
        assert self.go(r""" match [3, 4] case [a, *b, c] then [a, b, c] case _ then "no" end """) == [3, [], 4]
        assert self.go(r""" match [4, 5, 6] case [a, *b, c] then [a, b, c] case _ then "no" end """) == [4, [5], 6]
        assert self.go(r""" match [5, 6, 7, 8] case [a, *b, c] then [a, b, c] case _ then "no" end """) == [5, [6, 7], 8]
        assert self.go(r""" match [2] case [*a, *b] then [a, b] case _ then "no" end """) == "no"

    def test_match_dict_cases(self):
        assert self.go(r""" match {} case {} then "yes" case _ then "no" end """) == "yes"
        assert self.go(r""" match 2 case {} then "yes" case _ then "no" end """) == "no"
        assert self.go(r""" match {a: 2} case {} then "yes" case _ then "no" end """) == "yes"

        assert self.go(r""" match {a: 2} case {a: 2} then "yes" end """) == "yes"
        assert self.go(r""" match {a: 2} case {a: 3} then "yes" end """) is None
        assert self.go(r""" match {a: 2} case {a: a} then a end """) == 2
        assert self.go(r""" match {a: 3} case {a: b} then b end """) == 3
        assert self.go(r""" match {a: 4} case {a} then a end """) == 4
        assert self.go(r""" match {a: 5} case {"a": a} then a end """) == 5
        assert self.go(r""" match {a: 6, b: 7} case {a} then a end """) == 6
        assert self.go(r""" match {a: 7, b: 8} case {a, b} then [a, b] end """) == [7, 8]
        assert self.go(r""" match {a: 8, b: 9} case {a: _, b} then b end """) == 9
        assert self.go(r""" match {a: 2} case {b} then a end """) is None
        assert self.go(r""" match {a: 2} case {a, b} then a end """) is None

        assert self.go(r""" match {a: 2} case {*rest} then rest end """) == {'a': 2}
        assert self.go(r""" match {a: 3} case {a, *rest} then [a, rest] end """) == [3, {}]
        assert self.go(r""" match {a: 3} case {b, *rest} then [b, rest] end """) is None
        assert self.go(r""" match {a: 4, b: 5} case {a, *rest} then [a, rest] end """) == [4, {'b': 5}]
        assert self.go(r""" match {a: 5, b: 6, c: 7} case {a, *rest} then [a, rest] end """) == [5, {'b': 6, 'c': 7}]

    def test_match_ident_and_expr(self):
        assert self.go(r""" match Ident("aaa") case Ident("aaa") then "yes" end """) == "yes"
        assert self.go(r""" match Ident("aaa") case "aaa" then "yes" end """) is None
        assert self.go(r""" match Ident("aaa") case Ident("bbb") then "yes" end """) is None
        assert self.go(r""" match Ident("aaa") case Ident(a) then [a] end """) == ['aaa']

        assert self.go(r""" match quote a + b end case tuple(Ident("add"), [Ident(name1), Ident(name2)]) then [name1, name2] end """) == ["a", "b"]
        assert self.go(r""" match 2 + 3 case tuple(Ident("add"), [Ident(name1), Ident(name2)]) then [name1, name2] end """) is None
        assert self.go(r""" match tuple(Ident("add")) case tuple(Ident("add"), [Ident(name1), Ident(name2)]) then [name1, name2] end """) is None

    def test_match_type_and_or(self):
        assert self.go(r""" match 2 case int(a) then a end """) == 2
        assert self.go(r""" match "2" case int(a) then a end """) is None
        assert self.go(r""" match "aaa" case str(a) then [a] end """) == ['aaa']
        assert self.go(r""" match [] case str(a) then [a] end """) is None

        assert self.go(r""" match 2 case int(a) or str(a) then [a] end """) == [2]
        assert self.go(r""" match "aaa" case int(a) or str(a) then [a] end """) == ['aaa']
        assert self.go(r""" match [2] case int(a) or str(a) then [a] end """) is None
        assert self.go(r""" match [2] case int(a) or str(a) or list(a) then [a] end """) == [[2]]

    def test_match_combination(self):
        assert self.go(r""" match [{a: 2, b: 3}, 4] case  [{a: b}, c] then [b, c] end """) == [2, 4]
        assert self.go(r""" match {a: [5, 6]} case {a: [b, c]} then [b, c] end """) == [5, 6]

    def test_match_control_flow(self):
        assert self.go(r""" a := 0; match 2 case 2 then a = 1 case _ then a = 2 end; a """) == 1
        assert self.go(r""" match [2, 3] case [a, b] then "ok" end; a + b """) == 5
        assert self.go(r""" match [2, 3] case [a, 4] then "no" case _ then a end """) == 2

    def test_match_copy(self):
        assert self.go("""
            a := [2, 3, 4];
            match a
                case b then b[0] = 5
            end;
            a
        """) == [5, 3, 4]

        assert self.go("""
            a := [2, 3, 4];
            match a
                case [*b] then b[0] = 5
            end;
            a
        """) == [2, 3, 4]

    def test_return(self):
        self.go("""
            def f(a) do
                if a == 2 then return(3) end;
                4
            end
        """)
        assert self.go(""" f(2) """) == 3
        assert self.go(""" f(3) """) == 4

        self.go("""
            def fib(n) do
                if n == 0 then return(0) end;
                if n == 1 then return(1) end;
                fib(n - 1) + fib(n - 2)
            end
        """)
        assert self.go(""" fib(0) """) == 0
        assert self.go(""" fib(1) """) == 1
        assert self.go(""" fib(7) """) == 13
        assert self.go(""" fib(9) """) == 34

        with pytest.raises(AssertionError, match="Return takes zero or one argument"):
            self.go(""" func do return(2, 3) end () """)

        with pytest.raises(AssertionError, match="Return from top level"):
            self.go(""" return() """)

    def test_load(self, tmp_path):
        self.go(""" fib := load("lib/fib.toil") """)
        assert self.go(""" fib(9) """) == 34

        self.go(""" [gcd_recur, gcd_iter] := load("lib/gcd.toil") """)
        assert self.go(""" gcd_recur(24, 36) """) == 12
        assert self.go(""" gcd_iter(24, 36) """) == 12

    def test_load_isolation(self, tmp_path):
        mod_a_path = tmp_path / "mod_a.toil"
        mod_a_path.write_text("a_private := 100; func do a_private end")

        self.go(f""" f := load("{mod_a_path}") """)
        assert self.go("f()") == 100
        with pytest.raises(AssertionError, match="Undefined variable"):
            self.go("a_private")

        mod_b_path = tmp_path / "mod_b.toil"
        mod_b_path.write_text("b_private := 200; a_private")
        with pytest.raises(AssertionError, match="Undefined variable"):
            self.go(f""" load("{mod_b_path}") """)

    def test_dict(self):
        assert self.go(""" {} """) == {}
        assert self.go(""" {"aaa": 2} """) == {'aaa': 2}
        self.go(""" bbb := 4 """)
        assert self.go(""" {aaa: 2 + 3, bbb} """) == {'aaa': 5, 'bbb': 4}

        self.go(""" a := {aaa: 2 + 3, bbb} """)
        assert self.go(""" a["aaa"] """) == 5
        assert self.go(""" a["bbb"] """) == 4
        with pytest.raises(KeyError):
            self.go(""" a["ccc"] """)

        self.go(""" a["aaa"] = 2 """)
        assert self.go(""" a """) == {'aaa': 2, 'bbb': 4}
        self.go(""" a["ccc"] = 5 """)
        assert self.go(""" a """) == {'aaa': 2, 'bbb': 4, 'ccc': 5}

        assert self.go(""" len(a) """) == 3
        assert self.go(""" in("aaa", a) """) is True
        assert self.go(""" in("bbb", a) """) is True
        assert self.go(""" in("ddd", a) """) is False
        assert self.go(""" keys(a) """) == ['aaa', 'bbb', 'ccc']
        assert self.go(""" items(a) """) == [['aaa', 2], ['bbb', 4], ['ccc', 5]]

        self.go(""" [k, v] := items(a)[0] """)
        assert self.go(""" k """) == 'aaa'
        assert self.go(""" v """) == 2

        with pytest.raises(AssertionError, match="Invalid key"):
            self.go(""" {1: 2} """)

        with pytest.raises(AssertionError, match="Invalid indexing"):
            self.go(""" a[0] = 1 """)

    def test_dot_notation(self):
        self.go(""" a := {aaa: 2, bbb: 4} """)
        self.go(""" a.aaa = 2 """)
        assert self.go(""" a.aaa """) == 2
        self.go(""" a.ddd = 6 """)
        assert self.go(""" a """) == {'aaa': 2, 'bbb': 4, 'ddd': 6}

        with pytest.raises(AssertionError, match="Invalid attribute"):
            self.go(""" a.1 """)

        with pytest.raises(AssertionError):
            self.go(""" [1, 2].foo """)

    def test_dict_destructuring(self):
        assert self.go("""{a, b} := {a: 2, b: 3}; [a, b] """) == [2, 3]
        assert self.go("""{a, *b} := {a: 2, b: 3, c: 4, d: 5}; [a, b] """) == [2, {'b': 3, 'c': 4, 'd': 5}]
        assert self.go("""{*a, b} := {a: 2, b: 3, c: 4, d: 5}; [a, b] """) == [{'a': 2, 'c': 4, 'd': 5}, 3]
        assert self.go("""{a, *b, c} := {a: 2, b: 3, c: 4, d: 5}; [a, b, c] """) == [2, {'b': 3, 'd': 5}, 4]

    def test_dict_pattern_match(self):
        assert self.go(""" match {a: 2, b: 3} case {a, b} then [a, b] end """) == [2, 3]
        assert self.go(""" match {a: 2, b: 3} case {a: aa, b: bb} then [aa, bb] end """) == [2, 3]
        assert self.go(""" match {a: 2, b: 3, c: 4} case {a, b} then [a, b] end """) == [2, 3]
        assert self.go(""" match {a: 2, b: {c: 3, d: 4}} case {a, b: {c, d}} then [a, c, d] end """) == [2, 3, 4]
        assert self.go(""" match {a: 2, b: [3, 4]} case {a, b: [c, d]} then [a, c, d] end """) == [2, 3, 4]
        assert self.go(""" match {a: 2, b: 3, c: 4} case {a, *rest} then [a, rest] end """) == [2, {'b': 3, 'c': 4}]
        assert self.go(""" match {a: 2, b: 3, c: 4} case {*rest, b} then [rest, b] end """) == [{'a': 2, 'c': 4}, 3]
        assert self.go(""" match {a: 2, b: 3, c: 4} case {a, *rest, c} then [a, rest, c] end """) == [2, {'b': 3}, 4]
        assert self.go(""" match {a: 2} case {b: 3} then 4 end """) is None

    def test_ast_pattern_match(self):
        self.go("""
            f := func ast do
                match ast
                    case tuple(Ident("add"), [left, right]) then left + right
                    case tuple(Ident("sub"), [left, right]) then left - right
                    case tuple(op, args) then [op, args]
                    case _ then None
                end
            end
        """)
        assert self.go(""" f(quote 2 + 3 end) """) == 5
        assert self.go(""" f(quote 5 - 2 end) """) == 3
        assert self.go(""" f(quote 2 * 3 end) """) == [Ident("mul"), [2, 3]]
        assert self.go(""" f(2) """) is None

        assert self.go(""" f(tuple(Ident("add"), [2, 3])) """) == 5
        assert self.go(""" f(tuple("add", [2, 3])) """) == ["add", [2, 3]]
        assert self.go(""" f([Ident("add"), [2, 3]]) """) == None

    def test_dict_module(self):
        self.go(""" gcd := load("lib/gcd_dict.toil") """)
        assert self.go(""" gcd.recur(24, 36) """) == 12
        assert self.go(""" gcd.iter(24, 36) """) == 12

        self.go(""" {recur, iter} := load("lib/gcd_dict.toil") """)
        assert self.go(""" recur(24, 36) """) == 12
        assert self.go(""" iter(24, 36) """) == 12

        self.go(""" {recur: gcd_recur, iter: gcd_iter} := load("lib/gcd_dict.toil") """)
        assert self.go(""" gcd_recur(24, 36) """) == 12
        assert self.go(""" gcd_iter(24, 36) """) == 12

    def test_ufcs(self):
        # Case 1: Namespace
        self.go(""" foo := { add: func a, b do a + b end } """)
        assert self.go(""" foo.add(2, 3) """) == 5

        # Case 2: Method
        self.go(""" foo := { add: func self, a do self.val + a end, val: 2 } """)
        assert self.go(""" foo.add(3) """) == 5

        # Case 3: UFCS
        self.go(""" foo := 2 """)
        assert self.go(""" add(foo, 3) """) == 5
        assert self.go(""" foo.add(3) """) == 5

        self.go(""" myadd := func a, b do a + b end """)
        assert self.go(""" myadd(foo, 3) """) == 5
        assert self.go(""" foo.myadd(3) """) == 5

        # UFCS priority
        self.go(""" d := { len: func self do "local" end } """)
        assert self.go(""" d.len() """) == "local"

        with pytest.raises(AssertionError, match="Invalid operator"):
            self.go(""" d := { val: 123 }; d.val() """)
        with pytest.raises(AssertionError, match="Undefined variable"):
            self.go(""" 2.non_existent() """)

    def test_oo_style(self, capsys):
        self.go("""
            def Animal(name) do
                self := {};
                self._name = name;
                self.introduce = func self do print("I'm", self._name) end;
                self.make_sound = func self do print("crying") end;
                self
            end
        """)
        self.go("""
            animal1 := Animal("Rocky");
            animal2 := Animal("Lucy");
            animal1.introduce();
            animal1.make_sound();
            animal2.introduce();
            animal2.make_sound()
        """)
        assert capsys.readouterr().out == "I'm Rocky\ncrying\nI'm Lucy\ncrying\n"

        self.go("""
            def Dog(name) do
                self := Animal(name);
                self.make_sound = func self do print("woof") end;
                self
            end
        """)
        self.go("""
            dog1 := Dog("Leo");
            dog1.introduce();
            dog1.make_sound()
        """)
        assert capsys.readouterr().out == "I'm Leo\nwoof\n"

    def test_oo_style_with_defclass(self, capsys):
        self.go("""
            defclass Animal(name) do
                self._name = name;
                defmethod introduce do print("I'm", self._name) end;
                defmethod new_name(name) do self._name = name end;
                defmethod make_sound do print("crying") end
            end
        """)
        self.go("""
            animal1 := Animal("Rocky");
            animal2 := Animal("Lucy");
            animal1.introduce();
            animal1.make_sound();
            animal2.introduce();
            animal2.new_name("Bella");
            animal2.introduce();
            animal2.make_sound()
        """)
        assert capsys.readouterr().out == "I'm Rocky\ncrying\nI'm Lucy\nI'm Bella\ncrying\n"

        self.go("""
            defclass Dog(name) do
                inherits(Animal(name));
                defmethod make_sound do print("woof") end
            end
        """)
        self.go("""
            dog1 := Dog("Leo");
            dog1.introduce();
            dog1.make_sound()
        """)
        assert capsys.readouterr().out == "I'm Leo\nwoof\n"

    def test_overload_def(self, capsys):
        self.go("""
            def foo(x) do print("Not supported: " + str(x))  end;
            def foo({kind: "Person", name: str(name)}) do print("Person: " + name) end;
            def foo(str(s)) do print("string: " + s) end;
            def foo(int(n)) do print("int: " + str(n)) end
        """)
        self.go(""" foo(2) """)
        assert capsys.readouterr().out == "int: 2\n"
        self.go(""" foo("bar") """)
        assert capsys.readouterr().out == "string: bar\n"
        self.go(""" foo({kind: "Person", name: "John"}) """)
        assert capsys.readouterr().out == "Person: John\n"
        self.go(""" foo([2]) """)
        assert capsys.readouterr().out == "Not supported: [2]\n"

    def test_overload_arrow_func(self):
        self.go("""
            fib := n -> fib(n - 1) + fib(n - 2);
            fib := 1 -> 1;
            fib := 0 -> 0
        """)
        assert self.go(""" fib(0) """) == 0
        assert self.go(""" fib(1) """) == 1
        assert self.go(""" fib(4) """) == 3

    def test_defmethod_overloading(self):
        self.go("""
            defclass Accumulator do
                self.total = 0;
                defmethod add(int(n)) do self.total = self.total + n end;
                defmethod add(list(arr)) do
                    for n in arr do self.add(n) end
                end;
                defmethod add(str(s)) do self.add(int(s)) end
            end;
            acc := Accumulator();
            acc.add(10); acc.add([20, 30]); acc.add("40")
        """)
        assert self.go(""" acc.total """) == 100

    def test_sieve_ufcs(self):
        result = self.go("""
            sieve := [False, False] + [True] * 98;
            i := 2; while i * i < 100 do
                if sieve[i] then
                    j := i * i; while j < 100 do
                        sieve[j] = False;
                        j = j + i
                    end
                end;
                i = i + 1
            end;
            sieve.enumerate().filter(last).map(first)
        """)
        assert result == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]

    def test_test_framework(self, capsys):
        self.go("""
            def Test(name) do
                self := { name, failed: 0 };
                self.assert = func self, cond, msg do
                    if not cond then
                        print("FAIL:", self.name, ":", msg);
                        self.failed = self.failed + 1
                    end;
                    self
                end;
                self.report = func self do
                    if self.failed == 0 then print("PASS:", self.name)
                    else print("FAILED:", self.name, "(", self.failed, "errors )") end
                end;
                self
            end;

            t := Test("Math");
            t.assert(2 + 2 == 4, "2+2 should be 4")
             .assert(3 * 3 == 9, "3*3 should be 9")
             .assert(1 > 2, "1 should be greater than 2")
             .report()
        """)
        assert capsys.readouterr().out == "FAIL: Math : 1 should be greater than 2\nFAILED: Math ( 1 errors )\n"

    def test_try_except(self, capsys):
        # try without except
        assert self.go(""" try 2; 3 end """) == 3
        self.go(""" try print(2); print(3) end """)
        assert capsys.readouterr().out == "2\n3\n"

        # try with except, no raise
        assert self.go(""" try 2; 3 except e then print(e) end """) == 3
        self.go(""" try print(2); print(3) except e then print(e) end """)
        assert capsys.readouterr().out == "2\n3\n"

        # try with raise and catch
        self.go(""" try print(2); raise(2 + 3); print(3) except e then print(e) end """)
        assert capsys.readouterr().out == "2\n5\n"
        assert self.go(""" try 2; raise(2 + 3); 3 except e then e end """) == 5

        # pattern match in except
        self.go("""
            try
                print(2); raise(["foo", 3]); print(4)
            except ["foo", val] then print("foo", val)
            except ["bar", val] then print("bar", val)
            end
        """)
        assert capsys.readouterr().out == "2\nfoo 3\n"

        self.go("""
            try
                print(2); raise(["bar", 3]); print(4)
            except ["foo", val] then print("foo", val)
            except ["bar", val] then print("bar", val)
            end
        """)
        assert capsys.readouterr().out == "2\nbar 3\n"

        # unhandled exception
        with pytest.raises(AssertionError, match="ToilException"):
            self.go("""
                try
                    raise(["baz", 3])
                except ["foo", val] then print("foo", val)
                end
            """)

        # nested try
        self.go("""
            try
                try
                    raise("outer")
                except "inner" then print("caught inner")
                end
            except "outer" then print("caught outer")
            end
        """)
        assert capsys.readouterr().out == "caught outer\n"

    def test_eval_apply(self, capsys):
        # apply
        assert self.go(""" apply(add, [2, 3]) """) == 5
        assert self.go(""" apply(func a, b do a + b end, [2, 3]) """) == 5

        # eval
        self.go(""" a := 2; b := 3 """)
        assert self.go(""" eval("a + b") """) == 5
        assert self.go(""" scope a := 4; b := 5; eval("a + b") end """) == 5
        assert self.go(""" scope a := 4; b := 5; eval("a + b", __env) end """) == 9
        assert self.go(""" scope a := 4; b := 5; eval_expr(quote a + b end, __env) end """) == 9

        # Poor man's serialization
        self.go("""
            org := { name: "Toil", id: 1 };
            print(org);
            serialized := str(org);
            print(serialized);
            deserialized := eval(serialized);
            print(deserialized)
        """)
        assert capsys.readouterr().out == "{'name': 'Toil', 'id': 1}\n{'name': 'Toil', 'id': 1}\n{'name': 'Toil', 'id': 1}\n"

        # Poor man's syntax sugar
        assert self.go("""
            def mydef(name, params_, body) do
                eval("def " + name + "(" + params_ + ") do " + body + " end")
            end;
            mydef("myadd", "a, b", "a + b");
            myadd(2, 3)
        """) == 5

    def test_type(self):
        assert self.go(""" type(None) """) == "NoneType"
        assert self.go(""" type(True) """) == "bool"
        assert self.go(""" type(2) """) == "int"
        assert self.go(""" type("abc") """) == "str"
        assert self.go(""" type([2, 3]) """) == "list"
        assert self.go(""" type({a: 2}) """) == "dict"
        assert self.go(""" type(quote 2 + 3 end) """) == "tuple"
        assert self.go(""" type(quote a end) """) == "Ident"

    def test_gensym(self):
        g1 = self.go(""" gensym("foo") """)
        g2 = self.go(""" gensym("foo") """)
        assert type(g1) is Ident
        assert g1.name.startswith("__foo_")
        assert g1 != g2

    def test_env_exposure(self):
        self.go(""" a := 2 """)
        assert self.go(""" __env.vars.keys() """) == ["a"]
        assert self.go(""" __env.vars.items() """) == [["a", 2]]
        assert self.go(""" __env.val("a") """) == 2

        assert self.go(""" __env.define("b", 3) """) == 3
        assert self.go(""" __env.vars.keys() """) == ["a", "b"]
        assert self.go(""" b """) == 3

        assert self.go(""" scope c := 4; __env.vars.keys() end """) == ["c"]
        assert self.go(""" scope c := 4; __env.parent.vars.keys() end """) == ["a", "b"]
        assert self.go(""" scope a := 5; __env.parent.val("a") end """) == 2

        self.go(""" scope __env.assign("b", 6) end """)
        assert self.go(""" b """) == 6

        assert self.go(""" __env.lookup("add") != None """) is True
        assert self.go(""" __env.lookup("add").add(2, 3) """) == 5

        # Error cases
        with pytest.raises(AssertionError, match="Undefined variable"):
            self.go(""" __env.val("not_found") """)

        with pytest.raises(AssertionError, match="Undefined variable"):
            self.go(""" __env.assign("not_found", 100) """)

        # lookup not found returns None
        assert self.go(""" __env.lookup("not_found") """) is None

        # Trace parents to None
        assert self.go(""" __env.parent.parent.parent.parent """) is None

    def test_ast_primitives(self):
        assert self.go(""" quote if True then 2 else 3 end end """) == (Ident("__core_if_macro"), [True, 2, [], [3]])
        assert self.go(""" tuple(Ident("__core_if"), [True, 2, 3]) """) == (Ident("__core_if"), [True, 2, 3])
        assert self.go(""" eval_expr(tuple(Ident("__core_if"), [True, 2, 3])) """) == 2
        assert self.go(""" eval_expr(tuple(Ident("__core_if_macro"), [True, 2, [], [3]])) """) == 2

        with pytest.raises(AssertionError):
            self.go(""" eval_expr(tuple(Ident("if"), [True, 2, 3] """)

        assert self.go(""" quote add(2, 3) end """) == (Ident("add"), [2, 3])
        assert self.go(""" tuple(Ident("add"), [2, 3]) """) == (Ident("add"), [2, 3])
        assert self.go(""" eval_expr(tuple(Ident("add"), [2, 3])) """) == 5

        assert self.go(""" quote
            a := 2;
            b := 3;
            if a == b then a + b else a * b end
        end """) == (Ident("seq"), [(Ident("define"), [Ident("a"), 2]), (Ident("define"), [Ident("b"), 3]), (Ident("__core_if_macro"), [(Ident("equal"), [Ident("a"), Ident("b")]), (Ident("add"), [Ident("a"), Ident("b")]), [], [(Ident("mul"), [Ident("a"), Ident("b")])]])])
        assert self.go("""
            tuple(Ident("seq"), [
                tuple(Ident("define"), [Ident("a"), 2]),
                tuple(Ident("define"), [Ident("b"), 3]),
                tuple(Ident("__core_if"), [
                    tuple(Ident("equal"), [Ident("a"), Ident("b")]),
                    tuple(Ident("add"), [Ident("a"), Ident("b")]),
                    tuple(Ident("mul"), [Ident("a"), Ident("b")])
                ])
            ])
        """) == (Ident("seq"), [
            (Ident("define"), [Ident("a"), 2]),
            (Ident("define"), [Ident("b"), 3]),
            (Ident("__core_if"), [
                (Ident("equal"), [Ident("a"), Ident("b")]),
                (Ident("add"), [Ident("a"), Ident("b")]),
                (Ident("mul"), [Ident("a"), Ident("b")])
            ])
        ])
        assert self.go(""" eval_expr(
            tuple(Ident("seq"), [
                tuple(Ident("define"), [Ident("a"), 2]),
                tuple(Ident("define"), [Ident("b"), 3]),
                tuple(Ident("__core_if"), [
                    tuple(Ident("equal"), [Ident("a"), Ident("b")]),
                    tuple(Ident("add"), [Ident("a"), Ident("b")]),
                    tuple(Ident("mul"), [Ident("a"), Ident("b")])
                ])
            ])
        ) """) == 6

    def test_macro(self, capsys):
        # Basic macro (when) vs function (fwhen)
        self.go("""
            defmacro when(cond, body) do tuple(Ident("__core_if"), [cond, body, None]) end;
            def fwhen(cond, body) do if cond then body else None end end
        """)
        assert self.go(""" expand(when(2 == 2, 3)) """) == (Ident("__core_if"), [(Ident("equal"), [2, 2]), 3, None])
        assert self.go(""" when(2 == 2, 3) """) == 3
        assert self.go(""" when(2 == 3, 4 / 0) """) is None

        assert self.go(""" fwhen(2 == 2, 3) """) == 3
        with pytest.raises(ZeroDivisionError):
            self.go(""" fwhen(2 == 3, 4 / 0) """)

        self.go(""" defmacro mwhen(cond, body) do tuple(Ident("__core_if"), [cond, body, None]) end """)
        assert self.go(""" mwhen(2 == 2, 3) """) == 3
        with pytest.raises(AssertionError, match="Argument mismatch"):
            self.go(""" mwhen(2 == 2) """)

        # Macro for scope
        self.go("""
            defmacro mscope(body) do tuple(tuple(Ident("__core_func"), [[], body]), []) end
        """)
        self.go(""" a := 2; mscope(print(a); a := 3; print(a)); print(a) """)
        assert capsys.readouterr().out == "2\n3\n2\n"

        # Anaphoric if
        self.go("""
            defmacro maif(cnd, thn, els) do tuple(Ident("__core_scope"), [tuple(Ident("__core_if"), [
                tuple(Ident("define"), [Ident("it"), cnd]),
                thn,
                els
            ])]) end
        """)
        assert self.go(""" maif(2, [True, it], [False, it]) """) == [True, 2]
        assert self.go(""" maif(0, [True, it], [False, it]) """) == [False, 0]

        # and/or using aif
        self.go("""
            defmacro mand(a, b) do tuple(Ident("maif"), [a, b, Ident("it")]) end;
            defmacro mor(a, b) do tuple(Ident("maif"), [a, Ident("it"), b]) end
        """)
        assert self.go(""" mand(2, 3) """) == 3
        assert self.go(""" mand(0, 3) """) == 0
        assert self.go(""" mor(2, 3) """) == 2
        assert self.go(""" mor(0, 3) """) == 3

        # Side effect in macro argument
        self.go("""
            def ftwice(x) do x + x end;
            defmacro mtwice(x) do tuple(Ident("add"), [x, x]) end
        """)
        self.go(""" cnt := 0 """)
        assert self.go(""" ftwice(cnt = cnt + 1) """) == 2
        assert self.go(""" cnt """) == 1

        self.go(""" cnt := 0 """)
        assert self.go(""" mtwice(cnt = cnt + 1) """) == 3
        assert self.go(""" cnt """) == 2

        # Variable capture (Non-hygienic)
        self.go(""" defmacro capture(val) do tuple(Ident("define"), [Ident("x"), val]) end """)
        self.go(""" x := 1 """)
        self.go(""" capture(2) """)
        assert self.go(""" x """) == 2

class TestQuasiquote(TestBase):
    def test_basic(self):
        self.go(""" a := 2; b := ["A", "B"] """)
        assert self.go(""" quote 3 end """) == 3
        assert self.go(""" quote "A" end """) == "A"
        assert self.go(""" quote a end """) == Ident("a")
        assert self.go(""" quote !a end """) == 2
        assert self.go(""" quote !a + 2 end """) == (Ident("add"), [2, 2])
        assert self.go(""" quote !(a + 2) end """) == 4

    def test_list(self):
        self.go(""" a := 2; b := ["A", "B"] """)
        assert self.go(""" quote [a, b] end """) == [Ident("a"), Ident("b")]
        assert self.go(""" quote [!a, !b] end """) == [2, ["A", "B"]]

    def test_splicing(self):
        self.go(""" a := 2; b := ["A", "B"] """)
        assert self.go(""" quote [!!b] end """) == ["A", "B"]
        assert self.go(""" quote [a, !!b, 2] end """) == [Ident("a"), "A", "B", 2]

    def test_nested(self):
        self.go(""" a := 2 """)
        assert self.go(""" quote if !a == 3 then 4 else 5 end end """) == (Ident("__core_if_macro"), [(Ident("equal"), [2, 3]), 4, [], [5]])
        assert self.go(""" eval_expr(quote if !a == 3 then 4 else 5 end end) """) == 5

    def test_splicing_call(self, capsys):
        self.go(""" args := [2, 3] """)
        assert self.go(""" quote print(1, !!args, 4) end """) == (Ident("print"), [1, 2, 3, 4])
        self.go(""" eval_expr(quote print(1, !!args, 4) end) """)
        assert capsys.readouterr().out == "1 2 3 4\n"

    def test_splicing_seq(self, capsys):
        self.go(""" stmts := [quote print(2) end, quote print(3) end] """)
        seq_ast = self.go(""" quote print(1); !!stmts; print(4) end """)
        self.go(""" eval_expr(quote print(1); !!stmts; print(4) end) """)
        assert capsys.readouterr().out == "1\n2\n3\n4\n"

    def test_errors(self):
        with pytest.raises(AssertionError, match="Undefined variable"):
            self.go(""" quote !c end """)
        with pytest.raises(AssertionError):
            self.go(""" quote if end """)

class TestMacroSamples(TestBase):
    def test_when(self):
        self.go("""
            when := macro cond, body do quote if !cond then !body else None end end end
        """)
        assert self.go(""" expand(when(2 == 2, 3)) """) == (Ident("__core_if_macro"), [(Ident("equal"), [2, 2]), 3, [], [None]])
        assert self.go(""" when(2 == 2, 3) """) == 3
        assert self.go(""" when(2 == 3, 4 / 0) """) is None

    def test_fwhen_error(self):
        self.go("""
            fwhen := func cond, body do if cond then body else None end end
        """)
        assert self.go(""" fwhen(2 == 2, 3) """) == 3
        with pytest.raises(ZeroDivisionError):
            self.go(""" fwhen(2 == 3, 4 / 0) """)

    def test_mscope(self, capsys):
        self.go(""" mscope := macro body do quote func do !body end () end end """)
        self.go(""" a := 2; mscope(print(a); a := 3; print(a)); print(a) """)
        assert capsys.readouterr().out == "2\n3\n2\n"

    def test_anaphoric_if_and_or(self):
        self.go("""
            maif := macro cnd, thn, els do
                quote if it := !cnd then !thn else !els end end
            end
        """)
        assert self.go(""" maif(2, [True, it], [False, it]) """) == [True, 2]
        assert self.go(""" maif(0, [True, it], [False, it]) """) == [False, 0]

        self.go(""" mand := macro a, b do quote maif(!a, !b, it) end end """)
        self.go(""" mor := macro a, b do quote maif(!a, it, !b) end end """)

        assert self.go(""" mand(2, 3) """) == 3
        assert self.go(""" mand(0, 3) """) == 0
        assert self.go(""" mor(2, 3) """) == 2
        assert self.go(""" mor(0, 3) """) == 3

        with pytest.raises(AssertionError, match="Undefined variable"):
             self.go(""" expand(expand(mand(2, 3))) """)

    def test_side_effect_macro(self):
        self.go("""
            def ftwice(x) do x + x end;
            mtwice := macro x do quote add(!x, !x) end end
        """)
        self.go(""" cnt := 0 """)
        assert self.go(""" ftwice(cnt = cnt + 1) """) == 2
        assert self.go(""" cnt """) == 1
        self.go(""" cnt := 0 """)
        assert self.go(""" mtwice(cnt = cnt + 1) """) == 3
        assert self.go(""" cnt """) == 2

    def test_capture(self):
        self.go(""" capture := macro val do quote x := !val end end """)
        self.go(""" x := 1 """)
        self.go(""" capture(2) """)
        assert self.go(""" x """) == 2

    def test_call_by_name(self):
        self.go("""
            call_by_name := macro name_str, *args do
                quote (!Ident(quote !name_str end))(!!args) end
            end
        """)
        assert self.go(""" call_by_name("add", 2, 3) """) == 5
        assert self.go(""" call_by_name("sub", 10, 4) """) == 6

    def test_lazy_evaluation(self):
        assert self.go("""
            defmacro delay(expr) do quote func do !expr end end end;
            def force(thunk) do thunk() end;

            defmacro cons_stream(a, b) do quote tuple(!a, delay(!b)) end end;
            def stream_car(s) do s[0] end;
            def stream_cdr(s) do force(s[1]) end;

            def take(n, s) do
                if n == 0 then
                    []
                else
                    [stream_car(s)] + take(n - 1, stream_cdr(s))
                end
            end;

            def count_from(n) do
                cons_stream(n, count_from(n + 1))
            end;

            take(5, count_from(1))
        """) == [1, 2, 3, 4, 5]

class TestCustomSyntax(TestBase):
    def test_when(self):
        self.go("""
            _when := macro cond, body do quote if !cond then !body else None end end end
            #rule {when: [_when, EXPR, do, EXPR, end]}
        """)
        assert self.go(""" expand(_when(2 == 2, 3)) """) == (Ident("__core_if_macro"), [(Ident("equal"), [2, 2]), 3, [], [None]])
        assert self.go(""" _when(2 == 2, 3) """) == 3
        assert self.go(""" _when(2 == 3, 4 / 0) """) is None

        assert self.go(""" expand(when 2 == 2 do 3 end ) """) == (Ident("__core_if_macro"), [(Ident("equal"), [2, 2]), 3, [], [None]])
        assert self.go(""" when 2 == 2 do 3 end """) == 3
        assert self.go(""" when 2 == 3 do 4 / 0 end """) is None

        with pytest.raises(AssertionError):
            self.go(""" when do 4 end """)
        with pytest.raises(AssertionError):
            self.go(""" when 2 == 3 4 end """)
        with pytest.raises(AssertionError):
            self.go(""" when 2 == 3 do end """)
        with pytest.raises(AssertionError):
            self.go(""" when 2 == 3 do 4 """)

    def test_mfor(self):
        self.go("""
            _mfor := macro var, coll, body do quote scope
                __for_coll := !coll;
                __for_index := -1;
                while __for_index + 1 < len(__for_coll) do
                    __for_index = __for_index + 1;
                    scope
                        !var := __for_coll[__for_index];
                        !body
                    end
                end
            end end end
            #rule {mfor: [_mfor, EXPR, in, EXPR, do, EXPR, end]}
        """)
        assert self.go("""
            sum := 0;
            mfor n in [2, 3, 4] do sum = sum + n end;
            sum
        """) == 9

    def test_aif_and_or(self):
        self.go("""
            _aif := macro cnd, thn, els do quote if it := !cnd then !thn else !els end end end
            #rule {aif: [_aif, EXPR, then, EXPR, else, EXPR, end]}
        """)
        assert self.go(""" aif 2 then [True, it] else [False, it] end """) == [True, 2]
        assert self.go(""" aif 0 then [True, it] else [False, it] end """) == [False, 0]

        self.go("""
            mand := macro a, b do quote aif !a then !b else it end end end;
            mor := macro a, b do quote aif !a then it else !b end end end
        """)
        assert self.go(""" mand(2, 3) """) == 3
        assert self.go(""" mand(0, 3) """) == 0
        assert self.go(""" mor(2, 3) """) == 2
        assert self.go(""" mor(0, 3) """) == 3

        # Test short-circuiting
        assert self.go(""" mand(0, 2 / 0) """) == 0
        assert self.go(""" mor(2, 2 / 0) """) == 2
        with pytest.raises(ZeroDivisionError): self.go(""" mand(2, 2/0) """)
        with pytest.raises(ZeroDivisionError): self.go(""" mor(0, 2/0) """)

    def test_def(self):
        self.go(r"""
            def say_hello do "hello" end
        """)
        assert self.go(r""" say_hello() """) == "hello"

        self.go(r"""
            def fact(n) do n * fact(n - 1) end;
            def fact(0) do 1 end
        """)
        assert self.go(r""" fact(0) """) == 1
        assert self.go(r""" fact(3) """) == 6

        with pytest.raises(AssertionError, match="Invalid def syntax"):
            self.go(r""" def 2 do 3 end """)

    def test_defmacro(self):
        self.go(r"""
            defmacro mwhen(cond, body) do
                quote if !cond then !body else None end end
            end
        """)
        assert self.go(r""" expand(mwhen(2 == 2, 3)) """) == (Ident("__core_if_macro"), [(Ident("equal"), [2, 2]), 3, [], [None]])
        assert self.go(r""" mwhen(2 == 2, 3) """) == 3
        assert self.go(r""" mwhen(2 == 3, 4 / 0) """) is None

        self.go(r""" defmacro mzero() do quote 2 end end """)
        assert self.go(r""" mzero() """) == 2

        self.go(r""" defmacro mzero_no_paren do quote 3 end end """)
        assert self.go(r""" mzero_no_paren() """) == 3

        with pytest.raises(AssertionError, match="Argument mismatch"):
            self.go(""" mwhen(2 == 2) """)
        with pytest.raises(AssertionError, match="Invalid defmacro syntax"):
            self.go(r""" defmacro 2 do 3 end """)

    def test_defclass_defmethod(self):
        self.go(r"""
            defclass Counter(start) do
                self.count = start;
                defmethod inc(step) do
                    self.count = self.count + step
                end;
                defmethod get do
                    self.count
                end
            end
        """)
        assert self.go(""" c := Counter(10); c.inc(2); c.get() """) == 12

        with pytest.raises(AssertionError, match="Invalid defclass syntax"):
            self.go(r""" defclass 2 do 3 end """)
        with pytest.raises(AssertionError, match="Invalid defmethod syntax"):
            self.go(r""" defclass ErrCounter() do defmethod 2 do 3 end end; ErrCounter() """)

    def test_let_custom_rule(self):
        # Setup for let_func and let_scope
        self.go("""
            _let_func := macro bindings, body do quote
                func !!map(bindings, pair -> pair[0]) do
                    !body
                end (!!map(bindings, pair -> pair[1]))
            end end;
            #rule {let_func: [_let_func, *[var, EXPR, be, EXPR], do, EXPR, end]}

            _let_scope := macro bindings, body do quote
                scope
                    !!map(bindings, binding -> quote !binding[0] := !binding[1] end);
                    !body
                end
            end end
            #rule {let_scope: [_let_scope, *[var, EXPR, be, EXPR], do, EXPR, end]}
        """)

        # let_func tests (parallel binding)
        assert self.go(""" expand(let_func var a be 4 + 5 var b be 6 do [a, b] end) """) == \
                ((Ident("__core_func"), [
                   [Ident("a"), Ident("b")],
                   [Ident("a"), Ident("b")]]
                ), [(Ident("add"), [4, 5]), 6])

        self.go(""" a := 2 """)
        # 'b' is bound to the outer 'a' (2), demonstrating parallel binding
        assert self.go(""" let_func var a be 3 var b be a + 4 do [a, b] end """) == [3, 6]
        assert self.go(""" a """) == 2 # Outer scope is not affected

        # let_func with zero and one binding
        assert self.go(""" let_func do 2 end """) == 2
        assert self.go(""" let_func var a be 2 do a * 3 end """) == 6

        # let_func nested
        assert self.go(""" let_func var a be 2 do let_func var b be 3 do a + b end end """) == 5

        # let_scope tests (sequential binding)
        assert self.go(""" expand(let_scope var a be 4 + 5 var b be a + 6 do [a, b] end) """) == \
               (Ident('__core_scope'), [(Ident('seq'), [(Ident('define'), [Ident('a'), (Ident('add'), [4, 5])]), (Ident('define'), [Ident('b'), (Ident('add'), [Ident('a'), 6])]), [Ident('a'), Ident('b')]])])

        self.go(""" a := 2 """)
        # 'b' is bound to the inner 'a' (9), demonstrating sequential binding
        assert self.go(""" let_scope var a be 4 + 5 var b be a + 6 do [a, b] end """) == [9, 15]
        assert self.go(""" a """) == 2 # Outer scope is not affected

        # Error cases for custom rule with repetition
        with pytest.raises(AssertionError, match="Expected be @ consume: do"):
            self.go(""" let_func var a be 1 var b do a end """)

        with pytest.raises(AssertionError, match="Expected be @ consume: do"):
            self.go(""" let_func var a = 1 do a end """)

    def test_optional_arguments(self):
        self.go("""
            #rule {foo: [_foo, +[opt, EXPR], do, EXPR, end]}
            None
        """)

        assert self.ast(""" foo do 4 end """) == (Ident("_foo"), [[], 4])
        assert self.ast(""" foo opt 2 + 3 do 4 end """) == (Ident("_foo"), [[(Ident("add"), [2, 3])], 4])
        with pytest.raises(AssertionError, match="Expected do @ consume: opt"):
            self.ast(""" foo opt 2 + 3 opt 4 + 5 do 6 end """)

    def test_elif(self):
        assert self.ast(""" if 2 == 3 then 4 end """) == (Ident("__core_if_macro"), [(Ident("equal"), [2, 3]), 4, [], []])
        assert self.ast(""" if 2 == 3 then 4 else 5 end """) == (Ident("__core_if_macro"), [(Ident("equal"), [2, 3]), 4, [], [5]])
        assert self.ast(""" if 2 == 3 then 4 elif 2 == 2 then 5 end """) == (Ident("__core_if_macro"), [(Ident("equal"), [2, 3]), 4, [[(Ident("equal"), [2, 2]), 5]], []])
        assert self.ast(""" if 2 == 3 then 4 elif 2 == 2 then 5 else 6 end """) == (Ident("__core_if_macro"), [(Ident("equal"), [2, 3]), 4, [[(Ident("equal"), [2, 2]), 5]], [6]])
        assert self.ast(""" if 2 == 3 then 4 elif 3 == 4 then 5 elif 2 == 2 then 6 end """) == (Ident("__core_if_macro"), [(Ident("equal"), [2, 3]), 4, [[(Ident("equal"), [3, 4]), 5], [(Ident("equal"), [2, 2]), 6]], []])
        assert self.ast(""" if 2 == 3 then 4 elif 3 == 4 then 5 elif 2 == 2 then 6 else 7 end """) == (Ident("__core_if_macro"), [(Ident("equal"), [2, 3]), 4, [[(Ident("equal"), [3, 4]), 5], [(Ident("equal"), [2, 2]), 6]], [7]])

        assert self.go(""" expand(if 2 == 3 then 4 end) """) == (Ident("__core_if"), [(Ident("equal"), [2, 3]), 4, None])
        assert self.go(""" expand(if 2 == 3 then 4 else 5 end) """) == (Ident("__core_if"), [(Ident("equal"), [2, 3]), 4, 5])
        assert self.go(""" expand(if 2 == 3 then 4 elif 2 == 2 then 5 end) """) == (Ident("__core_if"), [(Ident("equal"), [2, 3]), 4, (Ident("__core_if"), [(Ident("equal"), [2, 2]), 5, None])])
        assert self.go(""" expand(if 2 == 3 then 4 elif 2 == 2 then 5 else 6 end) """) == (Ident("__core_if"), [(Ident("equal"), [2, 3]), 4, (Ident("__core_if"), [(Ident("equal"), [2, 2]), 5, 6])])
        assert self.go(""" expand(if 2 == 3 then 4 elif 3 == 4 then 5 elif 2 == 2 then 6 end) """) == (Ident("__core_if"), [(Ident("equal"), [2, 3]), 4, (Ident("__core_if"), [(Ident("equal"), [3, 4]), 5, (Ident("__core_if"), [(Ident("equal"), [2, 2]), 6, None])])])
        assert self.go(""" expand(if 2 == 3 then 4 elif 3 == 4 then 5 elif 2 == 2 then 6 else 7 end) """) == (Ident("__core_if"), [(Ident("equal"), [2, 3]), 4, (Ident("__core_if"), [(Ident("equal"), [3, 4]), 5, (Ident("__core_if"), [(Ident("equal"), [2, 2]), 6, 7])])])

        # Test mif evaluation
        assert self.go(""" if 2 == 3 then 4 end """) is None
        assert self.go(""" if 2 == 3 then 4 else 5 end """) == 5
        assert self.go(""" if 2 == 3 then 4 elif 2 == 2 then 5 end """) == 5
        assert self.go(""" if 2 == 3 then 4 elif 2 == 2 then 5 else 6 end """) == 5
        assert self.go(""" if 2 == 3 then 4 elif 3 == 4 then 5 elif 2 == 2 then 6 end """) == 6
        assert self.go(""" if 2 == 3 then 4 elif 3 == 4 then 5 elif 2 == 2 then 6 else 7 end """) == 6

        # Test mif error cases
        with pytest.raises(AssertionError, match="Expected then @ consume: 4"):
            self.ast(""" if then 4 end """)
        with pytest.raises(AssertionError, match="Expected then @ consume: 4"):
            self.ast(""" if 2 == 3 4 end """)
        with pytest.raises(AssertionError, match="Expected end @ consume"):
            self.ast(""" if 2 == 3 then 4 else end """)
        with pytest.raises(AssertionError, match="Expected end @ consume: else"):
            self.ast(""" if 2 == 3 then 4 else 5 else 6 end """)

    def test_module(self):
        self.go("""
            defmodule Mod1 export {public_val, public_func} do
                public_val := 2;
                _private_val := 3;

                def public_func(a) do a + 2 end;
                def _private_func(a) do a end
            end
        """)

        self.go(""" import Mod1 as mod1 end """)
        assert self.go(""" mod1.public_val """) == 2
        assert self.go(""" mod1.public_func(3) """) == 5

        with pytest.raises(AssertionError, match="Undefined variable"):
            self.go(""" mod1._private_val """)
        with pytest.raises(AssertionError, match="Undefined variable"):
            self.go(""" mod1._private_func() """)

        self.go(""" from Mod1 import {public_val} end """)
        assert self.go(""" public_val """) == 2

        self.go(""" from Mod1 import {public_func: f} end """)
        assert self.go(""" f(0) """) == 2

        with pytest.raises(AssertionError, match="Pattern mismatch"):
            self.go(""" from Mod1 import {not_found} end """)

        self.go("""
            defmodule Mod2 export {mod1, public_val} do
                import Mod1 as mod1 end;
                public_val := mod1.public_func(3)
            end
        """)

        self.go(""" import Mod2 as mod2 end """)
        assert self.go(""" mod2.mod1.public_val """) == 2
        assert self.go(""" mod2.public_val """) == 5

        self.go("""
            defmodule GCD export {recur, iter} do
                def recur(a, b) do
                    if a == 0 then b else recur(b % a, a) end
                end;
                def iter(a, b) do
                    while a != 0 do [a, b] := [b % a, a] end;
                    b
                end
            end
        """)
        self.go(""" import GCD as gcd end """)
        assert self.go(""" gcd.recur(18, 24) """) == 6
        assert self.go(""" gcd.iter(18, 24) """) == 6

if __name__ == "__main__":
    pytest.main([__file__])
