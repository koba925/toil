import pytest
from toil import Interpreter, Sym


class TestBase:
    @pytest.fixture(autouse=True)
    def set_interpreter(self):
        self.i = Interpreter().init_env().stdlib()


class TestScan(TestBase):
    def test_number(self):
        assert self.i.scan("""2""") == [2, Sym("$EOF")]
        assert self.i.scan(""" 3 """) == [3, Sym("$EOF")]
        assert self.i.scan(""" \t4\n5\n """) == [4, 5, Sym("$EOF")]
        assert self.i.scan("""  """) == [Sym("$EOF")]

    def test_operator(self):
        assert self.i.scan(""" 1 + 2 """) == [1, Sym("+"), 2, Sym("$EOF")]
        assert self.i.scan(""" 1 * 2 """) == [1, Sym("*"), 2, Sym("$EOF")]
        assert self.i.scan(""" 1 / 2 """) == [1, Sym("/"), 2, Sym("$EOF")]

    def test_bool_none_ident(self):
        assert self.i.scan(""" True """) == [True, Sym("$EOF")]
        assert self.i.scan(""" False """) == [False, Sym("$EOF")]
        assert self.i.scan(""" None """) == [None, Sym("$EOF")]
        assert self.i.scan(""" a """) == [Sym("a"), Sym("$EOF")]

    def test_define_assign(self):
        assert self.i.scan(""" a := 2 """) == [Sym("a"), Sym(":="), 2, Sym("$EOF")]
        assert self.i.scan(""" a = 2 """) == [Sym("a"), Sym("="), 2, Sym("$EOF")]

    def test_string(self):
        assert self.i.scan(""" 'hello' """) == ["hello", Sym("$EOF")]
        assert self.i.scan(""" "hello" """) == ["hello", Sym("$EOF")]
        assert self.i.scan(r""" "a\nb" """) == ["a\nb", Sym("$EOF")]

