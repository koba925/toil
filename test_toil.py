import pytest
from toil import Interpreter, Ident


class TestBase:
    @pytest.fixture(autouse=True)
    def set_interpreter(self):
        self.i = Interpreter().init_env().stdlib()


class TestScan(TestBase):
    def test_number(self):
        assert self.i.scan("""2""") == [2, Ident("$EOF")]
        assert self.i.scan(""" 3 """) == [3, Ident("$EOF")]
        assert self.i.scan(""" \t4\n5\n """) == [4, 5, Ident("$EOF")]
        assert self.i.scan("""  """) == [Ident("$EOF")]

    def test_operator(self):
        assert self.i.scan(""" 1 + 2 """) == [1, Ident("+"), 2, Ident("$EOF")]
        assert self.i.scan(""" 1 * 2 """) == [1, Ident("*"), 2, Ident("$EOF")]
        assert self.i.scan(""" 1 / 2 """) == [1, Ident("/"), 2, Ident("$EOF")]

    def test_bool_none_ident(self):
        assert self.i.scan(""" True """) == [True, Ident("$EOF")]
        assert self.i.scan(""" False """) == [False, Ident("$EOF")]
        assert self.i.scan(""" None """) == [None, Ident("$EOF")]
        assert self.i.scan(""" a """) == [Ident("a"), Ident("$EOF")]

    def test_define_assign(self):
        assert self.i.scan(""" a := 2 """) == [Ident("a"), Ident(":="), 2, Ident("$EOF")]
        assert self.i.scan(""" a = 2 """) == [Ident("a"), Ident("="), 2, Ident("$EOF")]

    def test_string(self):
        assert self.i.scan(""" 'hello' """) == ["hello", Ident("$EOF")]
        assert self.i.scan(""" "hello" """) == ["hello", Ident("$EOF")]
        assert self.i.scan(r""" "a\nb" """) == ["a\nb", Ident("$EOF")]

