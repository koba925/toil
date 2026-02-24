import pytest
from toil import Interpreter, Sym, Expr


class TestBase:
    @pytest.fixture(autouse=True)
    def set_interpreter(self):
        self.i = Interpreter().init_env()


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
        assert self.i.scan(""" True """) == [True, "$EOF"]
        assert self.i.scan(""" False """) == [False, "$EOF"]
        assert self.i.scan(""" None """) == [None, "$EOF"]
        assert self.i.scan(""" a """) == [Sym("a"), "$EOF"]

    def test_define_assign(self):
        assert self.i.scan(""" a := 2 """) == [Sym("a"), Sym(":="), 2, Sym("$EOF")]
        assert self.i.scan(""" a = 2 """) == [Sym("a"), Sym("="), 2, Sym("$EOF")]

class TestParse(TestBase):
    def test_comparison(self):
        assert self.i.ast(""" 2 == 3 == 4 """) == Expr((
            Sym("equal"), [Expr((Sym("equal"), [2, 3])), 4]
        ))

    def test_add_sub(self):
        assert self.i.ast(""" 2 + 3 """) == Expr((Sym("add"), [2, 3]))
        assert self.i.ast(""" 2 - 3 """) == Expr((Sym("sub"), [2, 3]))
        assert self.i.ast(""" 2 + 3 * 4 """) == Expr((Sym("add"), [2, Expr((Sym("mul"), [3, 4]))]))
        assert self.i.ast(""" 2 * 3 + 4 """) == Expr((Sym("add"), [Expr((Sym("mul"), [2, 3])), 4]))

    def test_mul_div(self):
        assert self.i.ast(""" 2 * 3 """) == Expr((Sym("mul"), [2, 3]))
        assert self.i.ast(""" 2 / 3 """) == Expr((Sym("div"), [2, 3]))
        assert self.i.ast(""" 2 * 3 / 4 """) == Expr((Sym("div"), [Expr((Sym("mul"), [2, 3])), 4]))

    def test_not(self):
        assert self.i.ast(""" not True """) == Expr((Sym("not"), [True]))
        assert self.i.ast(""" not not False """) == Expr((Sym("not"), [Expr((Sym("not"), [False]))]))

    def test_and_or(self):
        assert self.i.ast(""" True and False """) == Expr(('if', True, False, True))
        assert self.i.ast(""" True or False """) == Expr(('if', True, True, False))
        assert self.i.ast(""" True or False and True """) == Expr(('if', Expr(('if', True, True, False)), True, Expr(('if', True, True, False))))
        assert self.i.ast(""" a := False and not False """) == Expr((Sym('define'), [Sym('a'), Expr(('if', False, Expr((Sym('not'), [False])), False))]))
        assert self.i.ast(""" a := False or not False """) == Expr((Sym('define'), [Sym('a'), Expr(('if', False, False, Expr((Sym('not'), [False]))))]))

    def test_neg(self):
        assert self.i.ast(""" -2 """) == Expr((Sym("neg"), [2]))
        assert self.i.ast(""" --3 """) == Expr((Sym("neg"), [Expr((Sym("neg"), [3]))]))

    def test_number(self):
        assert self.i.ast(""" 2 """) == 2

    def test_bool_none(self):
        assert self.i.ast(""" True """) is True
        assert self.i.ast(""" False """) is False
        assert self.i.ast(""" None """) is None

    def test_paren(self):
        assert self.i.ast(""" (1 + 2) """) == Expr((Sym("add"), [1, 2]))
        assert self.i.ast(""" (1 + 2) * 3 """) == Expr((Sym("mul"), [Expr((Sym("add"), [1, 2])), 3]))

    def test_seq(self):
        assert self.i.ast(""" 2; 3 """) == Expr((Sym("seq"), [2, 3]))
        assert self.i.ast(""" not True; False """) == Expr((Sym("seq"), [Expr((Sym("not"), [True])), False]))

    def test_if(self):
        assert self.i.ast(""" if True then 2 else 3 end """) == Expr(
            (Sym("if"), True, 2, 3))
        assert self.i.ast(""" if not True then 2 + 3 else 4; 5 end """) == Expr(
            (Sym("if"), Expr((Sym('not'), [True])), Expr((Sym('add'), [2, 3])), Expr((Sym("seq"), [4, 5]))))

        assert self.i.ast(""" if 1 then 10 end """) == Expr(('if', 1, 10, None))
        assert self.i.ast(""" if 1 then 10 else 20 end """) == Expr(('if', 1, 10, 20))
        assert self.i.ast(""" if 1 then 10 elif 2 then 20 end """) == Expr(('if', 1, 10, Expr(('if', 2, 20, None))))
        assert self.i.ast(""" if 1 then 10 elif 2 then 20 else 30 end """) == Expr(('if', 1, 10, Expr(('if', 2, 20, 30))))
        assert self.i.ast(""" if 1 then 10 elif 2 then 20 elif 3 then 30 else 40 end """) == Expr(('if', 1, 10, Expr(('if', 2, 20, Expr(('if', 3, 30, 40))))))

    def test_define(self):
        assert self.i.ast(""" a := not True """) == Expr((Sym("define"), [Sym("a"), Expr((Sym("not"), [True]))]))
        assert self.i.ast(""" a := b := 2 """) == Expr((Sym("define"), [Sym("a"), Expr((Sym("define"), [Sym("b"), 2]))]))

    def test_assign(self):
        assert self.i.ast(""" a = 1 """) == Expr((Sym("assign"), [Sym("a"), 1]))
        assert self.i.ast(""" a = b = 2 """) == Expr((Sym("assign"), [Sym("a"), Expr((Sym("assign"), [Sym("b"), 2]))]))
        assert self.i.ast(""" a := b = 2 """) == Expr((Sym("define"), [Sym("a"), Expr((Sym("assign"), [Sym("b"), 2]))]))
        assert self.i.ast(""" a := b = c := 3 """) == Expr((Sym("define"), [Sym("a"), Expr((Sym("assign"), [Sym("b"), Expr((Sym("define"), [Sym("c"), 3]))]))]))

    def test_while(self):
        assert self.i.ast(""" while i < 10 do i = i + 1 end """) == Expr(('while', Expr((Sym('less'), [Sym('i'), 10])), Expr((Sym('assign'), [Sym('i'), Expr((Sym('add'), [Sym('i'), 1]))]))))

    def test_call(self):
        assert self.i.ast(""" print() """) == Expr((Sym("print"), []))
        assert self.i.ast(""" neg(2) """) == Expr((Sym("neg"), [2]))
        assert self.i.ast(""" add(2, mul(3, 4)) """) == Expr((Sym("add"), [2, Expr((Sym("mul"), [3, 4]))]))

    def test_func(self):
        assert self.i.ast(""" func do 2 end """) == Expr((Sym("func"), [], 2))
        assert self.i.ast(""" func a do a + 2 end """) == Expr((Sym("func"), [Sym("a")], Expr((Sym("add"), [Sym("a"), 2]))))
        assert self.i.ast(""" func a, b do a + b end """) == Expr((Sym("func"), [Sym("a"), Sym("b")], Expr((Sym("add"), [Sym("a"), Sym("b")]))))

        with pytest.raises(AssertionError, match="Expected `do`"):
            self.i.ast(""" func a 2 end """)
        with pytest.raises(AssertionError, match="Expected `end`"):
            self.i.ast(""" func a do 2 """)

    def test_deffunc(self):
        assert self.i.ast(""" deffunc two params do 2 end """) == Expr(
            (Sym('define'), [Sym('two'), Expr(('func', [], 2))]))
        assert self.i.ast("""
             deffunc add2 params a do
                a + 2
             end
        """) == Expr((Sym('define'), [Sym('add2'), Expr(('func', [Sym('a')], Expr((Sym('add'), [Sym('a'), 2]))))]))
        assert self.i.ast("""
            deffunc sum params a, b, c do
                a + b + c
            end
        """) == Expr((Sym('define'), [Sym('sum'), Expr(('func', [Sym('a'), Sym('b'), Sym('c')], Expr((Sym('add'), [Expr((Sym('add'), [Sym('a'), Sym('b')])), Sym('c')]))))]))

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
        self.i.evaluate(Expr((Sym("seq"), [
            Expr((Sym("print"), [2])),
            Expr((Sym("print"), [3]))
        ])))
        assert capsys.readouterr().out == "2\n3\n"

    def test_evaluate_if(self):
        assert self.i.evaluate(Expr((Sym("if"), True, 2, 3))) == 2
        assert self.i.evaluate(Expr((Sym("if"), False, 2, 3))) == 3
        assert self.i.evaluate(Expr((Sym("if"), Expr((Sym("if"), True, True, False)), 2, 3))) == 2
        assert self.i.evaluate(Expr((Sym("if"), True, Expr((Sym("if"), True, 2, 3)), 4))) == 2
        assert self.i.evaluate(Expr((Sym("if"), False, 2, Expr((Sym("if"), False, 3, 4))))) == 4

    def test_evaluate_variable(self):
        assert self.i.evaluate(Expr((Sym("define"), [Sym("a"), 2]))) == 2
        assert self.i.evaluate(Sym("a")) == 2

        assert self.i.evaluate(Expr((Sym("define"), [Sym("b"), True]))) == True
        assert self.i.evaluate(Expr((Sym("if"), Sym("b"), 2, 3))) == 2

        assert self.i.evaluate(Expr((Sym("define"), [Sym("c"), Expr((Sym("if"), False, 2, 3))]))) == 3
        assert self.i.evaluate(Sym("c")) == 3

    def test_evaluate_undefined_variable(self):
        with pytest.raises(AssertionError):
            self.i.evaluate(Sym("a"))

    def test_evaluate_assign(self):
        self.i.evaluate(Expr((Sym("define"), [Sym("a"), 1])))
        assert self.i.evaluate(Expr((Sym("assign"), [Sym("a"), 2]))) == 2
        assert self.i.evaluate(Sym("a")) == 2
        with pytest.raises(AssertionError):
            self.i.evaluate(Expr((Sym("assign"), [Sym("b"), 2])))

    def test_evaluate_scope(self, capsys):
        self.i.evaluate(Expr((Sym("define"), [Sym("a"), 2])))
        assert self.i.evaluate(Sym("a")) == 2
        assert self.i.evaluate(Expr((Sym("scope"), Sym("a")))) == 2

        assert self.i.evaluate(Expr((Sym("scope"), Expr((Sym("seq"), [
            Expr((Sym("print"), [Sym("a")])),
            Expr((Sym("define"), [Sym("a"), 3])),
            Expr((Sym("print"), [Sym("a")])),
            Expr((Sym("define"), [Sym("b"), 4])),
            Expr((Sym("print"), [Sym("b")])),
            Sym("b")
        ]))))) == 4
        assert capsys.readouterr().out == "2\n3\n4\n"

        assert self.i.evaluate(Sym("a")) == 2

        with pytest.raises(AssertionError):
            self.i.evaluate(Sym("b"))

    def test_builtin_functions(self, capsys):
        assert self.i.evaluate(Expr((Sym("add"), [2, 3]))) == 5
        assert self.i.evaluate(Expr((Sym("sub"), [5, 3]))) == 2
        assert self.i.evaluate(Expr((Sym("mul"), [2, 3]))) == 6

        assert self.i.evaluate(Expr((Sym("equal"), [2, 2]))) is True
        assert self.i.evaluate(Expr((Sym("equal"), [2, 3]))) is False

        assert self.i.evaluate(Expr((Sym("add"), [2, Expr((Sym("mul"), [3, 4]))]))) == 14

        self.i.evaluate(Expr((Sym("print"), [2, 3])))
        assert capsys.readouterr().out == "2 3\n"

        self.i.evaluate(Expr((Sym("print"), [Expr((Sym("add"), [5, 5]))])))
        assert capsys.readouterr().out == "10\n"

    def test_user_func(self):
        self.i.evaluate(Expr((Sym("define"), [Sym("add2"), Expr((Sym("func"), [Sym("a")],
            Expr((Sym("add"), [Sym("a"), 2]))
        ))])))
        assert self.i.evaluate(Expr((Sym("add2"), [3]))) == 5

        self.i.evaluate(Expr((Sym("define"), [Sym("sum3"), Expr((Sym("func"),[Sym("a"), Sym("b"), Sym("c")],
            Expr((Sym("add"), [Sym("a"), Expr((Sym("add"), [Sym("b"), Sym("c")]))]))
        ))])))
        assert self.i.evaluate(Expr((Sym("sum3"), [2, 3, 4]))) == 9

    def test_recursion(self):
        self.i.evaluate(Expr((Sym("define"), [Sym("fac"), Expr((Sym("func"),[Sym("n")],
            Expr((Sym("if"), Expr((Sym("equal"), [Sym("n"), 1])),
                1,
                Expr((Sym("mul"), [Sym("n"), Expr((Sym("fac"), [Expr((Sym("sub"), [Sym("n"), 1]))]))]))
            )
        )))])))
        assert self.i.evaluate(Expr((Sym("fac"), [1]))) == 1
        assert self.i.evaluate(Expr((Sym("fac"), [3]))) == 6
        assert self.i.evaluate(Expr((Sym("fac"), [5]))) == 120

    def test_scope_leak(self):
        self.i.evaluate(Expr((Sym("define"), [Sym("x"), 2])))
        self.i.evaluate(Expr((Sym("define"), [Sym("f"), Expr((Sym("func"), [Sym("x")], 3))])))
        self.i.evaluate(Expr((Sym("f"), [4])))
        assert self.i.evaluate(Sym("x")) == 2

    def test_closure(self):
        self.i.evaluate(Expr((Sym("define"), [Sym("x"), 2])))
        self.i.evaluate(Expr((Sym("define"), [Sym("return_x"), Expr((Sym("func"), [], Sym("x")))])))
        assert self.i.evaluate(Expr((Sym("return_x"), []))) == 2
        assert self.i.evaluate(Expr((Sym("scope"), Expr((Sym("seq"), [
            Expr((Sym("define"), [Sym("x"), 3])),
            Expr((Sym("return_x"), []))
        ]))))) == 2
        assert self.i.evaluate(Sym("x")) == 2

    def test_adder(self):
        self.i.evaluate(Expr((Sym("define"), [Sym("make_adder"), Expr((Sym("func"), [Sym("n")],
            Expr((Sym("func"), [Sym("m")], Expr((Sym("add"), [Sym("n"), Sym("m")]))))
        ))])))
        self.i.evaluate(Expr((Sym("define"), [Sym("add2"), Expr((Sym("make_adder"), [2]))])))
        self.i.evaluate(Expr((Sym("define"), [Sym("add3"), Expr((Sym("make_adder"), [3]))])))

        assert self.i.evaluate(Expr((Sym("add2"), [3]))) == 5
        assert self.i.evaluate(Expr((Sym("add3"), [4]))) == 7

    def test_shadowing(self):
        self.i.evaluate(Expr((Sym("define"), [Sym("make_shadow"), Expr((Sym("func"), [Sym("x")],
            Expr((Sym("func"), [],
                Expr((Sym("seq"), [
                    Expr((Sym("define"), [Sym("x"), 3])),
                    Sym("x")
                ])
            )
        ))))])))
        self.i.evaluate(Expr((Sym("define"), [Sym("g"), Expr((Sym("make_shadow"), [2]))])))
        assert self.i.evaluate(Expr((Sym("g"), []))) == 3

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

        assert self.i.go(""" if False then 1 elif True then 3 else 4 end """) == 3
        assert self.i.go(""" if False then 1 elif False then 3 else 4 end """) == 4

        with pytest.raises(AssertionError):
            self.i.go(""" if True then 2 else 3 """)
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

        with pytest.raises(AssertionError): # No condition
            self.i.go(""" while do i = i + 1 end """)
        with pytest.raises(AssertionError, match="Expected `do`"):
            self.i.go(""" while i < 10 i = i + 1 end """)
        with pytest.raises(AssertionError, match="Expected `end`"):
            self.i.go(""" while i < 10 do i = i + 1 """)

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

    def test_gcd(self):
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

    def test_no_code(self):
        with pytest.raises(AssertionError):
            self.i.go("""  """)

    def test_extra_token(self):
        with pytest.raises(AssertionError):
            self.i.go(""" 7 8 """)

if __name__ == "__main__":
    pytest.main([__file__])