class TestParse(TestBase):
    def test_comparison(self):
        assert self.i.ast(""" 2 == 3 == 4 """) == (
            Sym("equal"), [(Sym("equal"), [2, 3]), 4]
        )

    def test_add_sub(self):
        assert self.i.ast(""" 2 + 3 """) == (Sym("add"), [2, 3])
        assert self.i.ast(""" 2 - 3 """) == (Sym("sub"), [2, 3])
        assert self.i.ast(""" 2 + 3 * 4 """) == (Sym("add"), [2, (Sym("mul"), [3, 4])])
        assert self.i.ast(""" 2 * 3 + 4 """) == (Sym("add"), [(Sym("mul"), [2, 3]), 4])

    def test_mul_div(self):
        assert self.i.ast(""" 2 * 3 """) == (Sym("mul"), [2, 3])
        assert self.i.ast(""" 2 / 3 """) == (Sym("div"), [2, 3])
        assert self.i.ast(""" 2 * 3 / 4 """) == (Sym("div"), [(Sym("mul"), [2, 3]), 4])

    def test_not(self):
        assert self.i.ast(""" not True """) == (Sym("not"), [True])
        assert self.i.ast(""" not not False """) == (Sym("not"), [(Sym("not"), [False])])

    def test_and_or(self):
        assert self.i.ast(""" True and False """) == (Sym('if'), True, False, True)
        assert self.i.ast(""" True or False """) == (Sym('if'), True, True, False)
        assert self.i.ast(""" True or False and True """) == (Sym('if'), (Sym('if'), True, True, False), True, (Sym('if'), True, True, False))
        assert self.i.ast(""" a := False and not False """) == (Sym('define'), [Sym('a'), (Sym('if'), False, (Sym('not'), [False]), False)])
        assert self.i.ast(""" a := False or not False """) == (Sym('define'), [Sym('a'), (Sym('if'), False, False, (Sym('not'), [False]))])

    def test_neg(self):
        assert self.i.ast(""" -2 """) == (Sym("neg"), [2])
        assert self.i.ast(""" --3 """) == (Sym("neg"), [(Sym("neg"), [3])])

    def test_number(self):
        assert self.i.ast(""" 2 """) == 2

    def test_bool_none(self):
        assert self.i.ast(""" True """) is True
        assert self.i.ast(""" False """) is False
        assert self.i.ast(""" None """) is None

    def test_paren(self):
        assert self.i.ast(""" (1 + 2) """) == (Sym("add"), [1, 2])
        assert self.i.ast(""" (1 + 2) * 3 """) == (Sym("mul"), [(Sym("add"), [1, 2]), 3])

    def test_string(self):
        assert self.i.ast(""" 'hello' """) == "hello"
        assert self.i.ast(""" "hello" """) == "hello"
        assert self.i.ast(r""" "a\nb" """) == "a\nb"

    def test_seq(self):
        assert self.i.ast(""" 2; 3 """) == (Sym("seq"), [2, 3])
        assert self.i.ast(""" not True; False """) == (Sym("seq"), [(Sym("not"), [True]), False])

    def test_if(self):
        assert self.i.ast(""" if True then 2 else 3 end """) == (
            Sym("if"), True, 2, 3)
        assert self.i.ast(""" if not True then 2 + 3 else 4; 5 end """) == (
            Sym("if"), (Sym('not'), [True]), (Sym('add'), [2, 3]), (Sym("seq"), [4, 5]))

        assert self.i.ast(""" if 1 then 10 end """) == (Sym('if'), 1, 10, None)
        assert self.i.ast(""" if 1 then 10 else 20 end """) == (Sym('if'), 1, 10, 20)
        assert self.i.ast(""" if 1 then 10 elif 2 then 20 end """) == (Sym('if'), 1, 10, (Sym('if'), 2, 20, None))
        assert self.i.ast(""" if 1 then 10 elif 2 then 20 else 30 end """) == (Sym('if'), 1, 10, (Sym('if'), 2, 20, 30))
        assert self.i.ast(""" if 1 then 10 elif 2 then 20 elif 3 then 30 else 40 end """) == (Sym('if'), 1, 10, (Sym('if'), 2, 20, (Sym('if'), 3, 30, 40)))

    def test_define(self):
        assert self.i.ast(""" a := not True """) == (Sym("define"), [Sym("a"), (Sym("not"), [True])])
        assert self.i.ast(""" a := b := 2 """) == (Sym("define"), [Sym("a"), (Sym("define"), [Sym("b"), 2])])

    def test_assign(self):
        assert self.i.ast(""" a = 1 """) == (Sym("assign"), [Sym("a"), 1])
        assert self.i.ast(""" a = b = 2 """) == (Sym("assign"), [Sym("a"), (Sym("assign"), [Sym("b"), 2])])
        assert self.i.ast(""" a := b = 2 """) == (Sym("define"), [Sym("a"), (Sym("assign"), [Sym("b"), 2])])
        assert self.i.ast(""" a := b = c := 3 """) == (Sym("define"), [Sym("a"), (Sym("assign"), [Sym("b"), (Sym("define"), [Sym("c"), 3])])])

    def test_array_assign(self):
        assert self.i.ast(""" a[0] = 1 """) == (Sym("assign"), [(Sym("index"), [Sym("a"), 0]), 1])
        assert self.i.ast(""" a[1][2] = 3 """) == (Sym("assign"), [(Sym("index"), [(Sym("index"), [Sym("a"), 1]), 2]), 3])
        assert self.i.ast(""" a[0] = b[1] = 2 """) == (Sym("assign"), [(Sym("index"), [Sym("a"), 0]), (Sym("assign"), [(Sym("index"), [Sym("b"), 1]), 2])])

    def test_while(self):
        assert self.i.ast(""" while i < 10 do i = i + 1 end """) == (Sym('while'), (Sym('less'), [Sym('i'), 10]), (Sym('assign'), [Sym('i'), (Sym('add'), [Sym('i'), 1])]))

    def test_call(self):
        assert self.i.ast(""" print() """) == (Sym("print"), [])
        assert self.i.ast(""" neg(2) """) == (Sym("neg"), [2])
        assert self.i.ast(""" add(2, mul(3, 4)) """) == (Sym("add"), [2, (Sym("mul"), [3, 4])])

    def test_index(self):
        assert self.i.ast(""" a[0] """) == (Sym("index"), [Sym("a"), 0])
        assert self.i.ast(""" a[1][2] """) == (Sym("index"), [(Sym("index"), [Sym("a"), 1]), 2])

    def test_func(self):
        assert self.i.ast(""" func do 2 end """) == (Sym("func"), [], 2)
        assert self.i.ast(""" func a do a + 2 end """) == (Sym("func"), [Sym("a")], (Sym("add"), [Sym("a"), 2]))
        assert self.i.ast(""" func a, b do a + b end """) == (Sym("func"), [Sym("a"), Sym("b")], (Sym("add"), [Sym("a"), Sym("b")]))

        with pytest.raises(AssertionError):
            self.i.ast(""" func a 2 end """)
        with pytest.raises(AssertionError):
            self.i.ast(""" func a do 2 """)

    def test_deffunc(self):
        assert self.i.ast(""" deffunc two params do 2 end """) == (
            Sym('define'), [Sym('two'), (Sym('func'), [], 2)])
        assert self.i.ast("""
             deffunc add2 params a do
                a + 2
             end
        """) == (Sym('define'), [Sym('add2'), (Sym('func'), [Sym('a')], (Sym('add'), [Sym('a'), 2]))])
        assert self.i.ast("""
            deffunc sum params a, b, c do
                a + b + c
            end
        """) == (Sym('define'), [Sym('sum'), (Sym('func'), [Sym('a'), Sym('b'), Sym('c')], (Sym('add'), [(Sym('add'), [Sym('a'), Sym('b')]), Sym('c')]))])

        with pytest.raises(AssertionError):
            self.i.ast(""" deffunc add2 a do a + 2 end """)
        with pytest.raises(AssertionError):
            self.i.ast(""" deffunc add2 params a a + 2 end """)
        with pytest.raises(AssertionError):
            self.i.ast(""" deffunc 2 params do 3 end """)

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
        self.i.evaluate((Sym("seq"), [
            (Sym("print"), [2]),
            (Sym("print"), [3])
        ]))
        assert capsys.readouterr().out == "2\n3\n"

    def test_evaluate_if(self):
        assert self.i.evaluate((Sym("if"), True, 2, 3)) == 2
        assert self.i.evaluate((Sym("if"), False, 2, 3)) == 3
        assert self.i.evaluate((Sym("if"), (Sym("if"), True, True, False), 2, 3)) == 2
        assert self.i.evaluate((Sym("if"), True, (Sym("if"), True, 2, 3), 4)) == 2
        assert self.i.evaluate((Sym("if"), False, 2, (Sym("if"), False, 3, 4))) == 4

    def test_evaluate_if_scope(self):
        # Variable defined inside if should not leak
        self.i.evaluate((Sym("if"), True, (Sym("define"), [Sym("inner_if"), 1]), 2))
        with pytest.raises(AssertionError):
            self.i.evaluate(Sym("inner_if"))

    def test_evaluate_variable(self):
        assert self.i.evaluate((Sym("define"), [Sym("a"), 2])) == 2
        assert self.i.evaluate(Sym("a")) == 2

        assert self.i.evaluate((Sym("define"), [Sym("b"), True])) == True
        assert self.i.evaluate((Sym("if"), Sym("b"), 2, 3)) == 2

        assert self.i.evaluate((Sym("define"), [Sym("c"), (Sym("if"), False, 2, 3)])) == 3
        assert self.i.evaluate(Sym("c")) == 3

    def test_evaluate_undefined_variable(self):
        with pytest.raises(AssertionError):
            self.i.evaluate(Sym("a"))

    def test_evaluate_assign(self):
        self.i.evaluate((Sym("define"), [Sym("a"), 1]))
        assert self.i.evaluate((Sym("assign"), [Sym("a"), 2])) == 2
        assert self.i.evaluate(Sym("a")) == 2
        with pytest.raises(AssertionError):
            self.i.evaluate((Sym("assign"), [Sym("b"), 2]))

    def test_evaluate_scope(self, capsys):
        self.i.evaluate((Sym("define"), [Sym("a"), 2]))
        assert self.i.evaluate(Sym("a")) == 2
        assert self.i.evaluate((Sym("scope"), Sym("a"))) == 2

        assert self.i.evaluate((Sym("scope"), (Sym("seq"), [
            (Sym("print"), [Sym("a")]),
            (Sym("define"), [Sym("a"), 3]),
            (Sym("print"), [Sym("a")]),
            (Sym("define"), [Sym("b"), 4]),
            (Sym("print"), [Sym("b")]),
            Sym("b")
        ]))) == 4
        assert capsys.readouterr().out == "2\n3\n4\n"

        assert self.i.evaluate(Sym("a")) == 2

        with pytest.raises(AssertionError):
            self.i.evaluate(Sym("b"))

    def test_builtin_functions(self, capsys):
        assert self.i.evaluate((Sym("add"), [2, 3])) == 5
        assert self.i.evaluate((Sym("sub"), [5, 3])) == 2
        assert self.i.evaluate((Sym("mul"), [2, 3])) == 6

        assert self.i.evaluate((Sym("equal"), [2, 2])) is True
        assert self.i.evaluate((Sym("equal"), [2, 3])) is False

        assert self.i.evaluate((Sym("add"), [2, (Sym("mul"), [3, 4])])) == 14

        self.i.evaluate((Sym("print"), [2, 3]))
        assert capsys.readouterr().out == "2 3\n"

        self.i.evaluate((Sym("print"), [(Sym("add"), [5, 5])]))
        assert capsys.readouterr().out == "10\n"

    def test_user_func(self):
        self.i.evaluate((Sym("define"), [Sym("add2"), (Sym("func"), [Sym("a")],
            (Sym("add"), [Sym("a"), 2])
        )]))
        assert self.i.evaluate((Sym("add2"), [3])) == 5

        self.i.evaluate((Sym("define"), [Sym("sum3"), (Sym("func"),[Sym("a"), Sym("b"), Sym("c")],
            (Sym("add"), [Sym("a"), (Sym("add"), [Sym("b"), Sym("c")])])
        )]))
        assert self.i.evaluate((Sym("sum3"), [2, 3, 4])) == 9

    def test_recursion(self):
        self.i.evaluate((Sym("define"), [Sym("fac"), (Sym("func"),[Sym("n")],
            (Sym("if"), (Sym("equal"), [Sym("n"), 1]),
                1,
                (Sym("mul"), [Sym("n"), (Sym("fac"), [(Sym("sub"), [Sym("n"), 1])])])
            )
        )]))
        assert self.i.evaluate((Sym("fac"), [1])) == 1
        assert self.i.evaluate((Sym("fac"), [3])) == 6
        assert self.i.evaluate((Sym("fac"), [5])) == 120

    def test_scope_leak(self):
        self.i.evaluate((Sym("define"), [Sym("x"), 2]))
        self.i.evaluate((Sym("define"), [Sym("f"), (Sym("func"), [Sym("x")], 3)]))
        self.i.evaluate((Sym("f"), [4]))
        assert self.i.evaluate(Sym("x")) == 2

    def test_closure(self):
        self.i.evaluate((Sym("define"), [Sym("x"), 2]))
        self.i.evaluate((Sym("define"), [Sym("return_x"), (Sym("func"), [], Sym("x"))]))
        assert self.i.evaluate((Sym("return_x"), [])) == 2
        assert self.i.evaluate((Sym("scope"), (Sym("seq"), [
            (Sym("define"), [Sym("x"), 3]),
            (Sym("return_x"), [])
        ]))) == 2
        assert self.i.evaluate(Sym("x")) == 2

    def test_adder(self):
        self.i.evaluate((Sym("define"), [Sym("make_adder"), (Sym("func"), [Sym("n")],
            (Sym("func"), [Sym("m")], (Sym("add"), [Sym("n"), Sym("m")])))])
        )
        self.i.evaluate((Sym("define"), [Sym("add2"), (Sym("make_adder"), [2])]))
        self.i.evaluate((Sym("define"), [Sym("add3"), (Sym("make_adder"), [3])]))

        assert self.i.evaluate((Sym("add2"), [3])) == 5
        assert self.i.evaluate((Sym("add3"), [4])) == 7

    def test_shadowing(self):
        self.i.evaluate((Sym("define"), [Sym("make_shadow"), (Sym("func"), [Sym("x")],
            (Sym("func"), [],
                (Sym("seq"), [
                    (Sym("define"), [Sym("x"), 3]),
                    Sym("x")
                ])
            )
        )]))
        self.i.evaluate((Sym("define"), [Sym("g"), (Sym("make_shadow"), [2])]))
        assert self.i.evaluate((Sym("g"), [])) == 3

    def test_array(self):
        self.i.evaluate((Sym("define"), [Sym("a"), [1, 2, 3]]))
        assert self.i.evaluate(Sym("a")) == [1, 2, 3]
        assert self.i.evaluate((Sym("index"), [Sym("a"), 0])) == 1
        assert self.i.evaluate((Sym("index"), [Sym("a"), 2])) == 3

        self.i.evaluate((Sym("assign"), [(Sym("index"), [Sym("a"), 1]), 4]))
        assert self.i.evaluate(Sym("a")) == [1, 4, 3]

    def test_array_nested(self):
        self.i.evaluate((Sym("define"), [Sym("a"), [
            [1, 2],
            [3, 4]
        ]]))
        assert self.i.evaluate((Sym("index"), [(Sym("index"), [Sym("a"), 0]), 1])) == 2
        assert self.i.evaluate((Sym("index"), [(Sym("index"), [Sym("a"), 1]), 0])) == 3

        self.i.evaluate((Sym("assign"), [(Sym("index"), [(Sym("index"), [Sym("a"), 1]), 0]), 5]))
        assert self.i.evaluate((Sym("index"), [(Sym("index"), [Sym("a"), 1]), 0])) == 5

    def test_array_push_pop(self):
        self.i.evaluate((Sym("define"), [Sym("a"), [1, 2]]))
        self.i.evaluate((Sym("push"), [Sym("a"), 3]))
        assert self.i.evaluate(Sym("a")) == [1, 2, 3]
        assert self.i.evaluate((Sym("pop"), [Sym("a")])) == 3
        assert self.i.evaluate(Sym("a")) == [1, 2]

    def test_array_funcs(self):
        self.i.evaluate((Sym("define"), [Sym("a"), [1, 2, 3]]))
        assert self.i.evaluate((Sym("len"), [Sym("a")])) == 3
        assert self.i.evaluate((Sym("slice"), [Sym("a"), 1, None])) == [2, 3]
        assert self.i.evaluate((Sym("slice"), [Sym("a"), 1, 2])) == [2]
        assert self.i.evaluate((Sym("slice"), [Sym("a"), None, 2])) == [1, 2]
        assert self.i.evaluate((Sym("slice"), [Sym("a"), None, None])) == [1, 2, 3]

    def test_array_error(self):
        self.i.evaluate((Sym("define"), [Sym("a"), [1, 2]]))

        with pytest.raises(AssertionError, match="Illegal indexing"):
            self.i.evaluate((Sym("assign"), [(Sym("index"), [None, 0]), 1]))

        with pytest.raises(AssertionError, match="Illegal indexing"):
            self.i.evaluate((Sym("assign"), [(Sym("index"), [Sym("a"), None]), 1]))

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

    def test_and_or(self, capsys):
        assert self.i.go(""" True and False """) is False
        assert self.i.go(""" True or False """) is True
        assert self.i.go(""" False and True """) is False
        assert self.i.go(""" False or True """) is True

        assert self.i.go(""" True and 2 """) == 2
        assert self.i.go(""" 0 and 2 / 0 """) == 0
        assert self.i.go(""" False or 2 """) == 2
        assert self.i.go(""" 1 or 2 / 0 """) == 1

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
        assert self.i.go(""" if False then 2 else 3 end """) == 3

        assert self.i.go(""" if not True then 2 + 3 else 4; 5 end """) == 5

        assert self.i.go(""" if True then 2 end """) == 2
        assert self.i.go(""" if False then 2 end """) is None

        assert self.i.go(""" if False then 2 elif True then 3 else 4 end """) == 3
        assert self.i.go(""" if False then 2 elif False then 3 else 4 end """) == 4

        with pytest.raises(AssertionError):
            self.i.go(""" if True then 2 else 3 """)
        with pytest.raises(AssertionError):
            self.i.go(""" if True else 2 end """)

    def test_if_scope(self):
        # Definition inside if should not leak
        with pytest.raises(AssertionError, match="Undefined variable"):
             self.i.go(""" if True then a := 1 else a := 2 end; a """)

        # Assignment to existing variable should work (via parent scope lookup)
        assert self.i.go(""" a := False; if True then a = True end; a """) == True

        # Variable defined in condition should be visible in branches but not outside
        assert self.i.go(""" if (a := 2) == 2 then a + 1 else 0 end """) == 3
        assert self.i.go(""" a """) == True # 'a' is still True from previous test

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

    def test_while(self):
        assert self.i.go("""
            sum := i := 0;
            while i < 10 do
                sum = sum + i;
                i = i + 1
            end;
            sum
        """) == 45

        assert self.i.go(""" while False do 1 end """) is None
        assert self.i.go(""" i := 0; while False do i = 1 end; i """) == 0

        with pytest.raises(AssertionError):
            self.i.go(""" while do i = i + 1 end """)
        with pytest.raises(AssertionError):
            self.i.go(""" while i < 10 i = i + 1 end """)
        with pytest.raises(AssertionError):
            self.i.go(""" while i < 10 do i = i + 1 """)

    def test_for(self, capsys):
        assert self.i.go("""
            sum := 0;
            for n in [2, 3, 4] do
                sum = sum + n
            end;
            sum """) == 9

        assert self.i.go(""" for i in [] do print("never") end; "ok" """) == "ok"
        assert capsys.readouterr().out == ""

        assert self.i.go("""
            for i in [2, 3, 4] do
                if i == 3 then break(i * 10) end
            end
        """) == 30

        self.i.go("""
            for i in [2, 3, 4] do
                if i == 3 then continue() end;
                print(i)
            end
        """)
        assert capsys.readouterr().out == "2\n4\n"

        self.i.go("""
            funcs := [];
            for i in [2, 3, 4] do
                funcs.push(func do i end)
            end;
            print(funcs[0](), funcs[1](), funcs[2]())
        """)
        assert capsys.readouterr().out == "2 3 4\n"

        self.i.go("""
            keys := ["a", "b", "c"];
            values := [2, 3, 4];
            for [k, v] in zip(keys, values) do
                print(k, v)
            end
        """)
        assert capsys.readouterr().out == "a 2\nb 3\nc 4\n"

        self.i.go("""
            dic := { "a": 2, "b": 3, "c": 4 };
            for [k, v] in dic.items() do
                print(k, v)
            end
        """)
        assert capsys.readouterr().out == "a 2\nb 3\nc 4\n"

        with pytest.raises(AssertionError, match="Undefined variable"):
            self.i.go(""" for i in [2] do 1 end; i """)

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

    def test_deffunc(self):
        self.i.go(""" deffunc two params do 2 end """)
        assert self.i.go(""" two() """) == 2
        self.i.go(""" deffunc add2 params a do a + 2 end """)
        assert self.i.go(""" add2(3) """) == 5
        self.i.go(""" deffunc sum params a, b, c do a + b + c end """)
        assert self.i.go(""" sum(2, 3, 4) """) == 9

    def test_fac(self):
        assert self.i.go("""
            deffunc fac params n do
                if n == 1 then 1 else n * fac(n - 1) end
            end;
            fac(5)
        """) == 120

    def test_fib(self):
        self.i.go("""
            deffunc fib params n do
                if n == 0 then 0
                elif n == 1 then 1
                else fib(n - 1) + fib(n - 2)
                end
            end
        """)
        assert self.i.go(""" fib(0) """) == 0
        assert self.i.go(""" fib(1) """) == 1
        assert self.i.go(""" fib(7) """) == 13
        assert self.i.go(""" fib(9) """) == 34

    def test_gcd_recursive(self):
        assert self.i.go("""
            deffunc gcd params a, b do
                if a == 0 then b else gcd(b % a, a) end
            end;
            gcd(24, 36)
        """) == 12

    def test_mutual_recursion(self):
        self.i.go("""
            deffunc is_even params n do if n == 0 then True else is_odd(n - 1) end end;
            deffunc is_odd params n do if n == 0 then False else is_even(n - 1) end end
        """)
        assert self.i.go(""" is_even(10) """) is True
        assert self.i.go(""" is_odd(10) """) is False

    def test_gcd_iterative(self):
        assert self.i.go("""
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
            self.i.go("""  """)

    def test_extra_token(self):
        with pytest.raises(AssertionError):
            self.i.go(""" 7 8 """)

    def test_array(self):
        assert self.i.go(""" [] """) == []
        assert self.i.go(""" [2 + 3] """) == [5]
        assert self.i.go(""" [2][0] """) == 2
        assert self.i.go(""" [2, 3, [4, 5]] """) == [2, 3, [4, 5]]

        self.i.go(""" a := [2, 3, [4, 5]] """)
        assert self.i.go(""" a[2][0] """) == 4
        assert self.i.go(""" a[2][-1] """) == 5

        self.i.go(""" b := [2, 3, [4, 5]] """)
        self.i.go(""" b[0] = 6 """)
        assert self.i.go(""" b[0] """) == 6
        self.i.go(""" b[2][1] = 7 """)
        assert self.i.go(""" b[2][1] """) == 7
        assert self.i.go(""" b """) == [6, 3, [4, 7]]

        self.i.go(""" c := func do [add, sub] end """)
        assert self.i.go(""" c()[0](2, 3) """) == 5

        self.i.go(""" d := [2, 3, 4] """)
        assert self.i.go(""" len(d) """) == 3
        assert self.i.go(""" slice(d, 1, None) """) == [3, 4]
        assert self.i.go(""" slice(d, 1, 2) """) == [3]
        assert self.i.go(""" slice(d, None, 2) """) == [2, 3]
        assert self.i.go(""" slice(d, None, None) """) == [2, 3, 4]
        assert self.i.go(""" push(d, 5) """) is None
        assert self.i.go(""" d """) == [2, 3, 4, 5]
        assert self.i.go(""" pop(d) """) == 5
        assert self.i.go(""" d """) == [2, 3, 4]

        assert self.i.go(""" [2, 3] + [4, 5] """) == [2, 3, 4, 5]
        assert self.i.go(""" [2, 3] * 3 """) == [2, 3, 2, 3, 2, 3]

        self.i.go(""" e := [1] """)
        with pytest.raises(AssertionError):
            self.i.go(""" e[None] = 2 """)
        with pytest.raises(AssertionError):
            self.i.go(""" None[2] = 3 """)

    def test_stdlib(self):
        assert self.i.go(""" a := range(2, 10) """) == [2, 3, 4, 5, 6, 7, 8, 9]
        assert self.i.go(""" first(a) """) == 2
        assert self.i.go(""" rest(a) """) == [3, 4, 5, 6, 7, 8, 9]
        assert self.i.go(""" last(a) """) == 9
        assert self.i.go(""" map(a, func n do n * 2 end) """) == [4, 6, 8, 10, 12, 14, 16, 18]
        assert self.i.go(""" filter(a, func n do n % 2 == 0 end) """) == [2, 4, 6, 8]
        assert self.i.go(""" reduce(a, add, 0) """) == 44
        assert self.i.go(""" reverse(a) """) == [9, 8, 7, 6, 5, 4, 3, 2]
        assert self.i.go(""" zip(a, [4, 5, 6]) """) == [[2, 4], [3, 5], [4, 6]]
        assert self.i.go(""" enumerate(a) """) == [[0, 2], [1, 3], [2, 4], [3, 5], [4, 6], [5, 7], [6, 8], [7, 9]]

    def test_array_sieve(self):
        assert self.i.go("""
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
        assert self.i.go(""" 'Hello, world!' """) == "Hello, world!"
        assert self.i.go(""" '
multi
line
text
'       """) == "\nmulti\nline\ntext\n"
        assert self.i.go(""" 'Hello, world!'[1] """) == "e"
        assert self.i.go(""" 'Hello, ' + 'world!' """) == "Hello, world!"
        assert self.i.go(""" 'Hello, ' * 3 """) == "Hello, Hello, Hello, "

        assert self.i.go(""" len('Hello, world!') """) == 13
        assert self.i.go(""" first('Hello, world!') """) == "H"
        assert self.i.go(""" rest('Hello, world!') """) == "ello, world!"
        assert self.i.go(""" last('Hello, world!') """) == "!"

        assert self.i.go(""" join(['H', 'e', 'l', 'l', 'o'], ' ') """) == "H e l l o"
        assert self.i.go(""" ord('A') """) == 65
        assert self.i.go(""" chr(65) """) == "A"

        assert self.i.go(""" "Hello, world!" """) == "Hello, world!"
        assert self.i.go(r""" "Hello,\nworld!" """) == "Hello,\nworld!"
        assert self.i.go(r""" "Hello,\\world!" """) == "Hello,\\world!"
        assert self.i.go(r""" "Hello,\"world!" """) == 'Hello,"world!'

    def test_destructuring_assignment(self):
        self.i.go(""" [a, b] := [2, 3] """)
        assert self.i.go(""" a """) == 2
        assert self.i.go(""" b """) == 3

        self.i.go(""" [a, [b, c]] := [2, [3, 4]] """)
        assert self.i.go(""" a """) == 2
        assert self.i.go(""" b """) == 3
        assert self.i.go(""" c """) == 4

        self.i.go(""" [a, *b] := [2] """)
        assert self.i.go(""" a """) == 2
        assert self.i.go(""" b """) == []

        self.i.go(""" [a, *b] := [2, 3, 4] """)
        assert self.i.go(""" a """) == 2
        assert self.i.go(""" b """) == [3, 4]

        self.i.go(""" [*a] := [2, 3] """)
        assert self.i.go(""" a """) == [2, 3]

        with pytest.raises(AssertionError):
            self.i.go(""" [*b, a] := [2] """)

    def test_argument_destructuring(self, capsys):
        self.i.go(""" deffunc f params a, [b, c] do [a, b, c] end """)
        assert self.i.go(""" f(2, [3, 4]) """) == [2, 3, 4]

        self.i.go(""" deffunc g params *a do a end""")
        assert self.i.go(""" g() """) == []
        assert self.i.go(""" g(2 + 3) """) == [5]
        assert self.i.go(""" g(2, 3, 4) """) == [2, 3, 4]

        self.i.go(""" deffunc h params a, *b do [a, b] end """)
        assert self.i.go(""" h(2 + 3) """) == [5, []]
        assert self.i.go(""" h(2, 3, 4) """) == [2, [3, 4]]
        with pytest.raises(AssertionError):
            self.i.go(""" h() """)

        self.i.go(""" deffunc i params *a, b do [a, b] end """)
        with pytest.raises(AssertionError):
            self.i.go(""" i(2, 3, 4) """)

    def test_match(self):
        self.i.go("""
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
        assert self.i.go(""" f(2) """) == "two"
        assert self.i.go(""" f("two") """) == 3
        assert self.i.go(""" f([2]) """) == 2
        assert self.i.go(""" f([2, 3]) """) == -2
        assert self.i.go(""" f([2, [3, 4]]) """) == 12
        assert self.i.go(""" f([2, [2, 4]]) """) == 8
        assert self.i.go(""" f([2, 4]) """) == 6
        assert self.i.go(""" f([2, 3, 4]) """) == "not match"

        with pytest.raises(AssertionError):
            self.i.go(""" a """)

    def test_match_copy(self):
        assert self.i.go("""
            a := [2, 3, 4];
            match a
                case b then b[0] = 5
            end;
            a
        """) == [5, 3, 4]

        assert self.i.go("""
            a := [2, 3, 4];
            match a
                case [*b] then b[0] = 5
            end;
            a
        """) == [2, 3, 4]

    def test_continue(self):
        assert self.i.go("""
            a := [];
            i := 0; while i < 5 do
                i = i + 1;
                if i == 3 then continue() end;
                push(a, i)
            end;
            a
        """) == [1, 2, 4, 5]

        assert self.i.go("""
            a := []; i := 0; while i < 2 do
                j := 0; while j < 3 do
                    j = j + 1; if j == 2 then continue() end; push(a, [i, j])
                end; i = i + 1
            end;
            a
        """) == [[0, 1], [0, 3], [1, 1], [1, 3]]

        with pytest.raises(AssertionError, match="Continue takes no arguments"):
            self.i.go(""" while True do continue(2) end """)

        with pytest.raises(AssertionError, match="Continue at top level"):
            self.i.go(""" continue() """)

    def test_break(self):
        assert self.i.go("""
            a := [];
            i := 0; while i < 5 do
                if i == 3 then break() end;
                push(a, i);
                i = i + 1
            end;
            a
        """) == [0, 1, 2]

        assert self.i.go("""
            a := []; i := 0; while i < 2 do
                j := 0; while j < 3 do
                    if j == 2 then break() end; push(a, [i, j]); j = j + 1
                end; i = i + 1
            end; a
        """) == [[0, 0], [0, 1], [1, 0], [1, 1]]

        assert self.i.go(""" while True do break() end """) == None
        assert self.i.go(""" while True do break(2 + 3) end """) == 5

        with pytest.raises(AssertionError, match="Break takes zero or one argument"):
            self.i.go(""" while True do break(2, 3) end """)

        with pytest.raises(AssertionError, match="Break at top level"):
            self.i.go(""" break() """)

    def test_return(self):
        self.i.go("""
            deffunc f params a do
                if a == 2 then return(3) end;
                4
            end
        """)
        assert self.i.go(""" f(2) """) == 3
        assert self.i.go(""" f(3) """) == 4

        self.i.go("""
            deffunc fib params n do
                if n == 0 then return(0) end;
                if n == 1 then return(1) end;
                fib(n - 1) + fib(n - 2)
            end
        """)
        assert self.i.go(""" fib(0) """) == 0
        assert self.i.go(""" fib(1) """) == 1
        assert self.i.go(""" fib(7) """) == 13
        assert self.i.go(""" fib(9) """) == 34

        with pytest.raises(AssertionError, match="Return takes zero or one argument"):
            self.i.go(""" func do return(2, 3) end () """)

        with pytest.raises(AssertionError, match="Return from top level"):
            self.i.go(""" return() """)


    def test_import(self, tmp_path):
        self.i.go(""" fib := import("lib/fib.toil") """)
        assert self.i.go(""" fib(9) """) == 34

        self.i.go(""" [gcd_recur, gcd_iter] := import("lib/gcd.toil") """)
        assert self.i.go(""" gcd_recur(24, 36) """) == 12
        assert self.i.go(""" gcd_iter(24, 36) """) == 12

    def test_import_isolation(self, tmp_path):
        mod_a_path = tmp_path / "mod_a.toil"
        mod_a_path.write_text("a_private := 100; func do a_private end")

        self.i.go(f""" f := import("{mod_a_path}") """)
        assert self.i.go("f()") == 100
        with pytest.raises(AssertionError, match="Undefined variable"):
            self.i.go("a_private")

        mod_b_path = tmp_path / "mod_b.toil"
        mod_b_path.write_text("b_private := 200; a_private")
        with pytest.raises(AssertionError, match="Undefined variable"):
            self.i.go(f""" import("{mod_b_path}") """)

    def test_dict(self):
        assert self.i.go(""" {} """) == {}
        assert self.i.go(""" {"aaa": 2} """) == {'aaa': 2}
        self.i.go(""" bbb := 4 """)
        assert self.i.go(""" {aaa: 2 + 3, bbb} """) == {'aaa': 5, 'bbb': 4}

        self.i.go(""" a := {aaa: 2 + 3, bbb} """)
        assert self.i.go(""" a["aaa"] """) == 5
        assert self.i.go(""" a["bbb"] """) == 4
        with pytest.raises(KeyError):
            self.i.go(""" a["ccc"] """)

        self.i.go(""" a["aaa"] = 2 """)
        assert self.i.go(""" a """) == {'aaa': 2, 'bbb': 4}
        self.i.go(""" a["ccc"] = 5 """)
        assert self.i.go(""" a """) == {'aaa': 2, 'bbb': 4, 'ccc': 5}

        assert self.i.go(""" len(a) """) == 3
        assert self.i.go(""" has(a, "aaa") """) is True
        assert self.i.go(""" has(a, "bbb") """) is True
        assert self.i.go(""" has(a, "ddd") """) is False
        assert self.i.go(""" keys(a) """) == ['aaa', 'bbb', 'ccc']
        assert self.i.go(""" items(a) """) == [['aaa', 2], ['bbb', 4], ['ccc', 5]]

        self.i.go(""" [k, v] := items(a)[0] """)
        assert self.i.go(""" k """) == 'aaa'
        assert self.i.go(""" v """) == 2

        with pytest.raises(AssertionError, match="Illegal key"):
            self.i.go(""" {1: 2} """)

        with pytest.raises(AssertionError, match="Illegal indexing"):
            self.i.go(""" a[0] = 1 """)

    def test_dot_notation(self):
        self.i.go(""" a := {aaa: 2, bbb: 4} """)
        self.i.go(""" a.aaa = 2 """)
        assert self.i.go(""" a.aaa """) == 2
        self.i.go(""" a.ddd = 6 """)
        assert self.i.go(""" a """) == {'aaa': 2, 'bbb': 4, 'ddd': 6}

        with pytest.raises(AssertionError, match="Illegal property"):
            self.i.go(""" a.1 """)

        with pytest.raises(AssertionError):
            self.i.go(""" [1, 2].foo """)

    def test_dict_destructuring(self):
        assert self.i.go("""{a, b} := {a: 2, b: 3}; [a, b] """) == [2, 3]
        assert self.i.go("""{a, *b} := {a: 2, b: 3, c: 4, d: 5}; [a, b] """) == [2, {'b': 3, 'c': 4, 'd': 5}]
        assert self.i.go("""{*a, b} := {a: 2, b: 3, c: 4, d: 5}; [a, b] """) == [{'a': 2, 'c': 4, 'd': 5}, 3]
        assert self.i.go("""{a, *b, c} := {a: 2, b: 3, c: 4, d: 5}; [a, b, c] """) == [2, {'b': 3, 'd': 5}, 4]

    def test_dict_pattern_match(self):
        assert self.i.go(""" match {a: 2, b: 3} case {a, b} then [a, b] end """) == [2, 3]
        assert self.i.go(""" match {a: 2, b: 3} case {a: aa, b: bb} then [aa, bb] end """) == [2, 3]
        assert self.i.go(""" match {a: 2, b: 3, c: 4} case {a, b} then [a, b] end """) == [2, 3]
        assert self.i.go(""" match {a: 2, b: {c: 3, d: 4}} case {a, b: {c, d}} then [a, c, d] end """) == [2, 3, 4]
        assert self.i.go(""" match {a: 2, b: [3, 4]} case {a, b: [c, d]} then [a, c, d] end """) == [2, 3, 4]
        assert self.i.go(""" match {a: 2, b: 3, c: 4} case {a, *rest} then [a, rest] end """) == [2, {'b': 3, 'c': 4}]
        assert self.i.go(""" match {a: 2, b: 3, c: 4} case {*rest, b} then [rest, b] end """) == [{'a': 2, 'c': 4}, 3]
        assert self.i.go(""" match {a: 2, b: 3, c: 4} case {a, *rest, c} then [a, rest, c] end """) == [2, {'b': 3}, 4]
        assert self.i.go(""" match {a: 2} case {b: 3} then 4 end """) is None

    def test_dict_module(self):
        self.i.go(""" gcd := import("lib/gcd_dict.toil") """)
        assert self.i.go(""" gcd.recur(24, 36) """) == 12
        assert self.i.go(""" gcd.iter(24, 36) """) == 12

        self.i.go(""" {recur, iter} := import("lib/gcd_dict.toil") """)
        assert self.i.go(""" recur(24, 36) """) == 12
        assert self.i.go(""" iter(24, 36) """) == 12

        self.i.go(""" {recur: gcd_recur, iter: gcd_iter} := import("lib/gcd_dict.toil") """)
        assert self.i.go(""" gcd_recur(24, 36) """) == 12
        assert self.i.go(""" gcd_iter(24, 36) """) == 12

    def test_ufcs(self):
        # Case 1: Namespace
        self.i.go(""" foo := { add: func a, b do a + b end } """)
        assert self.i.go(""" foo.add(2, 3) """) == 5

        # Case 2: Method
        self.i.go(""" foo := { add: func self, a do self.val + a end, val: 2 } """)
        assert self.i.go(""" foo.add(3) """) == 5

        # Case 3: UFCS
        self.i.go(""" foo := 2 """)
        assert self.i.go(""" add(foo, 3) """) == 5
        assert self.i.go(""" foo.add(3) """) == 5

        self.i.go(""" myadd := func a, b do a + b end """)
        assert self.i.go(""" myadd(foo, 3) """) == 5
        assert self.i.go(""" foo.myadd(3) """) == 5

        # UFCS priority
        self.i.go(""" d := { len: func self do "local" end } """)
        assert self.i.go(""" d.len() """) == "local"

        with pytest.raises(AssertionError, match="Illegal operator"):
            self.i.go(""" d := { val: 123 }; d.val() """)
        with pytest.raises(AssertionError, match="Undefined variable"):
            self.i.go(""" 2.non_existent() """)

    def test_oo_style(self, capsys):
        self.i.go("""
            deffunc Animal params name do
                self := {};
                self._name = name;
                self.introduce = func self do print("I'm", self._name) end;
                self.make_sound = func self do print("crying") end;
                self
            end
        """)
        self.i.go("""
            animal1 := Animal("Rocky");
            animal2 := Animal("Lucy");
            animal1.introduce();
            animal1.make_sound();
            animal2.introduce();
            animal2.make_sound()
        """)
        assert capsys.readouterr().out == "I'm Rocky\ncrying\nI'm Lucy\ncrying\n"

        self.i.go("""
            deffunc Dog params name do
                self := Animal(name);
                self.make_sound = func self do print("woof") end;
                self
            end
        """)
        self.i.go("""
            dog1 := Dog("Leo");
            dog1.introduce();
            dog1.make_sound()
        """)
        assert capsys.readouterr().out == "I'm Leo\nwoof\n"

    def test_sieve_ufcs(self):
        result = self.i.go("""
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
        self.i.go("""
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
        assert self.i.go(""" try 2; 3 end """) == 3
        self.i.go(""" try print(2); print(3) end """)
        assert capsys.readouterr().out == "2\n3\n"

        # try with except, no raise
        assert self.i.go(""" try 2; 3 except e then print(e) end """) == 3
        self.i.go(""" try print(2); print(3) except e then print(e) end """)
        assert capsys.readouterr().out == "2\n3\n"

        # try with raise and catch
        self.i.go(""" try print(2); raise(2 + 3); print(3) except e then print(e) end """)
        assert capsys.readouterr().out == "2\n5\n"
        assert self.i.go(""" try 2; raise(2 + 3); 3 except e then e end """) == 5

        # pattern match in except
        self.i.go("""
            try
                print(2); raise(["foo", 3]); print(4)
            except ["foo", val] then print("foo", val)
            except ["bar", val] then print("bar", val)
            end
        """)
        assert capsys.readouterr().out == "2\nfoo 3\n"

        self.i.go("""
            try
                print(2); raise(["bar", 3]); print(4)
            except ["foo", val] then print("foo", val)
            except ["bar", val] then print("bar", val)
            end
        """)
        assert capsys.readouterr().out == "2\nbar 3\n"

        # unhandled exception
        with pytest.raises(AssertionError, match="ToilException"):
            self.i.go("""
                try
                    raise(["baz", 3])
                except ["foo", val] then print("foo", val)
                end
            """)

        # nested try
        self.i.go("""
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
        assert self.i.go(""" apply(add, [2, 3]) """) == 5
        assert self.i.go(""" apply(func a, b do a + b end, [2, 3]) """) == 5

        # eval
        self.i.go(""" a := 2; b := 3 """)
        assert self.i.go(""" eval("a + b") """) == 5
        assert self.i.go(""" scope a := 4; b := 5; eval("a + b") end """) == 5

        # Poor man's serialization
        self.i.go("""
            org := { name: "Toil", id: 1 };
            print(org);
            serialized := str(org);
            print(serialized);
            deserialized := eval(serialized);
            print(deserialized)
        """)
        assert capsys.readouterr().out == "{'name': 'Toil', 'id': 1}\n{'name': 'Toil', 'id': 1}\n{'name': 'Toil', 'id': 1}\n"

        # Poor man's syntax sugar
        assert self.i.go("""
            deffunc mydeffunc params name, params_, body do
                eval("deffunc " + name + " params " + params_ + " do " + body + " end")
            end;
            mydeffunc("myadd", "a, b", "a + b");
            myadd(2, 3)
        """) == 5

    def test_ast_primitives(self):
        assert self.i.go(""" quote(if True then 2 else 3 end) """) == (Sym("if"), True, 2, 3)
        assert self.i.go(""" expr(sym("if"), True, 2, 3) """) == (Sym("if"), True, 2, 3)
        assert self.i.go(""" eval_expr(expr(sym("if"), True, 2, 3)) """) == 2

        assert self.i.go(""" quote(add(2, 3)) """) == (Sym("add"), [2, 3])
        assert self.i.go(""" expr(sym("add"), [2, 3]) """) == (Sym("add"), [2, 3])
        assert self.i.go(""" eval_expr(expr(sym("add"), [2, 3])) """) == 5

        assert self.i.go(""" quote(
            a := 2;
            b := 3;
            if a == b then a + b else a * b end
        ) """) == (Sym("seq"), [(Sym("define"), [Sym("a"), 2]), (Sym("define"), [Sym("b"), 3]), (Sym("if"), (Sym("equal"), [Sym("a"), Sym("b")]), (Sym("add"), [Sym("a"), Sym("b")]), (Sym("mul"), [Sym("a"), Sym("b")]))])
        assert self.i.go("""
            expr(sym("seq"), [
                expr(sym("define"), [sym("a"), 2]),
                expr(sym("define"), [sym("b"), 3]),
                expr(sym("if"),
                    expr(sym("equal"), [sym("a"), sym("b")]),
                    expr(sym("add"), [sym("a"), sym("b")]),
                    expr(sym("mul"), [sym("a"), sym("b")])
                )
            ])
        """) == (Sym("seq"), [(Sym("define"), [Sym("a"), 2]), (Sym("define"), [Sym("b"), 3]), (Sym("if"), (Sym("equal"), [Sym("a"), Sym("b")]), (Sym("add"), [Sym("a"), Sym("b")]), (Sym("mul"), [Sym("a"), Sym("b")]))])
        assert self.i.go(""" eval_expr(
            expr(sym("seq"), [
                expr(sym("define"), [sym("a"), 2]),
                expr(sym("define"), [sym("b"), 3]),
                expr(sym("if"),
                    expr(sym("equal"), [sym("a"), sym("b")]),
                    expr(sym("add"), [sym("a"), sym("b")]),
                    expr(sym("mul"), [sym("a"), sym("b")])
                )
            ])
        ) """) == 6

    def test_macro(self, capsys):
        # Basic macro (when) vs function (fwhen)
        self.i.go("""
            when := macro cond, body do expr(sym("if"), cond, body, None) end;
            fwhen := func cond, body do if cond then body else None end end
        """)
        assert self.i.go(""" expand(when(2 == 2, 3)) """) == (Sym("if"), (Sym("equal"), [2, 2]), 3, None)
        assert self.i.go(""" when(2 == 2, 3) """) == 3
        assert self.i.go(""" when(2 == 3, 4 / 0) """) is None

        assert self.i.go(""" fwhen(2 == 2, 3) """) == 3
        with pytest.raises(ZeroDivisionError):
            self.i.go(""" fwhen(2 == 3, 4 / 0) """)

        # Macro defining macro (defmacro)
        self.i.go("""
            defmacro := macro name, params_, body do
                expr(sym("define"), [name, expr(sym("macro"), params_, body)])
            end
        """)
        self.i.go(""" defmacro(mwhen, [cond, body], expr(sym("if"), cond, body, None)) """)
        assert self.i.go(""" mwhen(2 == 2, 3) """) == 3
        with pytest.raises(AssertionError, match="Argument mismatch"):
            self.i.go(""" mwhen(2 == 2) """)

        # Macro for scope
        self.i.go("""
            defmacro(mscope, [body], expr(expr(sym("func"), [], body), []))
        """)
        self.i.go(""" a := 2; mscope(print(a); a := 3; print(a)); print(a) """)
        assert capsys.readouterr().out == "2\n3\n2\n"

        # Anaphoric if
        self.i.go("""
            defmacro(aif, [cnd, thn, els], expr(sym("scope"), expr(sym("if"),
                expr(sym("define"), [sym("it"), cnd]),
                thn,
                els
            )))
        """)
        assert self.i.go(""" aif(2, [True, it], [False, it]) """) == [True, 2]
        assert self.i.go(""" aif(0, [True, it], [False, it]) """) == [False, 0]

        # and/or using aif
        self.i.go("""
            defmacro(mand, [a, b], expr(sym("aif"), [a, b, sym("it")]));
            defmacro(mor, [a, b], expr(sym("aif"), [a, sym("it"), b]))
        """)
        assert self.i.go(""" mand(2, 3) """) == 3
        assert self.i.go(""" mand(0, 3) """) == 0
        assert self.i.go(""" mor(2, 3) """) == 2
        assert self.i.go(""" mor(0, 3) """) == 3

        # Side effect in macro argument
        self.i.go("""
            deffunc ftwice params x do x + x end;
            defmacro(mtwice, [x], expr(sym("add"), [x, x]))
        """)
        self.i.go(""" cnt := 0 """)
        assert self.i.go(""" ftwice(cnt = cnt + 1) """) == 2
        assert self.i.go(""" cnt """) == 1

        self.i.go(""" cnt := 0 """)
        assert self.i.go(""" mtwice(cnt = cnt + 1) """) == 3
        assert self.i.go(""" cnt """) == 2

        # Variable capture (Non-hygienic)
        self.i.go(""" defmacro(capture, [val], expr(sym("define"), [sym("x"), val])) """)
        self.i.go(""" x := 1 """)
        self.i.go(""" capture(2) """)
        assert self.i.go(""" x """) == 2

class TestQuasiquote(TestBase):
    def test_basic(self):
        self.i.go(""" a := 2; b := ["A", "B"] """)
        assert self.i.go(""" qq(3) """) == 3
        assert self.i.go(""" qq("A") """) == "A"
        assert self.i.go(""" qq(a) """) == Sym("a")
        assert self.i.go(""" qq(!a) """) == 2
        assert self.i.go(""" qq(!a + 2) """) == (Sym("add"), [2, 2])
        assert self.i.go(""" qq(!(a + 2)) """) == 4

    def test_list(self):
        self.i.go(""" a := 2; b := ["A", "B"] """)
        assert self.i.go(""" qq([a, b]) """) == [Sym("a"), Sym("b")]
        assert self.i.go(""" qq([!a, !b]) """) == [2, ["A", "B"]]

    def test_splicing(self):
        self.i.go(""" a := 2; b := ["A", "B"] """)
        assert self.i.go(""" qq([!!b]) """) == ["A", "B"]
        assert self.i.go(""" qq([a, !!b, 2]) """) == [Sym("a"), "A", "B", 2]

    def test_nested(self):
        self.i.go(""" a := 2 """)
        expected = (Sym("if"), (Sym("equal"), [2, 3]), 4, 5)
        assert self.i.go(""" qq(if !a == 3 then 4 else 5 end) """) == expected
        assert self.i.go(""" eval_expr(qq(if !a == 3 then 4 else 5 end)) """) == 5

    def test_splicing_call(self, capsys):
        self.i.go(""" args := [2, 3] """)
        assert self.i.go(""" qq(print(1, !!args, 4)) """) == (Sym("print"), [1, 2, 3, 4])
        self.i.go(""" eval_expr(qq(print(1, !!args, 4))) """)
        assert capsys.readouterr().out == "1 2 3 4\n"

    def test_splicing_seq(self, capsys):
        self.i.go(""" stmts := [quote(print(2)), quote(print(3))] """)
        seq_ast = self.i.go(""" qq(print(1); !!stmts; print(4)) """)
        self.i.go(""" eval_expr(qq(print(1); !!stmts; print(4))) """)
        assert capsys.readouterr().out == "1\n2\n3\n4\n"

    def test_errors(self):
        with pytest.raises(AssertionError, match="Undefined variable"):
            self.i.go(""" qq(!c) """)
        with pytest.raises(AssertionError, match="Unexpected token"):
             self.i.go(""" qq(if) """)

class TestMacroSamples(TestBase):
    def test_when(self):
        self.i.go("""
            when := macro cond, body do qq(if !cond then !body else None end) end
        """)
        assert self.i.go(""" expand(when(2 == 2, 3)) """) == (Sym("if"), (Sym("equal"), [2, 2]), 3, None)
        assert self.i.go(""" when(2 == 2, 3) """) == 3
        assert self.i.go(""" when(2 == 3, 4 / 0) """) is None

    def test_fwhen_error(self):
        self.i.go("""
            fwhen := func cond, body do if cond then body else None end end
        """)
        assert self.i.go(""" fwhen(2 == 2, 3) """) == 3
        with pytest.raises(ZeroDivisionError):
            self.i.go(""" fwhen(2 == 3, 4 / 0) """)

    def test_deffunc_macro(self):
        self.i.go("""
            mdeffunc := macro name, params_, body do
                qq(!name := func !!params_ do !body end)
            end
        """)
        self.i.go(""" mdeffunc(myadd, [a, b], a + b) """)
        assert self.i.go(""" myadd(2, 3) """) == 5

    def test_defmacro_macro(self):
        self.i.go("""
            defmacro := macro name, params_, body do
                qq(!name := macro !!params_ do !body end)
            end
        """)
        self.i.go(""" defmacro(when, [cond, body], qq(if !cond then !body else None end)) """)
        assert self.i.go(""" when(2 == 2, 3) """) == 3
        assert self.i.go(""" when(2 == 3, 4 / 0) """) is None
        with pytest.raises(AssertionError, match="Argument mismatch"):
            self.i.go(""" when(2 == 2) """)

    def test_mscope(self, capsys):
        self.i.go(""" mscope := macro body do qq(func do !body end ()) end """)
        self.i.go(""" a := 2; mscope(print(a); a := 3; print(a)); print(a) """)
        assert capsys.readouterr().out == "2\n3\n2\n"

    def test_anaphoric_if_and_or(self):
        self.i.go("""
            aif := macro cnd, thn, els do
                qq(if it := !cnd then !thn else !els end)
            end
        """)
        assert self.i.go(""" aif(2, [True, it], [False, it]) """) == [True, 2]
        assert self.i.go(""" aif(0, [True, it], [False, it]) """) == [False, 0]

        self.i.go(""" mand := macro a, b do qq(aif(!a, !b, it)) end """)
        self.i.go(""" mor := macro a, b do qq(aif(!a, it, !b)) end """)

        assert self.i.go(""" mand(2, 3) """) == 3
        assert self.i.go(""" mand(0, 3) """) == 0
        assert self.i.go(""" mor(2, 3) """) == 2
        assert self.i.go(""" mor(0, 3) """) == 3

        with pytest.raises(AssertionError, match="Undefined variable"):
             self.i.go(""" expand(expand(mand(2, 3))) """)

    def test_side_effect_macro(self):
        self.i.go("""
            deffunc ftwice params x do x + x end;
            mtwice := macro x do qq(add(!x, !x)) end
        """)
        self.i.go(""" cnt := 0 """)
        assert self.i.go(""" ftwice(cnt = cnt + 1) """) == 2
        assert self.i.go(""" cnt """) == 1
        self.i.go(""" cnt := 0 """)
        assert self.i.go(""" mtwice(cnt = cnt + 1) """) == 3
        assert self.i.go(""" cnt """) == 2

    def test_capture(self):
        self.i.go(""" capture := macro val do qq(x := !val) end """)
        self.i.go(""" x := 1 """)
        self.i.go(""" capture(2) """)
        assert self.i.go(""" x """) == 2

    def test_call_by_name(self):
        self.i.go("""
            call_by_name := macro name_str, *args do
                qq( (!sym(qq(!name_str)))(!!args) )
            end
        """)
        assert self.i.go(""" call_by_name("add", 2, 3) """) == 5
        assert self.i.go(""" call_by_name("sub", 10, 4) """) == 6

if __name__ == "__main__":
    pytest.main([__file__])