class TestParse(TestBase):
    def test_comparison(self):
        assert self.i.ast(""" 2 == 3 == 4 """) == (
            Ident("equal"), [(Ident("equal"), [2, 3]), 4]
        )

    def test_add_sub(self):
        assert self.i.ast(""" 2 + 3 """) == (Ident("add"), [2, 3])
        assert self.i.ast(""" 2 - 3 """) == (Ident("sub"), [2, 3])
        assert self.i.ast(""" 2 + 3 * 4 """) == (Ident("add"), [2, (Ident("mul"), [3, 4])])
        assert self.i.ast(""" 2 * 3 + 4 """) == (Ident("add"), [(Ident("mul"), [2, 3]), 4])

    def test_mul_div(self):
        assert self.i.ast(""" 2 * 3 """) == (Ident("mul"), [2, 3])
        assert self.i.ast(""" 2 / 3 """) == (Ident("div"), [2, 3])
        assert self.i.ast(""" 2 * 3 / 4 """) == (Ident("div"), [(Ident("mul"), [2, 3]), 4])

    def test_not(self):
        assert self.i.ast(""" not True """) == (Ident("not"), [True])
        assert self.i.ast(""" not not False """) == (Ident("not"), [(Ident("not"), [False])])

    def test_and_or(self):
        assert self.i.ast(""" True and False """) == (Ident('and'), [True, False])
        assert self.i.ast(""" True or False """) == (Ident('or'), [True, False])
        assert self.i.ast(""" True or False and True """) == (Ident('and'), [(Ident('or'), [True, False]), True])
        assert self.i.ast(""" a := False and not False """) == (Ident('define'), [Ident('a'), (Ident('and'), [False, (Ident('not'), [False])])])
        assert self.i.ast(""" a := False or not False """) == (Ident('define'), [Ident('a'), (Ident('or'), [False, (Ident('not'), [False])])])

    def test_neg(self):
        assert self.i.ast(""" -2 """) == (Ident("neg"), [2])
        assert self.i.ast(""" --3 """) == (Ident("neg"), [(Ident("neg"), [3])])

    def test_number(self):
        assert self.i.ast(""" 2 """) == 2

    def test_bool_none(self):
        assert self.i.ast(""" True """) is True
        assert self.i.ast(""" False """) is False
        assert self.i.ast(""" None """) is None

    def test_paren(self):
        assert self.i.ast(""" (1 + 2) """) == (Ident("add"), [1, 2])
        assert self.i.ast(""" (1 + 2) * 3 """) == (Ident("mul"), [(Ident("add"), [1, 2]), 3])

    def test_string(self):
        assert self.i.ast(""" 'hello' """) == "hello"
        assert self.i.ast(""" "hello" """) == "hello"
        assert self.i.ast(r""" "a\nb" """) == "a\nb"

    def test_seq(self):
        assert self.i.ast(""" 2; 3 """) == (Ident("seq"), [2, 3])
        assert self.i.ast(""" not True; False """) == (Ident("seq"), [(Ident("not"), [True]), False])

    def test_if(self):
        assert self.i.ast(""" if True then 2 else 3 end """) == (
            Ident("__core_if_macro"), [True, 2, [], [3]])
        assert self.i.ast(""" if not True then 2 + 3 else 4; 5 end """) == (
            Ident("__core_if_macro"), [(Ident('not'), [True]), (Ident('add'), [2, 3]), [], [(Ident("seq"), [4, 5])]])

        assert self.i.ast(""" if 1 then 10 end """) == (Ident('__core_if_macro'), [1, 10, [], []])
        assert self.i.ast(""" if 1 then 10 else 20 end """) == (Ident("__core_if_macro"), [1, 10, [], [20]])
        assert self.i.ast(""" if 1 then 10 elif 2 then 20 end """) == (Ident("__core_if_macro"), [1, 10, [[2, 20]], []])
        assert self.i.ast(""" if 1 then 10 elif 2 then 20 else 30 end """) == (Ident("__core_if_macro"), [1, 10, [[2, 20]], [30]])
        assert self.i.ast(""" if 1 then 10 elif 2 then 20 elif 3 then 30 else 40 end """) == (Ident("__core_if_macro"), [1, 10, [[2, 20], [3, 30]], [40]])

    def test_define(self):
        assert self.i.ast(""" a := not True """) == (Ident("define"), [Ident("a"), (Ident("not"), [True])])
        assert self.i.ast(""" a := b := 2 """) == (Ident("define"), [Ident("a"), (Ident("define"), [Ident("b"), 2])])

    def test_assign(self):
        assert self.i.ast(""" a = 1 """) == (Ident("assign"), [Ident("a"), 1])
        assert self.i.ast(""" a = b = 2 """) == (Ident("assign"), [Ident("a"), (Ident("assign"), [Ident("b"), 2])])
        assert self.i.ast(""" a := b = 2 """) == (Ident("define"), [Ident("a"), (Ident("assign"), [Ident("b"), 2])])
        assert self.i.ast(""" a := b = c := 3 """) == (Ident("define"), [Ident("a"), (Ident("assign"), [Ident("b"), (Ident("define"), [Ident("c"), 3])])])

    def test_list_assign(self):
        assert self.i.ast(""" a[0] = 1 """) == (Ident("assign"), [(Ident("index"), [Ident("a"), 0]), 1])
        assert self.i.ast(""" a[1][2] = 3 """) == (Ident("assign"), [(Ident("index"), [(Ident("index"), [Ident("a"), 1]), 2]), 3])
        assert self.i.ast(""" a[0] = b[1] = 2 """) == (Ident("assign"), [(Ident("index"), [Ident("a"), 0]), (Ident("assign"), [(Ident("index"), [Ident("b"), 1]), 2])])

    def test_while(self):
        assert self.i.ast(""" while i < 10 do i = i + 1 end """) == (Ident('__core_while'), [(Ident('less'), [Ident('i'), 10]), (Ident('assign'), [Ident('i'), (Ident('add'), [Ident('i'), 1])])])

    def test_call(self):
        assert self.i.ast(""" print() """) == (Ident("print"), [])
        assert self.i.ast(""" neg(2) """) == (Ident("neg"), [2])
        assert self.i.ast(""" add(2, mul(3, 4)) """) == (Ident("add"), [2, (Ident("mul"), [3, 4])])

    def test_index(self):
        assert self.i.ast(""" a[0] """) == (Ident("index"), [Ident("a"), 0])
        assert self.i.ast(""" a[1][2] """) == (Ident("index"), [(Ident("index"), [Ident("a"), 1]), 2])

    def test_func(self):
        assert self.i.ast(""" func do 2 end """) == (Ident("__core_func"), [[], 2])
        assert self.i.ast(""" func a do a + 2 end """) == (Ident("__core_func"), [[Ident("a")], (Ident("add"), [Ident("a"), 2])])
        assert self.i.ast(""" func a, b do a + b end """) == (Ident("__core_func"), [[Ident("a"), Ident("b")], (Ident("add"), [Ident("a"), Ident("b")])])

        with pytest.raises(AssertionError):
            self.i.ast(""" func a 2 end """)
        with pytest.raises(AssertionError):
            self.i.ast(""" func a do 2 """)

    def test_deffunc(self):
        assert self.i.walk(""" expand(deffunc two params do 2 end) """) == (
            Ident('define'), [Ident('two'), (Ident('__core_func'), [[], 2])])
        assert self.i.walk(""" expand(
             deffunc add2 params a do
                a + 2
             end
        )""") == (Ident('define'), [Ident('add2'), (Ident('__core_func'), [[Ident('a')], (Ident('add'), [Ident('a'), 2])])])
        assert self.i.walk(""" expand(
            deffunc sum params a, b, c do
                a + b + c
            end
        ) """) == (Ident('define'), [Ident('sum'), (Ident('__core_func'), [[Ident('a'), Ident('b'), Ident('c')], (Ident('add'), [(Ident('add'), [Ident('a'), Ident('b')]), Ident('c')])])])

        with pytest.raises(AssertionError):
            self.i.walk(""" deffunc add2 a do a + 2 end """)
        with pytest.raises(AssertionError):
            self.i.walk(""" deffunc add2 params a a + 2 end """)
        with pytest.raises(AssertionError):
            self.i.walk(""" deffunc 2 params do 3 end """)

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
        self.i.evaluate((Ident("seq"), [
            (Ident("print"), [2]),
            (Ident("print"), [3])
        ]))
        assert capsys.readouterr().out == "2\n3\n"

    def test_evaluate_if(self):
        assert self.i.evaluate((Ident("__core_if"), [True, 2, 3])) == 2
        assert self.i.evaluate((Ident("__core_if"), [False, 2, 3])) == 3
        assert self.i.evaluate((Ident("__core_if"), [(Ident("__core_if"), [True, True, False]), 2, 3])) == 2
        assert self.i.evaluate((Ident("__core_if"), [True, (Ident("__core_if"), [True, 2, 3]), 4])) == 2
        assert self.i.evaluate((Ident("__core_if"), [False, 2, (Ident("__core_if"), [False, 3, 4])])) == 4

    def test_evaluate_variable(self):
        assert self.i.evaluate((Ident("define"), [Ident("a"), 2])) == 2
        assert self.i.evaluate(Ident("a")) == 2

        assert self.i.evaluate((Ident("define"), [Ident("b"), True])) == True
        assert self.i.evaluate((Ident("__core_if"), [Ident("b"), 2, 3])) == 2

        assert self.i.evaluate((Ident("define"), [Ident("c"), (Ident("__core_if"), [False, 2, 3])])) == 3
        assert self.i.evaluate(Ident("c")) == 3

    def test_evaluate_undefined_variable(self):
        with pytest.raises(AssertionError):
            self.i.evaluate(Ident("a"))

    def test_evaluate_assign(self):
        self.i.evaluate((Ident("define"), [Ident("a"), 1]))
        assert self.i.evaluate((Ident("assign"), [Ident("a"), 2])) == 2
        assert self.i.evaluate(Ident("a")) == 2
        with pytest.raises(AssertionError):
            self.i.evaluate((Ident("assign"), [Ident("b"), 2]))

    def test_evaluate_scope(self, capsys):
        self.i.evaluate((Ident("define"), [Ident("a"), 2]))
        assert self.i.evaluate(Ident("a")) == 2
        assert self.i.evaluate((Ident("__core_scope"), [Ident("a")])) == 2

        assert self.i.evaluate((Ident("__core_scope"), [(Ident("seq"), [
            (Ident("print"), [Ident("a")]),
            (Ident("define"), [Ident("a"), 3]),
            (Ident("print"), [Ident("a")]),
            (Ident("define"), [Ident("b"), 4]),
            (Ident("print"), [Ident("b")]),
            Ident("b")
        ])])) == 4
        assert capsys.readouterr().out == "2\n3\n4\n"

        assert self.i.evaluate(Ident("a")) == 2

        with pytest.raises(AssertionError):
            self.i.evaluate(Ident("b"))

    def test_builtin_functions(self, capsys):
        assert self.i.evaluate((Ident("add"), [2, 3])) == 5
        assert self.i.evaluate((Ident("sub"), [5, 3])) == 2
        assert self.i.evaluate((Ident("mul"), [2, 3])) == 6

        assert self.i.evaluate((Ident("equal"), [2, 2])) is True
        assert self.i.evaluate((Ident("equal"), [2, 3])) is False

        assert self.i.evaluate((Ident("add"), [2, (Ident("mul"), [3, 4])])) == 14

        self.i.evaluate((Ident("print"), [2, 3]))
        assert capsys.readouterr().out == "2 3\n"

        self.i.evaluate((Ident("print"), [(Ident("add"), [5, 5])]))
        assert capsys.readouterr().out == "10\n"

    def test_user_func(self):
        self.i.evaluate((Ident("define"), [Ident("add2"), (Ident("__core_func"),
            [[Ident("a")], (Ident("add"), [Ident("a"), 2])]
        )]))
        assert self.i.evaluate((Ident("add2"), [3])) == 5

        self.i.evaluate((Ident("define"), [Ident("sum3"), (Ident("__core_func"),
            [[Ident("a"), Ident("b"), Ident("c")],(Ident("add"), [Ident("a"), (Ident("add"), [Ident("b"), Ident("c")])])]
        )]))
        assert self.i.evaluate((Ident("sum3"), [2, 3, 4])) == 9

    def test_recursion(self):
        self.i.evaluate((Ident("define"), [Ident("fac"), (Ident("__core_func"), [
            [Ident("n")],
            (Ident("__core_if"), [
                (Ident("equal"), [Ident("n"), 1]),
                1,
                (Ident("mul"), [Ident("n"), (Ident("fac"), [(Ident("sub"), [Ident("n"), 1])])])
        ])
        ])]))
        assert self.i.evaluate((Ident("fac"), [1])) == 1
        assert self.i.evaluate((Ident("fac"), [3])) == 6
        assert self.i.evaluate((Ident("fac"), [5])) == 120

    def test_scope_leak(self):
        self.i.evaluate((Ident("define"), [Ident("x"), 2]))
        self.i.evaluate((Ident("define"), [Ident("f"), (Ident("__core_func"), [[Ident("x")], 3])]))
        self.i.evaluate((Ident("f"), [4]))
        assert self.i.evaluate(Ident("x")) == 2

    def test_closure(self):
        self.i.evaluate((Ident("define"), [Ident("x"), 2]))
        self.i.evaluate((Ident("define"), [Ident("return_x"), (Ident("__core_func"), [[], Ident("x")])]))
        assert self.i.evaluate((Ident("return_x"), [])) == 2
        assert self.i.evaluate((Ident("__core_scope"), [(Ident("seq"), [
            (Ident("define"), [Ident("x"), 3]),
            (Ident("return_x"), [])
        ])])) == 2
        assert self.i.evaluate(Ident("x")) == 2

    def test_adder(self):
        self.i.evaluate((Ident("define"), [Ident("make_adder"), (Ident("__core_func"), [
            [Ident("n")],
            (Ident("__core_func"), [[Ident("m")], (Ident("add"), [Ident("n"), Ident("m")])])
        ])]))
        self.i.evaluate((Ident("define"), [Ident("add2"), (Ident("make_adder"), [2])]))
        self.i.evaluate((Ident("define"), [Ident("add3"), (Ident("make_adder"), [3])]))

        assert self.i.evaluate((Ident("add2"), [3])) == 5
        assert self.i.evaluate((Ident("add3"), [4])) == 7

    def test_shadowing(self):
        self.i.evaluate((Ident("define"), [Ident("make_shadow"), (Ident("__core_func"), [
            [Ident("x")],
            (Ident("__core_func"), [
                [],
                (Ident("seq"), [
                    (Ident("define"), [Ident("x"), 3]),
                    Ident("x")
                ])
            ])
        ])]))
        self.i.evaluate((Ident("define"), [Ident("g"), (Ident("make_shadow"), [2])]))
        assert self.i.evaluate((Ident("g"), [])) == 3

    def test_list(self):
        self.i.evaluate((Ident("define"), [Ident("a"), [1, 2, 3]]))
        assert self.i.evaluate(Ident("a")) == [1, 2, 3]
        assert self.i.evaluate((Ident("index"), [Ident("a"), 0])) == 1
        assert self.i.evaluate((Ident("index"), [Ident("a"), 2])) == 3

        self.i.evaluate((Ident("assign"), [(Ident("index"), [Ident("a"), 1]), 4]))
        assert self.i.evaluate(Ident("a")) == [1, 4, 3]

    def test_list_nested(self):
        self.i.evaluate((Ident("define"), [Ident("a"), [
            [1, 2],
            [3, 4]
        ]]))
        assert self.i.evaluate((Ident("index"), [(Ident("index"), [Ident("a"), 0]), 1])) == 2
        assert self.i.evaluate((Ident("index"), [(Ident("index"), [Ident("a"), 1]), 0])) == 3

        self.i.evaluate((Ident("assign"), [(Ident("index"), [(Ident("index"), [Ident("a"), 1]), 0]), 5]))
        assert self.i.evaluate((Ident("index"), [(Ident("index"), [Ident("a"), 1]), 0])) == 5

    def test_list_push_pop(self):
        self.i.evaluate((Ident("define"), [Ident("a"), [1, 2]]))
        self.i.evaluate((Ident("push"), [Ident("a"), 3]))
        assert self.i.evaluate(Ident("a")) == [1, 2, 3]
        assert self.i.evaluate((Ident("pop"), [Ident("a")])) == 3
        assert self.i.evaluate(Ident("a")) == [1, 2]

    def test_list_funcs(self):
        self.i.evaluate((Ident("define"), [Ident("a"), [1, 2, 3]]))
        assert self.i.evaluate((Ident("len"), [Ident("a")])) == 3
        assert self.i.evaluate((Ident("slice"), [Ident("a"), 1, None])) == [2, 3]
        assert self.i.evaluate((Ident("slice"), [Ident("a"), 1, 2])) == [2]
        assert self.i.evaluate((Ident("slice"), [Ident("a"), None, 2])) == [1, 2]
        assert self.i.evaluate((Ident("slice"), [Ident("a"), None, None])) == [1, 2, 3]

    def test_list_error(self):
        self.i.evaluate((Ident("define"), [Ident("a"), [1, 2]]))

        with pytest.raises(AssertionError, match="Invalid indexing"):
            self.i.evaluate((Ident("assign"), [(Ident("index"), [None, 0]), 1]))

        with pytest.raises(AssertionError, match="Invalid indexing"):
            self.i.evaluate((Ident("assign"), [(Ident("index"), [Ident("a"), None]), 1]))

class TestGo(TestBase):
    def test_whitespace(self):
        assert self.i.walk("""  3 """) == 3
        assert self.i.walk(""" 4 \t """) == 4
        assert self.i.walk(""" 56\n """) == 56

    def test_comparison(self):
        assert self.i.walk(""" 2 + 5 == 3 + 4 """) is True
        assert self.i.walk(""" 2 + 3 == 3 + 4 """) is False
        assert self.i.walk(""" 2 + 5 != 3 + 4 """) is False
        assert self.i.walk(""" 2 + 3 != 3 + 4 """) is True

        assert self.i.walk(""" 2 + 4 < 3 + 4 """) is True
        assert self.i.walk(""" 2 + 5 < 3 + 4 """) is False
        assert self.i.walk(""" 2 + 5 < 2 + 4 """) is False
        assert self.i.walk(""" 2 + 4 > 3 + 4 """) is False
        assert self.i.walk(""" 2 + 5 > 3 + 4 """) is False
        assert self.i.walk(""" 2 + 5 > 2 + 4 """) is True

        assert self.i.walk(""" 2 + 4 <= 3 + 4 """) is True
        assert self.i.walk(""" 2 + 5 <= 3 + 4 """) is True
        assert self.i.walk(""" 2 + 5 <= 2 + 4 """) is False
        assert self.i.walk(""" 2 + 4 >= 3 + 4 """) is False
        assert self.i.walk(""" 2 + 5 >= 3 + 4 """) is True
        assert self.i.walk(""" 2 + 5 >= 2 + 4 """) is True

        assert self.i.walk(""" 2 == 2 == 2 """) is False

    def test_add_sub(self):
        assert self.i.walk(""" 2 + 3 """) == 5
        assert self.i.walk(""" 5 - 3 """) == 2
        assert self.i.walk(""" 2 + 3 - 4 + 5 """) == 6

    def test_mul_div_mod(self):
        assert self.i.walk(""" 2 * 3 """) == 6
        assert self.i.walk(""" 6 / 3 """) == 2
        assert self.i.walk(""" 7 % 3 """) == 1
        assert self.i.walk(""" 2 * 3 / 2 """) == 3
        assert self.i.walk(""" 2 * 3 + 4 """) == 10
        assert self.i.walk(""" 2 + 3 * 4 """) == 14

    def test_not(self):
        assert self.i.walk(""" not True """) is False
        assert self.i.walk(""" not False """) is True
        assert self.i.walk(""" not not True """) is True
        assert self.i.walk(""" not 2 == 3 """) is True

    def test_and_or(self, capsys):
        assert self.i.walk(""" True and False """) is False
        assert self.i.walk(""" True or False """) is True
        assert self.i.walk(""" False and True """) is False
        assert self.i.walk(""" False or True """) is True

        assert self.i.walk(""" True and 2 """) == 2
        assert self.i.walk(""" 0 and 2 / 0 """) == 0
        assert self.i.walk(""" False or 2 """) == 2
        assert self.i.walk(""" 1 or 2 / 0 """) == 1

    def test_neg(self):
        assert self.i.walk(""" -2 """) == -2
        assert self.i.walk(""" --2 """) == 2
        assert self.i.walk(""" -2 * 3 """) == -6

    def test_number(self):
        assert self.i.walk(""" 2 """) == 2

        with pytest.raises(AssertionError):
            self.i.walk(""" a """)

    def test_bool_none(self):
        assert self.i.walk(""" True """) is True
        assert self.i.walk(""" False """) is False
        assert self.i.walk(""" None """) is None

    def test_paren(self):
        assert self.i.walk(""" (2 + 3) * 4 """) == 20
        assert self.i.walk(""" 2 * (3 + 4) """) == 14
        assert self.i.walk(""" 2 * (3 + 4 * 5) """) == 46

    def test_seq(self):
        assert self.i.walk(""" 2; 3 """) == 3
        assert self.i.walk(""" 2; 3; 4 """) == 4
        assert self.i.walk(""" True; not True """) is False

    def test_if(self):
        assert self.i.walk(""" if True then 2 else 3 end """) == 2
        assert self.i.walk(""" if False then 2 else 3 end """) == 3

        assert self.i.walk(""" if not True then 2 + 3 else 4; 5 end """) == 5

        assert self.i.walk(""" if True then 2 end """) == 2
        assert self.i.walk(""" if False then 2 end """) is None

        assert self.i.walk(""" if False then 2 elif True then 3 else 4 end """) == 3
        assert self.i.walk(""" if False then 2 elif False then 3 else 4 end """) == 4

        with pytest.raises(AssertionError):
            self.i.walk(""" if True then 2 else 3 """)
        with pytest.raises(AssertionError):
            self.i.walk(""" if True else 2 end """)

    def test_var_define(self):
        assert self.i.walk(""" a := not True """) == False
        assert self.i.walk(""" a """) == False
        assert self.i.walk(""" a := b := not False """) == True
        assert self.i.walk(""" a """) == True
        assert self.i.walk(""" b """) == True

    def test_assign(self):
        assert self.i.walk(""" a := 1; a = 2; a """) == 2
        assert self.i.walk(""" a := 1; b := 2; a = b = 3; a """) == 3
        assert self.i.walk(""" a := 2; a = 3 """) == 3
        assert self.i.walk(""" a := b := 2; a = b = 3 """) == 3

    def test_scope_assign(self, capsys):
        self.i.walk("""
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
            self.i.walk(""" c """)

    def test_while(self):
        assert self.i.walk("""
            sum := i := 0;
            while i < 10 do
                sum = sum + i;
                i = i + 1
            end;
            sum
        """) == 45

        assert self.i.walk(""" while False do 1 end """) is None
        assert self.i.walk(""" i := 0; while False do i = 1 end; i """) == 0

        with pytest.raises(AssertionError):
            self.i.walk(""" while do i = i + 1 end """)
        with pytest.raises(AssertionError):
            self.i.walk(""" while i < 10 i = i + 1 end """)
        with pytest.raises(AssertionError):
            self.i.walk(""" while i < 10 do i = i + 1 """)

    def test_for(self, capsys):
        assert self.i.walk("""
            sum := 0;
            for n in [2, 3, 4] do
                sum = sum + n
            end;
            sum """) == 9

        assert self.i.walk(""" for i in [] do print("never") end; "ok" """) == "ok"
        assert capsys.readouterr().out == ""

        assert self.i.walk("""
            for i in [2, 3, 4] do
                if i == 3 then break(i * 10) end
            end
        """) == 30

        self.i.walk("""
            for i in [2, 3, 4] do
                if i == 3 then continue() end;
                print(i)
            end
        """)
        assert capsys.readouterr().out == "2\n4\n"

        self.i.walk("""
            funcs := [];
            for i in [2, 3, 4] do
                funcs.push(func do i end)
            end;
            print(funcs[0](), funcs[1](), funcs[2]())
        """)
        assert capsys.readouterr().out == "2 3 4\n"

        self.i.walk("""
            keys := ["a", "b", "c"];
            values := [2, 3, 4];
            for [k, v] in zip(keys, values) do
                print(k, v)
            end
        """)
        assert capsys.readouterr().out == "a 2\nb 3\nc 4\n"

        self.i.walk("""
            dic := { "a": 2, "b": 3, "c": 4 };
            for [k, v] in dic.items() do
                print(k, v)
            end
        """)
        assert capsys.readouterr().out == "a 2\nb 3\nc 4\n"

        with pytest.raises(AssertionError, match="Undefined variable"):
            self.i.walk(""" for i in [2] do 1 end; i """)

    def test_call(self, capsys):
        assert self.i.walk(""" add(2, 3) """) == 5
        assert self.i.walk(""" add(2, mul(3, 4)) """) == 14
        self.i.walk(""" print(5) """)
        assert capsys.readouterr().out == "5\n"
        self.i.walk(""" print(6, 7) """)
        assert capsys.readouterr().out == "6 7\n"
        self.i.walk(""" print() """)
        assert capsys.readouterr().out == "\n"

    def test_func(self):
        assert self.i.walk(""" func do 2 end () """) == 2
        assert self.i.walk(""" func a do a + 2 end (3) """) == 5
        assert self.i.walk(""" func a, b do a + b end (2, 3) """) == 5

    def test_deffunc(self):
        self.i.walk(""" deffunc two params do 2 end """)
        assert self.i.walk(""" two() """) == 2
        self.i.walk(""" deffunc add2 params a do a + 2 end """)
        assert self.i.walk(""" add2(3) """) == 5
        self.i.walk(""" deffunc sum params a, b, c do a + b + c end """)
        assert self.i.walk(""" sum(2, 3, 4) """) == 9

    def test_fac(self):
        assert self.i.walk("""
            deffunc fac params n do
                if n == 1 then 1 else n * fac(n - 1) end
            end;
            fac(5)
        """) == 120

    def test_fib(self):
        self.i.walk("""
            deffunc fib params n do
                if n == 0 then 0
                elif n == 1 then 1
                else fib(n - 1) + fib(n - 2)
                end
            end
        """)
        assert self.i.walk(""" fib(0) """) == 0
        assert self.i.walk(""" fib(1) """) == 1
        assert self.i.walk(""" fib(7) """) == 13
        assert self.i.walk(""" fib(9) """) == 34

    def test_gcd_recursive(self):
        assert self.i.walk("""
            deffunc gcd params a, b do
                if a == 0 then b else gcd(b % a, a) end
            end;
            gcd(24, 36)
        """) == 12

    def test_mutual_recursion(self):
        self.i.walk("""
            deffunc is_even params n do if n == 0 then True else is_odd(n - 1) end end;
            deffunc is_odd params n do if n == 0 then False else is_even(n - 1) end end
        """)
        assert self.i.walk(""" is_even(10) """) is True
        assert self.i.walk(""" is_odd(10) """) is False

    def test_gcd_iterative(self):
        assert self.i.walk("""
            deffunc gcd params a, b do
                while a != 0 do
                    [a, b] := [b % a, a]
                end;
                b
            end;
            gcd(24, 36)
        """) == 12

    def test_no_code(self):
        with pytest.raises(AssertionError):
            self.i.walk("""  """)

    def test_extra_token(self):
        with pytest.raises(AssertionError):
            self.i.walk(""" 7 8 """)

    def test_list(self):
        assert self.i.walk(""" [] """) == []
        assert self.i.walk(""" [2 + 3] """) == [5]
        assert self.i.walk(""" [2][0] """) == 2
        assert self.i.walk(""" [2, 3, [4, 5]] """) == [2, 3, [4, 5]]

        self.i.walk(""" a := [2, 3, [4, 5]] """)
        assert self.i.walk(""" a[2][0] """) == 4
        assert self.i.walk(""" a[2][-1] """) == 5

        self.i.walk(""" b := [2, 3, [4, 5]] """)
        self.i.walk(""" b[0] = 6 """)
        assert self.i.walk(""" b[0] """) == 6
        self.i.walk(""" b[2][1] = 7 """)
        assert self.i.walk(""" b[2][1] """) == 7
        assert self.i.walk(""" b """) == [6, 3, [4, 7]]

        self.i.walk(""" c := func do [add, sub] end """)
        assert self.i.walk(""" c()[0](2, 3) """) == 5

        self.i.walk(""" d := [2, 3, 4] """)
        assert self.i.walk(""" len(d) """) == 3
        assert self.i.walk(""" slice(d, 1, None) """) == [3, 4]
        assert self.i.walk(""" slice(d, 1, 2) """) == [3]
        assert self.i.walk(""" slice(d, None, 2) """) == [2, 3]
        assert self.i.walk(""" slice(d, None, None) """) == [2, 3, 4]
        assert self.i.walk(""" push(d, 5) """) is None
        assert self.i.walk(""" d """) == [2, 3, 4, 5]
        assert self.i.walk(""" pop(d) """) == 5
        assert self.i.walk(""" d """) == [2, 3, 4]

        assert self.i.walk(""" [2, 3] + [4, 5] """) == [2, 3, 4, 5]
        assert self.i.walk(""" [2, 3] * 3 """) == [2, 3, 2, 3, 2, 3]

        self.i.walk(""" e := [1] """)
        with pytest.raises(AssertionError):
            self.i.walk(""" e[None] = 2 """)
        with pytest.raises(AssertionError):
            self.i.walk(""" None[2] = 3 """)

    def test_stdlib(self):
        assert self.i.walk(""" a := range(2, 10) """) == [2, 3, 4, 5, 6, 7, 8, 9]
        assert self.i.walk(""" first(a) """) == 2
        assert self.i.walk(""" rest(a) """) == [3, 4, 5, 6, 7, 8, 9]
        assert self.i.walk(""" last(a) """) == 9
        assert self.i.walk(""" map(a, func n do n * 2 end) """) == [4, 6, 8, 10, 12, 14, 16, 18]
        assert self.i.walk(""" filter(a, func n do n % 2 == 0 end) """) == [2, 4, 6, 8]
        assert self.i.walk(""" reduce(a, add, 0) """) == 44
        assert self.i.walk(""" reverse(a) """) == [9, 8, 7, 6, 5, 4, 3, 2]
        assert self.i.walk(""" zip(a, [4, 5, 6]) """) == [[2, 4], [3, 5], [4, 6]]
        assert self.i.walk(""" enumerate(a) """) == [[0, 2], [1, 3], [2, 4], [3, 5], [4, 6], [5, 7], [6, 8], [7, 9]]

    def test_list_sieve(self):
        assert self.i.walk("""
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
        assert self.i.walk(""" 'Hello, world!' """) == "Hello, world!"
        assert self.i.walk(""" '
multi
line
text
'       """) == "\nmulti\nline\ntext\n"
        assert self.i.walk(""" 'Hello, world!'[1] """) == "e"
        assert self.i.walk(""" 'Hello, ' + 'world!' """) == "Hello, world!"
        assert self.i.walk(""" 'Hello, ' * 3 """) == "Hello, Hello, Hello, "

        assert self.i.walk(""" len('Hello, world!') """) == 13
        assert self.i.walk(""" first('Hello, world!') """) == "H"
        assert self.i.walk(""" rest('Hello, world!') """) == "ello, world!"
        assert self.i.walk(""" last('Hello, world!') """) == "!"

        assert self.i.walk(""" join(['H', 'e', 'l', 'l', 'o'], ' ') """) == "H e l l o"
        assert self.i.walk(""" ord('A') """) == 65
        assert self.i.walk(""" chr(65) """) == "A"

        assert self.i.walk(""" "Hello, world!" """) == "Hello, world!"
        assert self.i.walk(r""" "Hello,\nworld!" """) == "Hello,\nworld!"
        assert self.i.walk(r""" "Hello,\\world!" """) == "Hello,\\world!"
        assert self.i.walk(r""" "Hello,\"world!" """) == 'Hello,"world!'

    def test_destructuring_assignment(self):
        self.i.walk(""" [a, b] := [2, 3] """)
        assert self.i.walk(""" a """) == 2
        assert self.i.walk(""" b """) == 3

        self.i.walk(""" [a, [b, c]] := [2, [3, 4]] """)
        assert self.i.walk(""" a """) == 2
        assert self.i.walk(""" b """) == 3
        assert self.i.walk(""" c """) == 4

        self.i.walk(""" [a, *b] := [2] """)
        assert self.i.walk(""" a """) == 2
        assert self.i.walk(""" b """) == []

        self.i.walk(""" [a, *b] := [2, 3, 4] """)
        assert self.i.walk(""" a """) == 2
        assert self.i.walk(""" b """) == [3, 4]

        self.i.walk(""" [*a] := [2, 3] """)
        assert self.i.walk(""" a """) == [2, 3]

        with pytest.raises(AssertionError):
            self.i.walk(""" [*b, a] := [2] """)

    def test_argument_destructuring(self, capsys):
        self.i.walk(""" deffunc f params a, [b, c] do [a, b, c] end """)
        assert self.i.walk(""" f(2, [3, 4]) """) == [2, 3, 4]

        self.i.walk(""" deffunc g params *a do a end""")
        assert self.i.walk(""" g() """) == []
        assert self.i.walk(""" g(2 + 3) """) == [5]
        assert self.i.walk(""" g(2, 3, 4) """) == [2, 3, 4]

        self.i.walk(""" deffunc h params a, *b do [a, b] end """)
        assert self.i.walk(""" h(2 + 3) """) == [5, []]
        assert self.i.walk(""" h(2, 3, 4) """) == [2, [3, 4]]
        with pytest.raises(AssertionError):
            self.i.walk(""" h() """)

        self.i.walk(""" deffunc i params *a, b do [a, b] end """)
        with pytest.raises(AssertionError):
            self.i.walk(""" i(2, 3, 4) """)

    def test_match(self):
        self.i.walk("""
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
        assert self.i.walk(""" f(2) """) == "two"
        assert self.i.walk(""" f("two") """) == 3
        assert self.i.walk(""" f([2]) """) == 2
        assert self.i.walk(""" f([2, 3]) """) == -2
        assert self.i.walk(""" f([2, [3, 4]]) """) == 12
        assert self.i.walk(""" f([2, [2, 4]]) """) == 8
        assert self.i.walk(""" f([2, 4]) """) == 6
        assert self.i.walk(""" f([2, 3, 4]) """) == "not match"

        with pytest.raises(AssertionError):
            self.i.walk(""" a """)

    def test_match_copy(self):
        assert self.i.walk("""
            a := [2, 3, 4];
            match a
                case b then b[0] = 5
            end;
            a
        """) == [5, 3, 4]

        assert self.i.walk("""
            a := [2, 3, 4];
            match a
                case [*b] then b[0] = 5
            end;
            a
        """) == [2, 3, 4]

    def test_continue(self):
        assert self.i.walk("""
            a := [];
            i := 0; while i < 5 do
                i = i + 1;
                if i == 3 then continue() end;
                push(a, i)
            end;
            a
        """) == [1, 2, 4, 5]

        assert self.i.walk("""
            a := []; i := 0; while i < 2 do
                j := 0; while j < 3 do
                    j = j + 1; if j == 2 then continue() end; push(a, [i, j])
                end; i = i + 1
            end;
            a
        """) == [[0, 1], [0, 3], [1, 1], [1, 3]]

        with pytest.raises(AssertionError, match="Continue takes no arguments"):
            self.i.walk(""" while True do continue(2) end """)

        with pytest.raises(AssertionError, match="Continue at top level"):
            self.i.walk(""" continue() """)

    def test_break(self):
        assert self.i.walk("""
            a := [];
            i := 0; while i < 5 do
                if i == 3 then break() end;
                push(a, i);
                i = i + 1
            end;
            a
        """) == [0, 1, 2]

        assert self.i.walk("""
            a := []; i := 0; while i < 2 do
                j := 0; while j < 3 do
                    if j == 2 then break() end; push(a, [i, j]); j = j + 1
                end; i = i + 1
            end; a
        """) == [[0, 0], [0, 1], [1, 0], [1, 1]]

        assert self.i.walk(""" while True do break() end """) == None
        assert self.i.walk(""" while True do break(2 + 3) end """) == 5

        with pytest.raises(AssertionError, match="Break takes zero or one argument"):
            self.i.walk(""" while True do break(2, 3) end """)

        with pytest.raises(AssertionError, match="Break at top level"):
            self.i.walk(""" break() """)

    def test_return(self):
        self.i.walk("""
            deffunc f params a do
                if a == 2 then return(3) end;
                4
            end
        """)
        assert self.i.walk(""" f(2) """) == 3
        assert self.i.walk(""" f(3) """) == 4

        self.i.walk("""
            deffunc fib params n do
                if n == 0 then return(0) end;
                if n == 1 then return(1) end;
                fib(n - 1) + fib(n - 2)
            end
        """)
        assert self.i.walk(""" fib(0) """) == 0
        assert self.i.walk(""" fib(1) """) == 1
        assert self.i.walk(""" fib(7) """) == 13
        assert self.i.walk(""" fib(9) """) == 34

        with pytest.raises(AssertionError, match="Return takes zero or one argument"):
            self.i.walk(""" func do return(2, 3) end () """)

        with pytest.raises(AssertionError, match="Return from top level"):
            self.i.walk(""" return() """)


    def test_import(self, tmp_path):
        self.i.walk(""" fib := import("lib/fib.toil") """)
        assert self.i.walk(""" fib(9) """) == 34

        self.i.walk(""" [gcd_recur, gcd_iter] := import("lib/gcd.toil") """)
        assert self.i.walk(""" gcd_recur(24, 36) """) == 12
        assert self.i.walk(""" gcd_iter(24, 36) """) == 12

    def test_import_isolation(self, tmp_path):
        mod_a_path = tmp_path / "mod_a.toil"
        mod_a_path.write_text("a_private := 100; func do a_private end")

        self.i.walk(f""" f := import("{mod_a_path}") """)
        assert self.i.walk("f()") == 100
        with pytest.raises(AssertionError, match="Undefined variable"):
            self.i.walk("a_private")

        mod_b_path = tmp_path / "mod_b.toil"
        mod_b_path.write_text("b_private := 200; a_private")
        with pytest.raises(AssertionError, match="Undefined variable"):
            self.i.walk(f""" import("{mod_b_path}") """)

    def test_dict(self):
        assert self.i.walk(""" {} """) == {}
        assert self.i.walk(""" {"aaa": 2} """) == {'aaa': 2}
        self.i.walk(""" bbb := 4 """)
        assert self.i.walk(""" {aaa: 2 + 3, bbb} """) == {'aaa': 5, 'bbb': 4}

        self.i.walk(""" a := {aaa: 2 + 3, bbb} """)
        assert self.i.walk(""" a["aaa"] """) == 5
        assert self.i.walk(""" a["bbb"] """) == 4
        with pytest.raises(KeyError):
            self.i.walk(""" a["ccc"] """)

        self.i.walk(""" a["aaa"] = 2 """)
        assert self.i.walk(""" a """) == {'aaa': 2, 'bbb': 4}
        self.i.walk(""" a["ccc"] = 5 """)
        assert self.i.walk(""" a """) == {'aaa': 2, 'bbb': 4, 'ccc': 5}

        assert self.i.walk(""" len(a) """) == 3
        assert self.i.walk(""" in("aaa", a) """) is True
        assert self.i.walk(""" in("bbb", a) """) is True
        assert self.i.walk(""" in("ddd", a) """) is False
        assert self.i.walk(""" keys(a) """) == ['aaa', 'bbb', 'ccc']
        assert self.i.walk(""" items(a) """) == [['aaa', 2], ['bbb', 4], ['ccc', 5]]

        self.i.walk(""" [k, v] := items(a)[0] """)
        assert self.i.walk(""" k """) == 'aaa'
        assert self.i.walk(""" v """) == 2

        with pytest.raises(AssertionError, match="Invalid key"):
            self.i.walk(""" {1: 2} """)

        with pytest.raises(AssertionError, match="Invalid indexing"):
            self.i.walk(""" a[0] = 1 """)

    def test_dot_notation(self):
        self.i.walk(""" a := {aaa: 2, bbb: 4} """)
        self.i.walk(""" a.aaa = 2 """)
        assert self.i.walk(""" a.aaa """) == 2
        self.i.walk(""" a.ddd = 6 """)
        assert self.i.walk(""" a """) == {'aaa': 2, 'bbb': 4, 'ddd': 6}

        with pytest.raises(AssertionError, match="Invalid property"):
            self.i.walk(""" a.1 """)

        with pytest.raises(AssertionError):
            self.i.walk(""" [1, 2].foo """)

    def test_dict_destructuring(self):
        assert self.i.walk("""{a, b} := {a: 2, b: 3}; [a, b] """) == [2, 3]
        assert self.i.walk("""{a, *b} := {a: 2, b: 3, c: 4, d: 5}; [a, b] """) == [2, {'b': 3, 'c': 4, 'd': 5}]
        assert self.i.walk("""{*a, b} := {a: 2, b: 3, c: 4, d: 5}; [a, b] """) == [{'a': 2, 'c': 4, 'd': 5}, 3]
        assert self.i.walk("""{a, *b, c} := {a: 2, b: 3, c: 4, d: 5}; [a, b, c] """) == [2, {'b': 3, 'd': 5}, 4]

    def test_dict_pattern_match(self):
        assert self.i.walk(""" match {a: 2, b: 3} case {a, b} then [a, b] end """) == [2, 3]
        assert self.i.walk(""" match {a: 2, b: 3} case {a: aa, b: bb} then [aa, bb] end """) == [2, 3]
        assert self.i.walk(""" match {a: 2, b: 3, c: 4} case {a, b} then [a, b] end """) == [2, 3]
        assert self.i.walk(""" match {a: 2, b: {c: 3, d: 4}} case {a, b: {c, d}} then [a, c, d] end """) == [2, 3, 4]
        assert self.i.walk(""" match {a: 2, b: [3, 4]} case {a, b: [c, d]} then [a, c, d] end """) == [2, 3, 4]
        assert self.i.walk(""" match {a: 2, b: 3, c: 4} case {a, *rest} then [a, rest] end """) == [2, {'b': 3, 'c': 4}]
        assert self.i.walk(""" match {a: 2, b: 3, c: 4} case {*rest, b} then [rest, b] end """) == [{'a': 2, 'c': 4}, 3]
        assert self.i.walk(""" match {a: 2, b: 3, c: 4} case {a, *rest, c} then [a, rest, c] end """) == [2, {'b': 3}, 4]
        assert self.i.walk(""" match {a: 2} case {b: 3} then 4 end """) is None

    def test_ast_pattern_match(self):
        self.i.walk("""
            f := func ast do
                match ast
                    case Expr(Ident("add"), [left, right]) then left + right
                    case Expr(Ident("sub"), [left, right]) then left - right
                    case Expr(op, args) then [op, args]
                    case _ then None
                end
            end
        """)
        assert self.i.walk(""" f(quote 2 + 3 end) """) == 5
        assert self.i.walk(""" f(quote 5 - 2 end) """) == 3
        assert self.i.walk(""" f(quote 2 * 3 end) """) == [Ident("mul"), [2, 3]]
        assert self.i.walk(""" f(2) """) is None

        assert self.i.walk(""" f(Expr(Ident("add"), [2, 3])) """) == 5
        assert self.i.walk(""" f(Expr("add", [2, 3])) """) == ["add", [2, 3]]
        assert self.i.walk(""" f([Ident("add"), [2, 3]]) """) == None

    def test_dict_module(self):
        self.i.walk(""" gcd := import("lib/gcd_dict.toil") """)
        assert self.i.walk(""" gcd.recur(24, 36) """) == 12
        assert self.i.walk(""" gcd.iter(24, 36) """) == 12

        self.i.walk(""" {recur, iter} := import("lib/gcd_dict.toil") """)
        assert self.i.walk(""" recur(24, 36) """) == 12
        assert self.i.walk(""" iter(24, 36) """) == 12

        self.i.walk(""" {recur: gcd_recur, iter: gcd_iter} := import("lib/gcd_dict.toil") """)
        assert self.i.walk(""" gcd_recur(24, 36) """) == 12
        assert self.i.walk(""" gcd_iter(24, 36) """) == 12

    def test_ufcs(self):
        # Case 1: Namespace
        self.i.walk(""" foo := { add: func a, b do a + b end } """)
        assert self.i.walk(""" foo.add(2, 3) """) == 5

        # Case 2: Method
        self.i.walk(""" foo := { add: func self, a do self.val + a end, val: 2 } """)
        assert self.i.walk(""" foo.add(3) """) == 5

        # Case 3: UFCS
        self.i.walk(""" foo := 2 """)
        assert self.i.walk(""" add(foo, 3) """) == 5
        assert self.i.walk(""" foo.add(3) """) == 5

        self.i.walk(""" myadd := func a, b do a + b end """)
        assert self.i.walk(""" myadd(foo, 3) """) == 5
        assert self.i.walk(""" foo.myadd(3) """) == 5

        # UFCS priority
        self.i.walk(""" d := { len: func self do "local" end } """)
        assert self.i.walk(""" d.len() """) == "local"

        with pytest.raises(AssertionError, match="Invalid operator"):
            self.i.walk(""" d := { val: 123 }; d.val() """)
        with pytest.raises(AssertionError, match="Undefined variable"):
            self.i.walk(""" 2.non_existent() """)

    def test_oo_style(self, capsys):
        self.i.walk("""
            deffunc Animal params name do
                self := {};
                self._name = name;
                self.introduce = func self do print("I'm", self._name) end;
                self.make_sound = func self do print("crying") end;
                self
            end
        """)
        self.i.walk("""
            animal1 := Animal("Rocky");
            animal2 := Animal("Lucy");
            animal1.introduce();
            animal1.make_sound();
            animal2.introduce();
            animal2.make_sound()
        """)
        assert capsys.readouterr().out == "I'm Rocky\ncrying\nI'm Lucy\ncrying\n"

        self.i.walk("""
            deffunc Dog params name do
                self := Animal(name);
                self.make_sound = func self do print("woof") end;
                self
            end
        """)
        self.i.walk("""
            dog1 := Dog("Leo");
            dog1.introduce();
            dog1.make_sound()
        """)
        assert capsys.readouterr().out == "I'm Leo\nwoof\n"

    def test_oo_style_with_macro(self, capsys):
        self.i.walk(r"""
            defmacro _defclass params name, params_, body do
                quote
                    deffunc !name params !!params_ do
                        self := {};
                        !body;
                        self
                    end
                end
            end;
            #rule {defclass: [_defclass, EXPR, params, EXPRS, do, EXPR, end]}

            defmacro inherits params super do
                quote self = !super end
            end;

            defmacro _defmethod params name, params_, body do
                Expr(Ident("assign"), [
                        Expr(Ident("dot"),
                        [Ident("self"), str(name)
                    ]),
                    quote func self, !!params_ do !body end end
                ])
            end
            #rule {defmethod: [_defmethod, EXPR, params, EXPRS, do, EXPR, end]}
        """)
        self.i.walk("""
            defclass Animal params name do
                self._name = name;
                defmethod introduce params do print("I'm", self._name) end;
                defmethod new_name params name do self._name = name end;
                defmethod make_sound params do print("crying") end
            end
        """)
        self.i.walk("""
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

        self.i.walk("""
            defclass Dog params name do
                inherits(Animal(name));
                defmethod make_sound params do print("woof") end
            end
        """)
        self.i.walk("""
            dog1 := Dog("Leo");
            dog1.introduce();
            dog1.make_sound()
        """)
        assert capsys.readouterr().out == "I'm Leo\nwoof\n"

    def test_sieve_ufcs(self):
        result = self.i.walk("""
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
        self.i.walk("""
            deffunc Test params name do
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
        assert self.i.walk(""" try 2; 3 end """) == 3
        self.i.walk(""" try print(2); print(3) end """)
        assert capsys.readouterr().out == "2\n3\n"

        # try with except, no raise
        assert self.i.walk(""" try 2; 3 except e then print(e) end """) == 3
        self.i.walk(""" try print(2); print(3) except e then print(e) end """)
        assert capsys.readouterr().out == "2\n3\n"

        # try with raise and catch
        self.i.walk(""" try print(2); raise(2 + 3); print(3) except e then print(e) end """)
        assert capsys.readouterr().out == "2\n5\n"
        assert self.i.walk(""" try 2; raise(2 + 3); 3 except e then e end """) == 5

        # pattern match in except
        self.i.walk("""
            try
                print(2); raise(["foo", 3]); print(4)
            except ["foo", val] then print("foo", val)
            except ["bar", val] then print("bar", val)
            end
        """)
        assert capsys.readouterr().out == "2\nfoo 3\n"

        self.i.walk("""
            try
                print(2); raise(["bar", 3]); print(4)
            except ["foo", val] then print("foo", val)
            except ["bar", val] then print("bar", val)
            end
        """)
        assert capsys.readouterr().out == "2\nbar 3\n"

        # unhandled exception
        with pytest.raises(AssertionError, match="ToilException"):
            self.i.walk("""
                try
                    raise(["baz", 3])
                except ["foo", val] then print("foo", val)
                end
            """)

        # nested try
        self.i.walk("""
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
        assert self.i.walk(""" apply(add, [2, 3]) """) == 5
        assert self.i.walk(""" apply(func a, b do a + b end, [2, 3]) """) == 5

        # eval
        self.i.walk(""" a := 2; b := 3 """)
        assert self.i.walk(""" eval("a + b") """) == 5
        assert self.i.walk(""" scope a := 4; b := 5; eval("a + b") end """) == 5
        assert self.i.walk(""" scope a := 4; b := 5; eval("a + b", __env) end """) == 9
        assert self.i.walk(""" scope a := 4; b := 5; eval_expr(quote a + b end, __env) end """) == 9

        # Poor man's serialization
        self.i.walk("""
            org := { name: "Toil", id: 1 };
            print(org);
            serialized := str(org);
            print(serialized);
            deserialized := eval(serialized);
            print(deserialized)
        """)
        assert capsys.readouterr().out == "{'name': 'Toil', 'id': 1}\n{'name': 'Toil', 'id': 1}\n{'name': 'Toil', 'id': 1}\n"

        # Poor man's syntax sugar
        assert self.i.walk("""
            deffunc mydeffunc params name, params_, body do
                eval("deffunc " + name + " params " + params_ + " do " + body + " end")
            end;
            mydeffunc("myadd", "a, b", "a + b");
            myadd(2, 3)
        """) == 5

    def test_type(self):
        assert self.i.walk(""" type(None) """) == "NoneType"
        assert self.i.walk(""" type(True) """) == "bool"
        assert self.i.walk(""" type(2) """) == "int"
        assert self.i.walk(""" type("abc") """) == "str"
        assert self.i.walk(""" type([2, 3]) """) == "list"
        assert self.i.walk(""" type({a: 2}) """) == "dict"
        assert self.i.walk(""" type(quote 2 + 3 end) """) == "Expr"
        assert self.i.walk(""" type(quote a end) """) == "Ident"

    def test_env_exposure(self):
        self.i.walk(""" a := 2 """)
        assert self.i.walk(""" __env.vars.keys() """) == ["a"]
        assert self.i.walk(""" __env.vars.items() """) == [["a", 2]]
        assert self.i.walk(""" __env.val("a") """) == 2

        assert self.i.walk(""" __env.define("b", 3) """) == 3
        assert self.i.walk(""" __env.vars.keys() """) == ["a", "b"]
        assert self.i.walk(""" b """) == 3

        assert self.i.walk(""" scope c := 4; __env.vars.keys() end """) == ["c"]
        assert self.i.walk(""" scope c := 4; __env.parent.vars.keys() end """) == ["a", "b"]
        assert self.i.walk(""" scope a := 5; __env.parent.val("a") end """) == 2

        self.i.walk(""" scope __env.assign("b", 6) end """)
        assert self.i.walk(""" b """) == 6

        assert self.i.walk(""" __env.lookup("add") != None """) is True
        assert self.i.walk(""" __env.lookup("add").add(2, 3) """) == 5

        # Error cases
        with pytest.raises(AssertionError, match="Undefined variable"):
            self.i.walk(""" __env.val("not_found") """)

        with pytest.raises(AssertionError, match="Undefined variable"):
            self.i.walk(""" __env.assign("not_found", 100) """)

        # lookup not found returns None
        assert self.i.walk(""" __env.lookup("not_found") """) is None

        # Trace parents to None
        assert self.i.walk(""" __env.parent.parent.parent.parent """) is None

    def test_ast_primitives(self):
        assert self.i.walk(""" quote if True then 2 else 3 end end """) == (Ident("__core_if_macro"), [True, 2, [], [3]])
        assert self.i.walk(""" Expr(Ident("__core_if"), [True, 2, 3]) """) == (Ident("__core_if"), [True, 2, 3])
        assert self.i.walk(""" eval_expr(Expr(Ident("__core_if"), [True, 2, 3])) """) == 2
        assert self.i.walk(""" eval_expr(Expr(Ident("__core_if_macro"), [True, 2, [], [3]])) """) == 2

        with pytest.raises(AssertionError):
            self.i.walk(""" eval_expr(Expr(Ident("if"), [True, 2, 3] """)

        assert self.i.walk(""" quote add(2, 3) end """) == (Ident("add"), [2, 3])
        assert self.i.walk(""" Expr(Ident("add"), [2, 3]) """) == (Ident("add"), [2, 3])
        assert self.i.walk(""" eval_expr(Expr(Ident("add"), [2, 3])) """) == 5

        assert self.i.walk(""" quote
            a := 2;
            b := 3;
            if a == b then a + b else a * b end
        end """) == (Ident("seq"), [(Ident("define"), [Ident("a"), 2]), (Ident("define"), [Ident("b"), 3]), (Ident("__core_if_macro"), [(Ident("equal"), [Ident("a"), Ident("b")]), (Ident("add"), [Ident("a"), Ident("b")]), [], [(Ident("mul"), [Ident("a"), Ident("b")])]])])
        assert self.i.walk("""
            Expr(Ident("seq"), [
                Expr(Ident("define"), [Ident("a"), 2]),
                Expr(Ident("define"), [Ident("b"), 3]),
                Expr(Ident("__core_if"), [
                    Expr(Ident("equal"), [Ident("a"), Ident("b")]),
                    Expr(Ident("add"), [Ident("a"), Ident("b")]),
                    Expr(Ident("mul"), [Ident("a"), Ident("b")])
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
        assert self.i.walk(""" eval_expr(
            Expr(Ident("seq"), [
                Expr(Ident("define"), [Ident("a"), 2]),
                Expr(Ident("define"), [Ident("b"), 3]),
                Expr(Ident("__core_if"), [
                    Expr(Ident("equal"), [Ident("a"), Ident("b")]),
                    Expr(Ident("add"), [Ident("a"), Ident("b")]),
                    Expr(Ident("mul"), [Ident("a"), Ident("b")])
                ])
            ])
        ) """) == 6

    def test_macro(self, capsys):
        # Basic macro (when) vs function (fwhen)
        self.i.walk("""
            defmacro when params cond, body do Expr(Ident("__core_if"), [cond, body, None]) end;
            deffunc fwhen params cond, body do if cond then body else None end end
        """)
        assert self.i.walk(""" expand(when(2 == 2, 3)) """) == (Ident("__core_if"), [(Ident("equal"), [2, 2]), 3, None])
        assert self.i.walk(""" when(2 == 2, 3) """) == 3
        assert self.i.walk(""" when(2 == 3, 4 / 0) """) is None

        assert self.i.walk(""" fwhen(2 == 2, 3) """) == 3
        with pytest.raises(ZeroDivisionError):
            self.i.walk(""" fwhen(2 == 3, 4 / 0) """)

        self.i.walk(""" defmacro mwhen params cond, body do Expr(Ident("__core_if"), [cond, body, None]) end """)
        assert self.i.walk(""" mwhen(2 == 2, 3) """) == 3
        with pytest.raises(AssertionError, match="Argument mismatch"):
            self.i.walk(""" mwhen(2 == 2) """)

        # Macro for scope
        self.i.walk("""
            defmacro mscope params body do Expr(Expr(Ident("__core_func"), [[], body]), []) end
        """)
        self.i.walk(""" a := 2; mscope(print(a); a := 3; print(a)); print(a) """)
        assert capsys.readouterr().out == "2\n3\n2\n"

        # Anaphoric if
        self.i.walk("""
            defmacro maif params cnd, thn, els do Expr(Ident("__core_scope"), [Expr(Ident("__core_if"), [
                Expr(Ident("define"), [Ident("it"), cnd]),
                thn,
                els
            ])]) end
        """)
        assert self.i.walk(""" maif(2, [True, it], [False, it]) """) == [True, 2]
        assert self.i.walk(""" maif(0, [True, it], [False, it]) """) == [False, 0]

        # and/or using aif
        self.i.walk("""
            defmacro mand params a, b do Expr(Ident("maif"), [a, b, Ident("it")]) end;
            defmacro mor params a, b do Expr(Ident("maif"), [a, Ident("it"), b]) end
        """)
        assert self.i.walk(""" mand(2, 3) """) == 3
        assert self.i.walk(""" mand(0, 3) """) == 0
        assert self.i.walk(""" mor(2, 3) """) == 2
        assert self.i.walk(""" mor(0, 3) """) == 3

        # Side effect in macro argument
        self.i.walk("""
            deffunc ftwice params x do x + x end;
            defmacro mtwice params x do Expr(Ident("add"), [x, x]) end
        """)
        self.i.walk(""" cnt := 0 """)
        assert self.i.walk(""" ftwice(cnt = cnt + 1) """) == 2
        assert self.i.walk(""" cnt """) == 1

        self.i.walk(""" cnt := 0 """)
        assert self.i.walk(""" mtwice(cnt = cnt + 1) """) == 3
        assert self.i.walk(""" cnt """) == 2

        # Variable capture (Non-hygienic)
        self.i.walk(""" defmacro capture params val do Expr(Ident("define"), [Ident("x"), val]) end """)
        self.i.walk(""" x := 1 """)
        self.i.walk(""" capture(2) """)
        assert self.i.walk(""" x """) == 2

class TestQuasiquote(TestBase):
    def test_basic(self):
        self.i.walk(""" a := 2; b := ["A", "B"] """)
        assert self.i.walk(""" quote 3 end """) == 3
        assert self.i.walk(""" quote "A" end """) == "A"
        assert self.i.walk(""" quote a end """) == Ident("a")
        assert self.i.walk(""" quote !a end """) == 2
        assert self.i.walk(""" quote !a + 2 end """) == (Ident("add"), [2, 2])
        assert self.i.walk(""" quote !(a + 2) end """) == 4

    def test_list(self):
        self.i.walk(""" a := 2; b := ["A", "B"] """)
        assert self.i.walk(""" quote [a, b] end """) == [Ident("a"), Ident("b")]
        assert self.i.walk(""" quote [!a, !b] end """) == [2, ["A", "B"]]

    def test_splicing(self):
        self.i.walk(""" a := 2; b := ["A", "B"] """)
        assert self.i.walk(""" quote [!!b] end """) == ["A", "B"]
        assert self.i.walk(""" quote [a, !!b, 2] end """) == [Ident("a"), "A", "B", 2]

    def test_nested(self):
        self.i.walk(""" a := 2 """)
        assert self.i.walk(""" quote if !a == 3 then 4 else 5 end end """) == (Ident("__core_if_macro"), [(Ident("equal"), [2, 3]), 4, [], [5]])
        assert self.i.walk(""" eval_expr(quote if !a == 3 then 4 else 5 end end) """) == 5

    def test_splicing_call(self, capsys):
        self.i.walk(""" args := [2, 3] """)
        assert self.i.walk(""" quote print(1, !!args, 4) end """) == (Ident("print"), [1, 2, 3, 4])
        self.i.walk(""" eval_expr(quote print(1, !!args, 4) end) """)
        assert capsys.readouterr().out == "1 2 3 4\n"

    def test_splicing_seq(self, capsys):
        self.i.walk(""" stmts := [quote print(2) end, quote print(3) end] """)
        seq_ast = self.i.walk(""" quote print(1); !!stmts; print(4) end """)
        self.i.walk(""" eval_expr(quote print(1); !!stmts; print(4) end) """)
        assert capsys.readouterr().out == "1\n2\n3\n4\n"

    def test_errors(self):
        with pytest.raises(AssertionError, match="Undefined variable"):
            self.i.walk(""" quote !c end """)
        with pytest.raises(AssertionError):
            self.i.walk(""" quote if end """)

class TestMacroSamples(TestBase):
    def test_when(self):
        self.i.walk("""
            when := macro cond, body do quote if !cond then !body else None end end end
        """)
        assert self.i.walk(""" expand(when(2 == 2, 3)) """) == (Ident("__core_if_macro"), [(Ident("equal"), [2, 2]), 3, [], [None]])
        assert self.i.walk(""" when(2 == 2, 3) """) == 3
        assert self.i.walk(""" when(2 == 3, 4 / 0) """) is None

    def test_fwhen_error(self):
        self.i.walk("""
            fwhen := func cond, body do if cond then body else None end end
        """)
        assert self.i.walk(""" fwhen(2 == 2, 3) """) == 3
        with pytest.raises(ZeroDivisionError):
            self.i.walk(""" fwhen(2 == 3, 4 / 0) """)

    def test_deffunc_macro(self):
        self.i.walk("""
            mdeffunc := macro name, params_, body do
                quote !name := func !!params_ do !body end end
            end
        """)
        self.i.walk(""" mdeffunc(myadd, [a, b], a + b) """)
        assert self.i.walk(""" myadd(2, 3) """) == 5

    def test_defmacro_macro(self):
        self.i.walk("""
            mdefmacro := macro name, params_, body do
                quote !name := macro !!params_ do !body end end
            end
        """)
        self.i.walk(""" mdefmacro(when, [cond, body], quote if !cond then !body else None end end) """)
        assert self.i.walk(""" when(2 == 2, 3) """) == 3
        assert self.i.walk(""" when(2 == 3, 4 / 0) """) is None
        with pytest.raises(AssertionError, match="Argument mismatch"):
            self.i.walk(""" when(2 == 2) """)

    def test_mscope(self, capsys):
        self.i.walk(""" mscope := macro body do quote func do !body end () end end """)
        self.i.walk(""" a := 2; mscope(print(a); a := 3; print(a)); print(a) """)
        assert capsys.readouterr().out == "2\n3\n2\n"

    def test_anaphoric_if_and_or(self):
        self.i.walk("""
            maif := macro cnd, thn, els do
                quote if it := !cnd then !thn else !els end end
            end
        """)
        assert self.i.walk(""" maif(2, [True, it], [False, it]) """) == [True, 2]
        assert self.i.walk(""" maif(0, [True, it], [False, it]) """) == [False, 0]

        self.i.walk(""" mand := macro a, b do quote maif(!a, !b, it) end end """)
        self.i.walk(""" mor := macro a, b do quote maif(!a, it, !b) end end """)

        assert self.i.walk(""" mand(2, 3) """) == 3
        assert self.i.walk(""" mand(0, 3) """) == 0
        assert self.i.walk(""" mor(2, 3) """) == 2
        assert self.i.walk(""" mor(0, 3) """) == 3

        with pytest.raises(AssertionError, match="Undefined variable"):
             self.i.walk(""" expand(expand(mand(2, 3))) """)

    def test_side_effect_macro(self):
        self.i.walk("""
            deffunc ftwice params x do x + x end;
            mtwice := macro x do quote add(!x, !x) end end
        """)
        self.i.walk(""" cnt := 0 """)
        assert self.i.walk(""" ftwice(cnt = cnt + 1) """) == 2
        assert self.i.walk(""" cnt """) == 1
        self.i.walk(""" cnt := 0 """)
        assert self.i.walk(""" mtwice(cnt = cnt + 1) """) == 3
        assert self.i.walk(""" cnt """) == 2

    def test_capture(self):
        self.i.walk(""" capture := macro val do quote x := !val end end """)
        self.i.walk(""" x := 1 """)
        self.i.walk(""" capture(2) """)
        assert self.i.walk(""" x """) == 2

    def test_call_by_name(self):
        self.i.walk("""
            call_by_name := macro name_str, *args do
                quote (!Ident(quote !name_str end))(!!args) end
            end
        """)
        assert self.i.walk(""" call_by_name("add", 2, 3) """) == 5
        assert self.i.walk(""" call_by_name("sub", 10, 4) """) == 6

class TestCustomSyntax(TestBase):
    def test_when(self):
        self.i.walk("""
            _when := macro cond, body do quote if !cond then !body else None end end end
            #rule {when: [_when, EXPR, do, EXPR, end]}
        """)
        assert self.i.walk(""" expand(_when(2 == 2, 3)) """) == (Ident("__core_if_macro"), [(Ident("equal"), [2, 2]), 3, [], [None]])
        assert self.i.walk(""" _when(2 == 2, 3) """) == 3
        assert self.i.walk(""" _when(2 == 3, 4 / 0) """) is None

        assert self.i.walk(""" expand(when 2 == 2 do 3 end ) """) == (Ident("__core_if_macro"), [(Ident("equal"), [2, 2]), 3, [], [None]])
        assert self.i.walk(""" when 2 == 2 do 3 end """) == 3
        assert self.i.walk(""" when 2 == 3 do 4 / 0 end """) is None

        with pytest.raises(AssertionError):
            self.i.walk(""" when do 4 end """)
        with pytest.raises(AssertionError):
            self.i.walk(""" when 2 == 3 4 end """)
        with pytest.raises(AssertionError):
            self.i.walk(""" when 2 == 3 do end """)
        with pytest.raises(AssertionError):
            self.i.walk(""" when 2 == 3 do 4 """)

    def test_mfor(self):
        self.i.walk("""
            _mfor := macro var, coll, body do quotes
                __for_coll := !coll;
                __for_index := -1;
                while __for_index + 1 < len(__for_coll) do
                    __for_index = __for_index + 1;
                    scope
                        !var := __for_coll[__for_index];
                        !body
                    end
                end
            end end
            #rule {mfor: [_mfor, EXPR, in, EXPR, do, EXPR, end]}
        """)
        assert self.i.walk("""
            sum := 0;
            mfor n in [2, 3, 4] do sum = sum + n end;
            sum
        """) == 9

    def test_aif_and_or(self):
        self.i.walk("""
            _aif := macro cnd, thn, els do quotes if it := !cnd then !thn else !els end end end
            #rule {aif: [_aif, EXPR, then, EXPR, else, EXPR, end]}
        """)
        assert self.i.walk(""" aif 2 then [True, it] else [False, it] end """) == [True, 2]
        assert self.i.walk(""" aif 0 then [True, it] else [False, it] end """) == [False, 0]

        self.i.walk("""
            mand := macro a, b do quote aif !a then !b else it end end end;
            mor := macro a, b do quote aif !a then it else !b end end end
        """)
        assert self.i.walk(""" mand(2, 3) """) == 3
        assert self.i.walk(""" mand(0, 3) """) == 0
        assert self.i.walk(""" mor(2, 3) """) == 2
        assert self.i.walk(""" mor(0, 3) """) == 3

        # Test short-circuiting
        assert self.i.walk(""" mand(0, 2 / 0) """) == 0
        assert self.i.walk(""" mor(2, 2 / 0) """) == 2
        with pytest.raises(ZeroDivisionError): self.i.walk(""" mand(2, 2/0) """)
        with pytest.raises(ZeroDivisionError): self.i.walk(""" mor(0, 2/0) """)

    def test_mdeffunc_defmacro(self):
        # _mdeffunc macro definition and rule
        self.i.walk("""
            _mdeffunc := macro name, params_, body do
                quote !name := func !!params_ do !body end end
            end
            #rule {mdeffunc: [_mdeffunc, EXPR, params, EXPRS, do, EXPR, end]}
        """)
        assert self.i.walk(""" expand(_mdeffunc(myadd, [a, b], a + b)) """) == \
                (Ident("define"), [Ident("myadd"), (Ident("__core_func"), [
                   [Ident("a"), Ident("b")], (Ident("add"), [Ident("a"), Ident("b")])
                ])])
        self.i.walk(""" _mdeffunc(myadd, [a, b], a + b) """)
        assert self.i.walk(""" myadd(2, 3) """) == 5

        # mdeffunc custom syntax
        assert self.i.walk(""" expand(mdeffunc myadd2 params a, b do a + b end) """) == \
                (Ident("define"), [Ident("myadd2"), (Ident("__core_func"), [
                   [Ident("a"), Ident("b")], (Ident("add"), [Ident("a"), Ident("b")])
                ])])
        self.i.walk(""" mdeffunc myadd2 params a, b do a + b end """)
        assert self.i.walk(""" myadd2(2, 3) """) == 5

        # _defmacro macro definition and rule
        self.i.walk("""
            _defmacro := macro name, params_, body do
                quote !name := macro !!params_ do !body end end
            end
            #rule {defmacro: [_defmacro, EXPR, params, EXPRS, do, EXPR, end]}
        """)
        assert self.i.walk(""" expand(
            _defmacro(mwhen, [cond, body], Expr(Ident("__core_if"), [cond, body, None]))
        ) """) == (Ident("define"), [Ident("mwhen"), (Ident("__core_macro"), [
            [Ident("cond"), Ident("body")],
            (Ident("Expr"), [(Ident("Ident"), ["__core_if"]), [Ident("cond"), Ident("body"), None]])
        ])])

        self.i.walk(""" _defmacro(mwhen, [cond, body], quote if !cond then !body else None end end) """)
        assert self.i.walk(""" expand(mwhen(2 == 2, 3)) """) == (Ident("__core_if_macro"), [(Ident("equal"), [2, 2]), 3, [], [None]])
        assert self.i.walk(""" mwhen(2 == 2, 3) """) == 3
        assert self.i.walk(""" mwhen(2 == 3, 4 / 0) """) is None
        with pytest.raises(AssertionError, match="Argument mismatch"):
            self.i.walk(""" mwhen(2 == 2) """)

        # defmacro custom syntax
        assert self.i.walk(""" expand(
            defmacro mwhen2 params cond, body do quote if !cond then !body else None end end end
        ) """) == (Ident("define"), [Ident("mwhen2"), (Ident("__core_macro"), [
            [Ident("cond"), Ident("body")],
            (Ident("__core_quote"), [(Ident("__core_if_macro"), [(Ident("!"), [Ident("cond")]), (Ident("!"), [Ident("body")]), [], [None]])])
        ])])

        self.i.walk("""
            defmacro mwhen2 params cond, body do quote if !cond then !body else None end end end
        """)

        assert self.i.walk(""" expand(mwhen2(2 == 2, 3)) """) == (Ident("__core_if_macro"), [(Ident("equal"), [2, 2]), 3, [], [None]])
        assert self.i.walk(""" mwhen2(2 == 2, 3) """) == 3
        assert self.i.walk(""" mwhen2(2 == 3, 4 / 0) """) is None
        with pytest.raises(AssertionError, match="Argument mismatch"):
            self.i.walk(""" mwhen2(2 == 2) """)

        # Test EXPRS with zero and one parameter for mdeffunc
        self.i.walk(""" mdeffunc zero_params params do 2 end """)
        assert self.i.walk(""" zero_params() """) == 2

        self.i.walk(""" mdeffunc one_param params x do x * 2 end """)
        assert self.i.walk(""" one_param(3) """) == 6

        # Test EXPRS with zero and one parameter for defmacro
        self.i.walk(""" defmacro mzero_macro params do quote 2 end end """)
        assert self.i.walk(""" expand(mzero_macro()) """) == 2
        assert self.i.walk(""" mzero_macro() """) == 2

        self.i.walk(""" defmacro mone_macro params x do quote !x * 2 end end """)
        assert self.i.walk(""" expand(mone_macro(3)) """)
        assert self.i.walk(""" mone_macro(3) """) == 6

    def test_let_custom_rule(self):
        # Setup for let_func and let_scope
        self.i.walk("""
            _let_func := macro bindings, body do quote
                func !!map(bindings, func pair do pair[0] end) do
                    !body
                end (!!map(bindings, func pair do pair[1] end))
            end end;
            #rule {let_func: [_let_func, *[var, EXPR, be, EXPR], do, EXPR, end]}

            _let_scope := macro bindings, body do quote
                scope
                    !!map(bindings, func binding do
                        quote !binding[0] := !binding[1] end
                    end);
                    !body
                end
            end end
            #rule {let_scope: [_let_scope, *[var, EXPR, be, EXPR], do, EXPR, end]}
        """)

        # let_func tests (parallel binding)
        assert self.i.walk(""" expand(let_func var a be 4 + 5 var b be 6 do [a, b] end) """) == \
                ((Ident("__core_func"), [
                   [Ident("a"), Ident("b")],
                   [Ident("a"), Ident("b")]]
                ), [(Ident("add"), [4, 5]), 6])

        self.i.walk(""" a := 2 """)
        # 'b' is bound to the outer 'a' (2), demonstrating parallel binding
        assert self.i.walk(""" let_func var a be 3 var b be a + 4 do [a, b] end """) == [3, 6]
        assert self.i.walk(""" a """) == 2 # Outer scope is not affected

        # let_func with zero and one binding
        assert self.i.walk(""" let_func do 2 end """) == 2
        assert self.i.walk(""" let_func var a be 2 do a * 3 end """) == 6

        # let_func nested
        assert self.i.walk(""" let_func var a be 2 do let_func var b be 3 do a + b end end """) == 5

        # let_scope tests (sequential binding)
        assert self.i.walk(""" expand(let_scope var a be 4 + 5 var b be a + 6 do [a, b] end) """) == \
               (Ident('__core_scope'), [(Ident('seq'), [(Ident('define'), [Ident('a'), (Ident('add'), [4, 5])]), (Ident('define'), [Ident('b'), (Ident('add'), [Ident('a'), 6])]), [Ident('a'), Ident('b')]])])

        self.i.walk(""" a := 2 """)
        # 'b' is bound to the inner 'a' (9), demonstrating sequential binding
        assert self.i.walk(""" let_scope var a be 4 + 5 var b be a + 6 do [a, b] end """) == [9, 15]
        assert self.i.walk(""" a """) == 2 # Outer scope is not affected

        # Error cases for custom rule with repetition
        with pytest.raises(AssertionError, match="Expected be @ consume: do"):
            self.i.walk(""" let_func var a be 1 var b do a end """)

        with pytest.raises(AssertionError, match="Expected be @ consume: do"):
            self.i.walk(""" let_func var a = 1 do a end """)

    def test_optional_arguments(self):
        self.i.walk("""
            #rule {foo: [_foo, +[opt, EXPR], do, EXPR, end]}
            None
        """)

        assert self.i.ast(""" foo do 4 end """) == (Ident("_foo"), [[], 4])
        assert self.i.ast(""" foo opt 2 + 3 do 4 end """) == (Ident("_foo"), [[(Ident("add"), [2, 3])], 4])
        with pytest.raises(AssertionError, match="Expected do @ consume: opt"):
            self.i.ast(""" foo opt 2 + 3 opt 4 + 5 do 6 end """)

    def test_elif(self):
        assert self.i.ast(""" if 2 == 3 then 4 end """) == (Ident("__core_if_macro"), [(Ident("equal"), [2, 3]), 4, [], []])
        assert self.i.ast(""" if 2 == 3 then 4 else 5 end """) == (Ident("__core_if_macro"), [(Ident("equal"), [2, 3]), 4, [], [5]])
        assert self.i.ast(""" if 2 == 3 then 4 elif 2 == 2 then 5 end """) == (Ident("__core_if_macro"), [(Ident("equal"), [2, 3]), 4, [[(Ident("equal"), [2, 2]), 5]], []])
        assert self.i.ast(""" if 2 == 3 then 4 elif 2 == 2 then 5 else 6 end """) == (Ident("__core_if_macro"), [(Ident("equal"), [2, 3]), 4, [[(Ident("equal"), [2, 2]), 5]], [6]])
        assert self.i.ast(""" if 2 == 3 then 4 elif 3 == 4 then 5 elif 2 == 2 then 6 end """) == (Ident("__core_if_macro"), [(Ident("equal"), [2, 3]), 4, [[(Ident("equal"), [3, 4]), 5], [(Ident("equal"), [2, 2]), 6]], []])
        assert self.i.ast(""" if 2 == 3 then 4 elif 3 == 4 then 5 elif 2 == 2 then 6 else 7 end """) == (Ident("__core_if_macro"), [(Ident("equal"), [2, 3]), 4, [[(Ident("equal"), [3, 4]), 5], [(Ident("equal"), [2, 2]), 6]], [7]])

        assert self.i.walk(""" expand(if 2 == 3 then 4 end) """) == (Ident("__core_if"), [(Ident("equal"), [2, 3]), 4, None])
        assert self.i.walk(""" expand(if 2 == 3 then 4 else 5 end) """) == (Ident("__core_if"), [(Ident("equal"), [2, 3]), 4, 5])
        assert self.i.walk(""" expand(if 2 == 3 then 4 elif 2 == 2 then 5 end) """) == (Ident("__core_if"), [(Ident("equal"), [2, 3]), 4, (Ident("__core_if"), [(Ident("equal"), [2, 2]), 5, None])])
        assert self.i.walk(""" expand(if 2 == 3 then 4 elif 2 == 2 then 5 else 6 end) """) == (Ident("__core_if"), [(Ident("equal"), [2, 3]), 4, (Ident("__core_if"), [(Ident("equal"), [2, 2]), 5, 6])])
        assert self.i.walk(""" expand(if 2 == 3 then 4 elif 3 == 4 then 5 elif 2 == 2 then 6 end) """) == (Ident("__core_if"), [(Ident("equal"), [2, 3]), 4, (Ident("__core_if"), [(Ident("equal"), [3, 4]), 5, (Ident("__core_if"), [(Ident("equal"), [2, 2]), 6, None])])])
        assert self.i.walk(""" expand(if 2 == 3 then 4 elif 3 == 4 then 5 elif 2 == 2 then 6 else 7 end) """) == (Ident("__core_if"), [(Ident("equal"), [2, 3]), 4, (Ident("__core_if"), [(Ident("equal"), [3, 4]), 5, (Ident("__core_if"), [(Ident("equal"), [2, 2]), 6, 7])])])

        # Test mif evaluation
        assert self.i.walk(""" if 2 == 3 then 4 end """) is None
        assert self.i.walk(""" if 2 == 3 then 4 else 5 end """) == 5
        assert self.i.walk(""" if 2 == 3 then 4 elif 2 == 2 then 5 end """) == 5
        assert self.i.walk(""" if 2 == 3 then 4 elif 2 == 2 then 5 else 6 end """) == 5
        assert self.i.walk(""" if 2 == 3 then 4 elif 3 == 4 then 5 elif 2 == 2 then 6 end """) == 6
        assert self.i.walk(""" if 2 == 3 then 4 elif 3 == 4 then 5 elif 2 == 2 then 6 else 7 end """) == 6

        # Test mif error cases
        with pytest.raises(AssertionError, match="Expected then @ consume: 4"):
            self.i.ast(""" if then 4 end """)
        with pytest.raises(AssertionError, match="Expected then @ consume: 4"):
            self.i.ast(""" if 2 == 3 4 end """)
        with pytest.raises(AssertionError, match="Expected end @ consume"):
            self.i.ast(""" if 2 == 3 then 4 else end """)
        with pytest.raises(AssertionError, match="Expected end @ consume: else"):
            self.i.ast(""" if 2 == 3 then 4 else 5 else 6 end """)

if __name__ == "__main__":
    pytest.main([__file__])
