import pytest
from toil import Interpreter, Ident

toil = Interpreter()


@pytest.fixture(autouse=True)
def setup_toil():
    global toil
    toil = Interpreter().init_env().stdlib()

class TestToil:
    # Ensure test independence
    def test_env_isolation_step1(self):
        assert toil.walk(r""" a := 2 """) == 2
    def test_env_isolation_step2(self):
        with pytest.raises(AssertionError, match="Undefined variable"):
            toil.walk(r""" a """)

    def test_overall_structure(self):
        assert toil.scan(r""" 2 """) == [2, Ident('$EOF')]
        assert toil.parse([2, Ident('$EOF')]) == 2
        assert toil.ast(r""" 2 """) == 2
        assert toil.eval(2) == 2
        assert toil.walk(r""" 2 """) == 2

    def test_sequence(self):
        assert toil.walk(r""" if True then 2 end; if True then 3 end """) == 3
        assert toil.walk(r""" if True then 2 end; if True then 3 end; 4 """) == 4

    def test_define_assign(self):
        assert toil.walk(r""" a := 2 """) == 2
        assert toil.walk(r""" a """) == 2

        assert toil.walk(r""" a = 3 """) == 3
        assert toil.walk(r""" a """) == 3

        assert toil.walk(r""" a := b := 4 """) == 4
        assert toil.walk(r""" a """) == 4
        assert toil.walk(r""" b """) == 4

        assert toil.walk(r""" a = b = 5 """) == 5
        assert toil.walk(r""" a """) == 5
        assert toil.walk(r""" b """) == 5

        assert toil.walk(r""" a = c := 6 """) == 6
        assert toil.walk(r""" a """) == 6
        assert toil.walk(r""" c """) == 6

        with pytest.raises(AssertionError, match="Undefined variable"):
            toil.walk(r""" undefined_variable """)
        with pytest.raises(AssertionError, match="Undefined variable"):
            toil.walk(r""" undefined_variable = 2 """)
        with pytest.raises(AssertionError, match="Unexpected token"):
            toil.walk(r""" a := """)

    def test_destructure_variable_and_literal(self):
        # Variable pattern
        assert toil.walk(r""" a := 2; a """) == 2
        assert toil.walk(r""" _ := 2; _ """) == 2

        # Literal pattern
        assert toil.walk(r""" a := 2; 2 := a """) == 2
        assert toil.walk(r""" None := None """) is None
        assert toil.walk(r""" True := True """) is True
        assert toil.walk(r""" "hello" := "hello" """) == "hello"

        with pytest.raises(Exception, match="Pattern mismatch"):
            toil.walk(r""" "hello" := "world" """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            toil.walk(r""" a := 3; 2 := a """)

    def test_destructure_list(self):
        assert toil.walk(r""" [a, b] := [3, 4]; [a, b] """) == [3, 4]
        assert toil.walk(r""" [] := [] """) == []
        assert toil.walk(r""" [_, b, _] := [2, 3, 4]; b """) == 3

        with pytest.raises(Exception, match="Pattern mismatch"):
            toil.walk(r""" [a, b] := [2] """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            toil.walk(r""" [a, b] := [4, 5, 6] """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            toil.walk(r""" [] := [1] """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            toil.walk(r""" [a] := 2 """)

        # Rest parameters
        assert toil.walk(r""" [a, *b] := [2]; [a, b] """) == [2, []]
        assert toil.walk(r""" [a, *b] := [3, 4]; [a, b] """) == [3, [4]]
        assert toil.walk(r""" [a, *b] := [4, 5, 6]; [a, b] """) == [4, [5, 6]]
        assert toil.walk(r""" [*a] := [4, 5, 6]; a """) == [4, 5, 6]

        assert toil.walk(r""" [*a, b] := [2]; [a, b] """) == [[], 2]
        assert toil.walk(r""" [*a, b] := [2, 3]; [a, b] """) == [[2], 3]
        assert toil.walk(r""" [*a, b] := [2, 3, 4]; [a, b] """) == [[2, 3], 4]

        assert toil.walk(r""" [a, *b, c] := [3, 4]; [a, b, c] """) == [3, [], 4]
        assert toil.walk(r""" [a, *b, c] := [4, 5, 6]; [a, b, c] """) == [4, [5], 6]
        assert toil.walk(r""" [a, *b, c] := [5, 6, 7, 8]; [a, b, c] """) == [5, [6, 7], 8]

        with pytest.raises(Exception, match="Pattern mismatch"):
            toil.walk(r""" [a, *b] := [] """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            toil.walk(r""" [*a, b] := [] """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            toil.walk(r""" [a, *b, c] := [2] """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            toil.walk(r""" [a, *b, *c, d] := [5, 6, 7, 8] """)

    def test_destructure_dict(self):
        assert toil.walk(r""" {a} := {a: 2, b: 3}; a """) == 2
        assert toil.walk(r""" {a, b} := {a: 2, b: 3}; [a, b] """) == [2, 3]
        assert toil.walk(r""" {a: c, b: d} := {a: 3, b: 4}; [c, d] """) == [3, 4]
        assert toil.walk(r""" {a} := {"a": 5, b: 6}; a """) == 5
        assert toil.walk(r""" {a: _, b} := {a: 2, b: 3}; b """) == 3
        assert toil.walk(r""" {} := {a: 2, b: 3} """) == {'a': 2, 'b': 3}

        assert toil.walk(r""" {a, *rest} := {a: 2}; [a, rest] """) == [2, {}]
        assert toil.walk(r""" {a, *rest} := {a: 2, b: 3}; [a, rest] """) == [2, {'b': 3}]
        assert toil.walk(r""" {a, *rest} := {a: 2, b: 3, c: 4}; [a, rest] """) == [2, {'b': 3, 'c': 4}]

        with pytest.raises(Exception, match="Pattern mismatch"):
            toil.walk(r""" {a} := {b: 2} """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            toil.walk(r""" {a, b, c} := {a: 2, b: 3} """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            toil.walk(r""" {a, *rest} := {b: 2} """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            toil.walk(r""" {a} := 2 """)

    def test_destructure_ident_and_expr(self):
        assert toil.walk(r""" Ident("aaa") := Ident("aaa") """) == Ident("aaa")
        assert toil.walk(r""" Ident(a) := Ident("aaa"); a """) == "aaa"

        with pytest.raises(Exception, match="Pattern mismatch"):
            toil.walk(r""" Ident("aaa") := Ident("bbb") """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            toil.walk(r""" Ident(a) := "aaa" """)

        assert toil.walk(r""" tuple(Ident("add"), [int(a), int(b)]) := tuple(Ident("add"), [2, 3]); [a, b] """) == [2, 3]
        assert toil.walk(r""" tuple(Ident("add"), [Ident(name1), Ident(name2)]) := tuple(Ident("add"), [Ident("a"), Ident("b")]); [name1, name2] """) == ['a', 'b']

        with pytest.raises(Exception, match="Pattern mismatch"):
            toil.walk(r""" tuple(Ident("add"), [Ident(name1), Ident(name2)]) := 2 + 3 """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            toil.walk(r""" tuple(Ident("add"), [Ident(name1), Ident(name2)]) := tuple(Ident("add")) """)

    def test_destructure_type(self):
        assert toil.walk(r""" int(a) := 2; a """) == 2
        assert toil.walk(r""" str(a) := "aaa"; a """) == "aaa"
        with pytest.raises(Exception, match="Pattern mismatch"):
            toil.walk(r""" int(a) := "2" """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            toil.walk(r""" str(a) := [] """)

    def test_destructure_or(self):
        assert toil.walk(r""" int(a) or str(a) := 2; a """) == 2
        assert toil.walk(r""" int(a) or str(a) := "aaa"; a """) == "aaa"
        assert toil.walk(r""" int(a) or str(a) or list(a):= [2]; a """) == [2]
        with pytest.raises(Exception, match="Pattern mismatch"):
            toil.walk(r""" int(a) or str(a) := [2] """)

    def test_destructure_combination(self):
        assert toil.walk(r""" [{a: b}, c] := [{a: 2, b: 3}, 4]; [b, c] """) == [2, 4]
        assert toil.walk(r""" {a: [b, c]} := {a: [5, 6]}; [b, c] """) == [5, 6]

    def test_list_assign(self):
        toil.walk(r""" b := [2, 3, [4, 5]] """)
        toil.walk(r""" b[0] = 6 """)
        assert toil.walk(r""" b[0] """) == 6
        toil.walk(r""" b[2][1] = 7 """)
        assert toil.walk(r""" b[2][1] """) == 7
        assert toil.walk(r""" b """) == [6, 3, [4, 7]]

        assert toil.walk(r""" a := [1, 2]; b := [3, 4]; a[0] = b[1] = 5; [a, b] """) == [[5, 2], [3, 5]]

    def test_arrow_function(self):
        assert toil.walk(r""" ([] -> 2)() """) == 2
        assert toil.walk(r""" ([a] -> a + 2)(3) """) == 5
        assert toil.walk(r""" (a -> a + 2)(3) """) == 5
        assert toil.walk(r""" ([[a, b]] -> a + b)([2, 3]) """) == 5
        assert toil.walk(r""" ([a, b] -> a + b)(2, 3) """) == 5
        with pytest.raises(Exception, match="Pattern mismatch"):
            toil.walk(r""" ([a, b] -> a + b)(2) """)

        assert toil.walk(r""" ([a, *b] -> b)(2, 3, 4) """) == [3, 4]
        assert toil.walk(r""" ({a} -> a + 2)({a: 3}) """) == 5
        with pytest.raises(Exception, match="Pattern mismatch"):
            toil.walk(r""" ({a} -> a + 2)({b: 3}) """)

        assert toil.walk(r""" (int(a) -> a + 2)(3) """) == 5
        with pytest.raises(Exception, match="Pattern mismatch"):
            toil.walk(r""" (int(a) -> a + 2)("aaa") """)

        assert toil.walk(r""" (x -> x or 2)(False) """) == 2
        assert toil.walk(r""" (a -> b -> a + b)(2)(3) """) == 5

        assert toil.walk(r""" inc := a -> a + 1; inc(2) """) == 3
        assert toil.walk(r""" myadd := [a, b] -> a + b; myadd(2, 3) """) == 5

        assert toil.walk(r""" f := a -> a or 2; f(False) """) == 2

    def test_logical_operations(self, capsys):
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

        assert toil.walk(r""" not True """) is False
        assert toil.walk(r""" not False """) is True
        assert toil.walk(r""" not not True """) is True

        assert toil.walk(r""" a := not 2 == 2 or True """) is True

        assert toil.walk(r""" True or False and False """) is False  # (True or False) and False
        assert toil.walk(r""" False and False or True """) is True   # (False and False) or True
        assert toil.walk(r""" not True and False """) is False       # (not True) and False
        assert toil.walk(r""" False or not False """) is True        # False or (not False)
        assert toil.walk(r""" not 2 == 3 """) is True                # not (2 == 3)

    def test_comparison_operations(self):
        assert toil.walk(r""" 2 + 5 == 3 + 4 """) is True
        assert toil.walk(r""" 2 + 3 == 3 + 4 """) is False
        assert toil.walk(r""" 2 + 5 != 3 + 4 """) is False
        assert toil.walk(r""" 2 + 3 != 3 + 4 """) is True

        assert toil.walk(r""" 2 + 4 < 3 + 4 """) is True
        assert toil.walk(r""" 2 + 5 < 3 + 4 """) is False
        assert toil.walk(r""" 2 + 5 < 2 + 4 """) is False

        assert toil.walk(r""" 2 + 4 > 3 + 4 """) is False
        assert toil.walk(r""" 2 + 5 > 3 + 4 """) is False
        assert toil.walk(r""" 2 + 5 > 2 + 4 """) is True

        assert toil.walk(r""" 2 + 4 <= 3 + 4 """) is True
        assert toil.walk(r""" 2 + 5 <= 3 + 4 """) is True
        assert toil.walk(r""" 2 + 5 <= 2 + 4 """) is False

        assert toil.walk(r""" 2 + 4 >= 3 + 4 """) is False
        assert toil.walk(r""" 2 + 5 >= 3 + 4 """) is True
        assert toil.walk(r""" 2 + 5 >= 2 + 4 """) is True

        assert toil.walk(r""" 2 == 2 == 2 """) is False
        assert toil.walk(r""" a := 2 == 3 + 4 """) is False

        assert toil.walk(r""" True == True """) is True
        assert toil.walk(r""" None == None """) is True
        assert toil.walk(r""" False != True """) is True

        assert toil.walk(r""" [1, 2] == [1, 2] """) is True
        assert toil.walk(r""" [1, 2] == [1, 3] """) is False
        assert toil.walk(r""" {"a": 1} == {"a": 1} """) is True

        assert toil.walk(r""" not 2 + 3 == 4 + 1 """) is False       # not ((2 + 3) == (4 + 1))
        assert toil.walk(r""" 2 + 3 > 4 and 5 < 6 """) is True       # ((2 + 3) > 4) and (5 < 6)

    def test_arithmetic_operations(self):
        assert toil.walk(r""" 2 + 3 """) == 5
        assert toil.walk(r""" 2 + 3 - 4 """) == 1
        assert toil.walk(r""" a := 2 + sub(4, 3) """) == 3

        assert toil.walk(r""" 2 + 3 * 4 """) == 14                   # 2 + (3 * 4)
        assert toil.walk(r""" 2 * 3 + 4 * 5 """) == 26               # (2 * 3) + (4 * 5)
        assert toil.walk(r""" 10 - 4 / 2 """) == 8                   # 10 - (4 / 2)
        assert toil.walk(r""" 2 + 3 == 5 """) is True                # (2 + 3) == 5

    def test_mul_div_mod(self):
        assert toil.walk(r""" 2 * 3 """) == 6
        assert toil.walk(r""" 4 / 2 * 3 """) == 6
        assert toil.walk(r""" 2 * 3 % 4 """) == 2
        assert toil.walk(r""" 2 + 3 * add(4, 5) """) == 29

        assert toil.walk(r""" -2 * 3 """) == -6                      # (-2) * 3
        assert toil.walk(r""" 10 / -2 """) == -5                     # 10 / (-2)
        assert toil.walk(r""" 2 + 3 * 4 == 14 """) is True           # (2 + (3 * 4)) == 14

    def test_unary_operations(self):
        assert toil.walk(r""" -2 """) == -2
        assert toil.walk(r""" --2 """) == 2
        assert toil.walk(r""" 3--2 """) == 5
        assert toil.walk(r""" -add(2, 3) * 4 """) == -20

        assert toil.walk(r""" -2 * 3 """) == -6                      # (-2) * 3
        assert toil.walk(r""" -len([1, 2]) """) == -2                # -(len([1, 2]))
        assert toil.walk(r""" -[1, -2][-1] """) == 2                 # -([1, -2][-1])

    def test_call_index(self):
        assert toil.walk(r""" neg(2) """) == -2
        assert toil.walk(r""" add(2, 3) """) == 5

        toil.walk(r""" a := [2, 3, [4, 5]] """)
        assert toil.walk(r""" a[2][0] """) == 4
        assert toil.walk(r""" a[2][-1] """) == 5

        toil.walk(r""" c := func do [add, sub] end """)
        assert toil.walk(r""" c()[0](2, 3) """) == 5

        toil.walk(r""" e := [1] """)
        with pytest.raises(Exception):
            toil.walk(r""" e[None] = 2 """)
        with pytest.raises(Exception):
            toil.walk(r""" None[2] = 3 """)
        with pytest.raises(Exception):
            toil.walk(r""" [1, 2][5] """)
        with pytest.raises(Exception):
            toil.walk(r""" [1, 2][None] """)
        with pytest.raises(Exception):
            toil.walk(r""" None[0] """)

    def test_dot_notation(self):
        toil.walk(r""" a := {aaa: 2, bbb: 3} """)
        assert toil.walk(r""" a.aaa """) == 2

        toil.walk(r""" a.bbb = 4 """)
        assert toil.walk(r""" a """) == {'aaa': 2, 'bbb': 4}
        toil.walk(r""" a.ccc = 5 """)
        assert toil.walk(r""" a """) == {'aaa': 2, 'bbb': 4, 'ccc': 5}

        with pytest.raises(AssertionError):
            toil.walk(r""" a.not_found """)
        with pytest.raises(AssertionError, match="Invalid attribute"):
            toil.walk(r""" a.1 """)
        with pytest.raises(Exception):
            toil.walk(r""" [2, 3].aaa """)
        with pytest.raises(Exception):
            toil.walk(r""" [2, 3].aaa = 4 """)

    def test_ufcs(self):
        assert toil.walk(r""" 2.add(3) """) == 5
        assert toil.walk(r""" [2, 3, 4].len() """) == 3
        assert toil.walk(r""" [2, 3, 4].len().add(5) """) == 8

        toil.walk(r""" def myadd(a, b) do a + b end """)
        assert toil.walk(r""" 2.myadd(3) """) == 5

        with pytest.raises(AssertionError, match="Undefined variable"):
            toil.walk(r""" 2.not_found() """)
        with pytest.raises(AssertionError, match="Invalid operator"):
            toil.walk(r""" foo := 2; 3.foo() """)

    def test_method_notation(self):
        toil.walk(r""" obj := {
            set: func self, val do self.val = val end,
            add: func self, a do self.val + a end,
            val: None
        } """)
        toil.walk(r""" obj.set(2) """)
        assert toil.walk(r""" obj.val """) == 2
        assert toil.walk(r""" obj.add(3) """) == 5

        assert toil.walk(r""" {a: 2, b: 3}.keys() """) == ['a', 'b']
        assert toil.walk(r""" { len: func self do "local" end }.len() """) == "local"

    def test_none_bool(self):
        assert toil.walk(r""" None """) is None
        assert toil.walk(r""" True """) is True
        assert toil.walk(r""" False """) is False

    def test_numbers(self):
        assert toil.walk(r"""2""") == 2
        assert toil.walk(r"""23""") == 23
        assert toil.walk(r"""0""") == 0
        assert toil.walk(r"""023""") == 23

    def test_raw_string(self):
        assert toil.walk(r""" 'hello, world' """) == "hello, world"
        assert toil.walk(r""" '' """) == ""
        assert toil.walk(r""" 'if ; #"\n' """) == r"""if ; #"\n"""
        assert toil.walk(""" 'a\nb' """) == "a\nb"

        with pytest.raises(AssertionError, match="Unterminated string"):
            toil.walk(r""" ' """)

    def test_string(self):
        assert toil.walk(r""" "hello, world" """) == "hello, world"
        assert toil.walk(r""" "" """) == ""
        assert toil.walk(r""" "if ; #\"\\\n" """) == 'if ; #"\\\n'
        assert toil.walk(""" \"a\nb\" """) == "a\nb"

        with pytest.raises(AssertionError, match="Unterminated string"):
            toil.walk(r""" " """)

        with pytest.raises(AssertionError, match="Unterminated string"):
            toil.walk(r""" "\" """)

    def test_string_functions(self):
        assert toil.walk(r""" join(["ab", "cd", "ef"], ",") """) == "ab,cd,ef"
        assert toil.walk(r""" format("a: {}, b: {}", 1, 2) """) == "a: 1, b: 2"

    def test_grouping(self):
        assert toil.walk(r""" (2 + 3) * 4 """) == 20
        assert toil.walk(r""" (2) * 3 """) == 6

    def test_list(self, capsys):
        assert toil.walk(r""" [] """) == []
        assert toil.walk(r""" [2 + 3] """) == [5]
        assert toil.walk(r""" [2, 3, [4, 5]] """) == [2, 3, [4, 5]]
        toil.walk(r""" [print(2), print(3)] """)

        with pytest.raises(AssertionError, match="Unexpected token"):
            toil.walk(r""" [1, 2,] """)
        assert capsys.readouterr().out == "2\n3\n"

    def test_list_functions(self, capsys):
        toil.walk(r""" d := [2, 3, 4] """)
        assert toil.walk(r""" len(d) """) == 3
        assert toil.walk(r""" index(d, 2) """) == 4
        assert toil.walk(r""" slice(d, 1, None) """) == [3, 4]
        assert toil.walk(r""" slice(d, 1, 2) """) == [3]
        assert toil.walk(r""" slice(d, None, 2) """) == [2, 3]
        assert toil.walk(r""" slice(d, None, None) """) == [2, 3, 4]
        assert toil.walk(r""" push(d, 5) """) is None
        assert toil.walk(r""" d """) == [2, 3, 4, 5]
        assert toil.walk(r""" pop(d) """) == 5
        assert toil.walk(r""" d """) == [2, 3, 4]
        assert toil.walk(r""" in(2, d) """) is True
        assert toil.walk(r""" in(5, d) """) is False
        assert toil.walk(r""" dd := copy(d); dd[0] = 6; [d, dd] """) == [[2, 3, 4], [6, 3, 4]]

        assert toil.walk(r""" [2, 3] + [4, 5] """) == [2, 3, 4, 5]
        assert toil.walk(r""" [2, 3] * 3 """) == [2, 3, 2, 3, 2, 3]

    def test_dict(self):
        assert toil.walk(r""" {} """) == {}

        toil.walk(r""" ccc := 1 """)
        assert toil.walk(r""" a := {"aaa": 2 + 3, bbb: 4, ccc} """) == {'aaa': 5, 'bbb': 4, 'ccc': 1}
        assert toil.walk(r""" a["aaa"] """) == 5

        toil.walk(r""" a["aaa"] = 6 """)
        toil.walk(r""" a["ddd"] = 7 """)
        assert toil.walk(r""" a """) == {'aaa': 6, 'bbb': 4, 'ccc': 1, 'ddd': 7}

        assert toil.walk(r""" {outer: {inner: 1}} """) == {'outer': {'inner': 1}}

        with pytest.raises(AssertionError, match="Expected :"):
            toil.walk(r""" {"aaa"} """)
        with pytest.raises(AssertionError, match="Invalid key"):
            toil.walk(r""" {2: 3} """)
        with pytest.raises(KeyError):
            toil.walk(r""" a["eee"] """)
        with pytest.raises(AssertionError, match="Undefined variable"):
            toil.walk(r""" {undefined_var} """)

        with pytest.raises(AssertionError, match="Expected ,"):
            toil.walk(r""" {"a": 1,} """)

    def test_dict_functions(self):
        assert toil.walk(r""" a := dict([["aaa", 2], ["bbb", 3], ["ccc", 4]]) """) == {'aaa': 2, 'bbb': 3, 'ccc': 4}
        assert toil.walk(r""" len(a) """) == 3
        assert toil.walk(r""" in("aaa", a) """) is True
        assert toil.walk(r""" in("ddd", a) """) is False
        assert toil.walk(r""" keys(a) """) == ['aaa', 'bbb', 'ccc']
        assert toil.walk(r""" items(a) """) == [['aaa', 2], ['bbb', 3], ['ccc', 4]]

    def test_type_functions(self):
        assert toil.walk(r""" type(None) """) == "NoneType"
        assert toil.walk(r""" type(True) """) == "bool"
        assert toil.walk(r""" type(5) """) == "int"
        assert toil.walk(r""" type("") """) == "str"
        assert toil.walk(r""" type([]) """) == "list"
        assert toil.walk(r""" type({}) """) == "dict"

        assert toil.walk(r""" bool(True) """) is True
        assert toil.walk(r""" bool(1) """) is True
        assert toil.walk(r""" int(2) """) == 2
        assert toil.walk(r""" int("2") """) == 2
        assert toil.walk(r""" str("a") """) == "a"
        assert toil.walk(r""" str(2) """) == "2"
        assert toil.walk(r""" list([2, 3]) """) == [2, 3]
        assert toil.walk(r""" list({a: 2, b: 3}) """) == ["a", "b"]
        assert toil.walk(r""" dict({a: 2, b: 3}) """) == {"a": 2, "b": 3}
        assert toil.walk(r""" dict([["a", 2], ["b", 3]]) """) == {"a": 2, "b": 3}
        assert toil.walk(r""" type(tuple([2, 3])) """) == "tuple"

    def test_scope(self):
        assert toil.walk(r""" a := 2; scope a end """) == 2
        assert toil.walk(r""" a := 2; scope scope a end end """) == 2

        assert toil.walk(r""" a := 2; scope a := 3 end """) == 3
        assert toil.walk(r""" a """) == 2

        assert toil.walk(r""" a := 2; scope a = 3 end """) == 3
        assert toil.walk(r""" a """) == 3

        assert toil.walk(r""" a := 2; scope d := 3 end """) == 3
        with pytest.raises(AssertionError, match="Undefined variable"):
            toil.walk(r""" d """)

        assert toil.walk(r"""
            a := 1;
            def f do a := 2; a end;
            [f(), a]
        """) == [2, 1]

    def test_func(self):
        assert toil.walk(r"""func do 2 end ()""") == 2
        assert toil.walk(r"""func a do add(a, 2) end (3)""") == 5
        assert toil.walk(r"""func a, b do add(a, b) end (2, 3)""") == 5

        assert toil.walk(r"""func a, b do add(a, b) end (add(2, 3), 4; 5)""") == 10
        assert toil.walk(r"""
           myadd := func a, b do add(a, b) end;
           myadd(2, 3)
        """) == 5

        with pytest.raises(AssertionError, match="Pattern mismatch"):
            toil.walk(r"""func a, b do add(a, b) end (2)""")

        with pytest.raises(AssertionError, match="Expected do"):
            toil.walk(r"""func a add(a, 2) end""")

        with pytest.raises(AssertionError, match="Expected end"):
            toil.walk(r"""func a do add(a, 2)""")

    def test_destructure_function_arguments(self):
        assert toil.walk(r""" func a, *rest do [a, rest] end (2, 3, 4) """) == [2, [3, 4]]
        assert toil.walk(r""" func {a: d, *rest}, e do [d, e, rest] end ({a: 2, b: 3, c: 4}, 5) """) == [2, 5, {'b': 3, 'c': 4}]

        assert toil.walk(r""" def foo(int(a), str(b)) do [a, b] end; foo(2, "a") """) == [2, "a"]

        with pytest.raises(Exception, match="Pattern mismatch"):
            toil.walk(r""" def bar(int(a), str(b)) do [a, b] end; bar(2, 3) """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            toil.walk(r""" func a, b do [a, b] end (2) """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            toil.walk(r""" func a do a end (2, 3) """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            toil.walk(r""" func do 2 end (2) """)

        assert toil.walk(r""" func do "ok" end () """) == "ok"

    def test_return(self):
        toil.walk(r"""
            def f(a) do
                if a == 2 then return(3) end;
                4
            end
        """)
        assert toil.walk(r""" f(2) """) == 3
        assert toil.walk(r""" f(3) """) == 4

        toil.walk(r"""
            def fib(n) do
                if n == 0 then return(0) end;
                if n == 1 then return(1) end;
                fib(n - 1) + fib(n - 2)
            end
        """)
        assert toil.walk(r""" fib(0) """) == 0
        assert toil.walk(r""" fib(1) """) == 1
        assert toil.walk(r""" fib(6) """) == 8

        assert toil.walk(r""" func do return() end () """) is None

        with pytest.raises(Exception):
            toil.walk(r""" return() """)

        assert toil.walk(r"""
            def find_even(nums) do
                for x in nums do
                    if x % 2 == 0 then return(x) end
                end;
                -1
            end;
            [find_even([1, 3, 5]), find_even([1, 4, 5])]
        """) == [-1, 4]

    def test_def(self):
        toil.walk(r""" def myadd(a, b) do a + b end """)
        assert toil.walk(r""" myadd(2, 3) """) == 5

        toil.walk(r""" def say_hello do "hello" end """)
        assert toil.walk(r""" say_hello() """) == "hello"

        with pytest.raises(Exception, match="Invalid def syntax"):
            toil.walk(r""" def 2 do 3 end """)

    def test_if(self):
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

        assert toil.walk(r""" if 2; True then 1; 2 else 2; 3 end """) == 2
        assert toil.walk(r""" if 2; False then 1; 2 else 2; 3 end """) == 3

        with pytest.raises(AssertionError, match="Expected then"):
            toil.walk(r""" if True 2 end """)
        with pytest.raises(AssertionError, match="Expected end"):
            toil.walk(r""" if True then 2 """)
        with pytest.raises(AssertionError, match="Expected end"):
            toil.walk(r""" if True then 2 3 end """)
        with pytest.raises(AssertionError, match="Expected end"):
            toil.walk(r""" if True then 2 else 3 """)
        with pytest.raises(AssertionError, match="Expected then"):
            toil.walk(r""" if False then 2 elif True 3 end """)
        with pytest.raises(AssertionError, match="Expected end"):
            toil.walk(r""" if False then 2 elif True then 3 """)

    def test_match_syntax(self):
        assert toil.walk(r""" match 2 end """) is None

        with pytest.raises(Exception, match="Expected end"):
            toil.walk(r""" match end """)
        with pytest.raises(Exception, match="Expected end"):
            toil.walk(r""" match 2 case 2 then 3 """)
        with pytest.raises(Exception, match="Expected end"):
            toil.walk(r""" match 2 then 3 end """)
        with pytest.raises(Exception, match="Expected then"):
            toil.walk(r""" match 2 case then 3 end """)

    def test_match_variable_and_literal(self):
        assert toil.walk(r""" match 2 case a then a + 1 case _ then "no" end """) == 3
        assert toil.walk(r""" match 2 case 3 then "yes" end """) is None
        assert toil.walk(r""" match 2 case 2 then "yes" case _ then "no" end """) == "yes"
        assert toil.walk(r""" match 2 case 3 then "yes" case _ then "no" end """) == "no"
        assert toil.walk(r""" match [] case 3 then "yes" case _ then "no" end """) == "no"
        assert toil.walk(r""" match None case None then "yes" case _ then "no" end """) == "yes"
        assert toil.walk(r""" match 2 case None then "yes" case _ then "no" end """) == "no"
        assert toil.walk(r""" match True case True then "yes" case _ then "no" end """) == "yes"
        assert toil.walk(r""" match False case True then "yes" case _ then "no" end """) == "no"
        assert toil.walk(r""" match False case False then "yes" case _ then "no" end """) == "yes"
        assert toil.walk(r""" match True case False then "yes" case _ then "no" end """) == "no"
        assert toil.walk(r""" match "hello" case "hello" then "yes" case _ then "no" end """) == "yes"
        assert toil.walk(r""" match "world" case "hello" then "yes" case _ then "no" end """) == "no"

    def test_match_list(self):
        assert toil.walk(r""" match [] case [] then "yes" case _ then "no" end """) == "yes"
        assert toil.walk(r""" match 2 case [] then "yes" case _ then "no" end """) == "no"
        assert toil.walk(r""" match [2] case [a] then a + 1 case _ then "no" end """) == 3
        assert toil.walk(r""" match [2, 3] case [a] then a + 1 case _ then "no" end """) == "no"
        assert toil.walk(r""" match [2, 3] case [a, b] then a * b case _ then "no" end """) == 6
        assert toil.walk(r""" match [2] case [a, b] then a * b case _ then "no" end """) == "no"
        assert toil.walk(r""" match [] case [a, *b] then [a, b] case _ then "no" end """) == "no"
        assert toil.walk(r""" match [2] case [a, *b] then [a, b] case _ then "no" end """) == [2, []]
        assert toil.walk(r""" match [3, 4] case [a, *b] then [a, b] case _ then "no" end """) == [3, [4]]
        assert toil.walk(r""" match [4, 5, 6] case [a, *b] then [a, b] case _ then "no" end """) == [4, [5, 6]]
        assert toil.walk(r""" match [] case [*a, b] then [a, b] case _ then "no" end """) == "no"
        assert toil.walk(r""" match [2] case [*a, b] then [a, b] case _ then "no" end """) == [[], 2]
        assert toil.walk(r""" match [3, 4] case [*a, b] then [a, b] case _ then "no" end """) == [[3], 4]
        assert toil.walk(r""" match [4, 5, 6] case [*a, b] then [a, b] case _ then "no" end """) == [[4, 5], 6]
        assert toil.walk(r""" match [2] case [a, *b, c] then [a, b, c] case _ then "no" end """) == "no"
        assert toil.walk(r""" match [3, 4] case [a, *b, c] then [a, b, c] case _ then "no" end """) == [3, [], 4]
        assert toil.walk(r""" match [4, 5, 6] case [a, *b, c] then [a, b, c] case _ then "no" end """) == [4, [5], 6]
        assert toil.walk(r""" match [5, 6, 7, 8] case [a, *b, c] then [a, b, c] case _ then "no" end """) == [5, [6, 7], 8]
        assert toil.walk(r""" match [2] case [*a, *b] then [a, b] case _ then "no" end """) == "no"

    def test_match_dict_cases(self):
        assert toil.walk(r""" match {} case {} then "yes" case _ then "no" end """) == "yes"
        assert toil.walk(r""" match 2 case {} then "yes" case _ then "no" end """) == "no"
        assert toil.walk(r""" match {a: 2} case {} then "yes" case _ then "no" end """) == "yes"

        assert toil.walk(r""" match {a: 2} case {a: 2} then "yes" end """) == "yes"
        assert toil.walk(r""" match {a: 2} case {a: 3} then "yes" end """) is None
        assert toil.walk(r""" match {a: 2} case {a: a} then a end """) == 2
        assert toil.walk(r""" match {a: 3} case {a: b} then b end """) == 3
        assert toil.walk(r""" match {a: 4} case {a} then a end """) == 4
        assert toil.walk(r""" match {a: 5} case {"a": a} then a end """) == 5
        assert toil.walk(r""" match {a: 6, b: 7} case {a} then a end """) == 6
        assert toil.walk(r""" match {a: 7, b: 8} case {a, b} then [a, b] end """) == [7, 8]
        assert toil.walk(r""" match {a: 8, b: 9} case {a: _, b} then b end """) == 9
        assert toil.walk(r""" match {a: 2} case {b} then a end """) is None
        assert toil.walk(r""" match {a: 2} case {a, b} then a end """) is None

        assert toil.walk(r""" match {a: 2} case {*rest} then rest end """) == {'a': 2}
        assert toil.walk(r""" match {a: 3} case {a, *rest} then [a, rest] end """) == [3, {}]
        assert toil.walk(r""" match {a: 3} case {b, *rest} then [b, rest] end """) is None
        assert toil.walk(r""" match {a: 4, b: 5} case {a, *rest} then [a, rest] end """) == [4, {'b': 5}]
        assert toil.walk(r""" match {a: 5, b: 6, c: 7} case {a, *rest} then [a, rest] end """) == [5, {'b': 6, 'c': 7}]

    def test_match_ident_and_expr(self):
        assert toil.walk(r""" match Ident("aaa") case Ident("aaa") then "yes" end """) == "yes"
        assert toil.walk(r""" match Ident("aaa") case "aaa" then "yes" end """) is None
        assert toil.walk(r""" match Ident("aaa") case Ident("bbb") then "yes" end """) is None
        assert toil.walk(r""" match Ident("aaa") case Ident(a) then [a] end """) == ['aaa']

        assert toil.walk(r""" match tuple(Ident("add"), [Ident("a"), Ident("b")]) case tuple(Ident("add"), [Ident(name1), Ident(name2)]) then [name1, name2] end """) == ["a", "b"]
        assert toil.walk(r""" match 2 + 3 case tuple(Ident("add"), [Ident(name1), Ident(name2)]) then [name1, name2] end """) is None
        assert toil.walk(r""" match tuple(Ident("add")) case tuple(Ident("add"), [Ident(name1), Ident(name2)]) then [name1, name2] end """) is None

    def test_match_type_and_or(self):
        assert toil.walk(r""" match 2 case int(a) then a end """) == 2
        assert toil.walk(r""" match "2" case int(a) then a end """) is None
        assert toil.walk(r""" match "aaa" case str(a) then [a] end """) == ['aaa']
        assert toil.walk(r""" match [] case str(a) then [a] end """) is None

        assert toil.walk(r""" match 2 case int(a) or str(a) then [a] end """) == [2]
        assert toil.walk(r""" match "aaa" case int(a) or str(a) then [a] end """) == ['aaa']
        assert toil.walk(r""" match [2] case int(a) or str(a) then [a] end """) is None
        assert toil.walk(r""" match [2] case int(a) or str(a) or list(a) then [a] end """) == [[2]]

    def test_match_combination(self):
        assert toil.walk(r""" match [{a: 2, b: 3}, 4] case  [{a: b}, c] then [b, c] end """) == [2, 4]
        assert toil.walk(r""" match {a: [5, 6]} case {a: [b, c]} then [b, c] end """) == [5, 6]

    def test_match_control_flow(self):
        assert toil.walk(r""" a := 0; match 2 case 2 then a = 1 case _ then a = 2 end; a """) == 1
        assert toil.walk(r""" match [2, 3] case [a, b] then "ok" end; a + b """) == 5
        assert toil.walk(r""" match [2, 3] case [a, 4] then "no" case _ then a end """) == 2

    def test_while(self):
        assert toil.walk(r""" i := 0; while i < 2 do i = i + 1 end """) == None
        assert toil.walk(r"""
            a := [];
            i := 0; while i < 3 do push(a, i); i = i + 1 end;
            a
        """) == [0, 1, 2]

        assert toil.walk(r"""
            a := [];
            i := 0; while i < 3 do push(a, i); i = i + 1 then a else 1/0 end
        """) == [0, 1, 2]

        assert toil.walk(r"""
            a := [];
            i := 0; while i < 3 do push(a, i); i = i + 1 then a end
        """) == [0, 1, 2]

        assert toil.walk(r""" while False do 1 / 0 then 3 else 4 end """) == 3

        with pytest.raises(Exception, match="Expected do"):
            toil.walk(r""" while do 2 then 3 else 4 end """)
        with pytest.raises(Exception, match="Expected do"):
            toil.walk(r""" while True 2 then 3 else 4 end """)
        with pytest.raises(Exception, match="Expected end"):
            toil.walk(r""" while True do 2 3 else 4 end """)
        with pytest.raises(Exception, match="Expected end"):
            toil.walk(r""" while True do 2 then 3 4 end """)
        with pytest.raises(Exception, match="Expected end"):
            toil.walk(r""" while True do 2 then 3 else end """)
        with pytest.raises(Exception, match="Expected end"):
            toil.walk(r""" while True do 2 then 3 else 4 """)

    def test_continue(self):
        assert toil.walk(r"""
            a := [];
            i := 0; while i < 3 do
                i = i + 1; if i == 2 then continue end;
                push(a, i)
            then a end
        """) == [1, 3]

        assert toil.walk(r"""
            a := []; i := 0; while i < 2 do
                j := 0; while j < 3 do
                    j = j + 1; if j == 2 then continue end;
                    push(a, [i, j])
                end;
                i = i + 1
            then a end
        """) == [[0, 1], [0, 3], [1, 1], [1, 3]]

        with pytest.raises(Exception, match="Continue at top level"):
            toil.walk(r""" continue """)

    def test_break(self):
        assert toil.walk(r""" i := 0; while i < 2 do break end """) == None
        assert toil.walk(r"""
            a := [];
            i := 0; while i < 3 do
                if i == 1 then break end;
                push(a, i); i = i + 1
            then 1/0 else a end
        """) == [0]

        assert toil.walk(r"""
            a := [];
            i := 0; while i < 3 do
                if i == 1 then break end;
                push(a, i); i = i + 1
            else a end
        """) == [0]

        assert toil.walk(r"""
            a := [];
            i := 0; while i < 2 do
                j := 0; while j < 3 do
                    if i == 0 and j == 1 then break end;
                    push(a, [i, j]);
                    j = j + 1
                end;
                i = i + 1
            then a end
        """) == [[0, 0], [1, 0], [1, 1], [1, 2]]

        assert toil.walk(r"""
            a := [];
            i := 0; while i < 2 do
                j := 0; while j < 3 do
                    if i == 1 and j == 1 then break end;
                    push(a, [i, j]);
                    j = j + 1
                else break end;
                i = i + 1
            else a end
        """) == [[0, 0], [0, 1], [0, 2], [1, 0]]

        assert toil.walk(r""" while True do break end """) is None
        assert toil.walk(r""" while True do break else 2 end """) == 2

        with pytest.raises(Exception, match="Break at top level"):
            toil.walk(r""" break """)

    def test_for(self):
        assert toil.walk(r""" a := []; for i in [0, 1, 2] do push(a, i) end; a """) == [0, 1, 2]

        assert toil.walk(r"""
            a := []; for i in [0, 1, 2] do push(a, i) then [i, a] else 1/0 end
        """) == [2, [0, 1, 2]]

        assert toil.walk(r"""
            a := []; for i in [0, 1, 2] do push(a, i) then a end
        """) == [0, 1, 2]

        assert toil.walk(r"""
            a := []; for [i, j] in [[1, 2], [3, 4]] do push(a, [i, j]) then a end
        """) == [[1, 2], [3, 4]]

        assert toil.walk(r"""
            a := [];
            for [k, v] in {"a": 2, "b": 3}.items() do push(a, [k, v]) then a end
        """) == [['a', 2], ['b', 3]]

        assert toil.walk(r"""
            a := [];
            keys := ["a", "b", "c"];
            values := [2, 3, 4];
            for [k, v] in zip(keys, values) do push(a, [k, v]) then a end
        """) == [['a', 2], ['b', 3], ['c', 4]]

        assert toil.walk(r""" for i in [] do 1/0 then 2 end """) == 2

        with pytest.raises(Exception):
            toil.walk(r""" for in [] do 2 then 3 else 4 end """)
        with pytest.raises(Exception):
            toil.walk(r""" for i [] do 2 then 3 else 4 end """)
        with pytest.raises(Exception, match="Expected do"):
            toil.walk(r""" for i in do 2 then 3 else 4 end """)
        with pytest.raises(Exception, match="Expected end"):
            toil.walk(r""" for i in [] do then 3 else 4 end """)
        with pytest.raises(Exception, match="Expected end"):
            toil.walk(r""" for i in [] do 2 3 else 4 end """)
        with pytest.raises(Exception, match="Expected end"):
            toil.walk(r""" for i in [] do 2 then else 4 end """)
        with pytest.raises(Exception, match="Expected end"):
            toil.walk(r""" for i in [] do 2 then 3 4 end """)
        with pytest.raises(Exception, match="Expected end"):
            toil.walk(r""" for i in [] do 2 then 3 else end """)
        with pytest.raises(Exception, match="Expected end"):
            toil.walk(r""" for i in [] do 2 then 3 else 4 """)

    def test_for_continue(self):
        assert toil.walk(r"""
            a := []; for i in [0, 1, 2] do
                if i == 1 then continue end;
                push(a, i)
            then a end
        """) == [0, 2]

        assert toil.walk(r"""
            a := []; for i in [0, 1] do
                for j in [0, 1, 2] do
                    if j == 1 then continue end;
                    push(a, [i, j])
                end
            then a end
        """) == [[0, 0], [0, 2], [1, 0], [1, 2]]

    def test_for_break(self):
        assert toil.walk(r"""
            a := []; for i in [0, 1, 2] do
                if i == 1 then break end;
                push(a, i)
            then 1/0 else a end
        """) == [0]

        assert toil.walk(r"""
            a := []; for i in [0, 1, 2] do
                if i == 1 then break end;
                push(a, i)
            else a end
        """) == [0]

        assert toil.walk(r"""
            a := [];
            for i in [0, 1] do
                for j in [0, 1, 2] do
                    if i == 0 and j == 1 then break end;
                    push(a, [i, j])
                end
            then a end
        """) == [[0, 0], [1, 0], [1, 1], [1, 2]]

        assert toil.walk(r"""
            a := [];
            for i in [0, 1] do
                for j in [0, 1, 2] do
                    if i == 1 and j == 1 then break end;
                    push(a, [i, j])
                else break end
            else a end
        """) == [[0, 0], [0, 1], [0, 2], [1, 0]]

    def test_try_except(self):
        assert toil.walk(r""" try 2; 3 end """) == 3
        assert toil.walk(r""" try 2; 3 except e then e end """) == 3
        assert toil.walk(r""" try 2; raise(2 + 3); 3 except e then e end """) == 5

        assert toil.walk(r"""
            try
                raise(["foo", 3])
            except ["foo", val] then ["foo", val]
            except ["bar", val] then ["bar", val]
            end
        """) == ['foo', 3]

        assert toil.walk(r"""
            try
                raise(["bar", 3])
            except ["foo", val] then ["foo", val]
            except ["bar", val] then ["bar", val]
            end
        """) == ['bar', 3]

        with pytest.raises(Exception):
            toil.walk(r"""
                try
                    raise(["baz", 3])
                except ["foo", val] then ["foo", val]
                end
            """)

        assert toil.walk(r""" try raise(2) except _ then 3 end """) == 3

        assert toil.walk(r""" func do try return(2) except _ then 3 end end () """) == 2

        assert toil.walk(r"""
            a := 0; while a < 5 do
                try a = a + 1; if a == 3 then break end
                except _ then a = 10 end
            end; a
        """) == 3

        assert toil.walk(r"""
            try
                try
                    raise(2)
                except e then
                    raise(e + 1)
                end
            except e then
                e
            end
        """) == 3

        assert toil.walk(r"""
            try
                try
                    raise("outer")
                except "inner" then "caught inner"
                end
            except "outer" then "caught outer"
            end
        """) == "caught outer"

    def test_defclass(self):
        assert toil.walk(r"""
            defclass Counter(start) do
                self.count = start;
                defmethod inc(step) do
                    self.count = self.count + step
                end;
                defmethod get do
                    self.count
                end
            end;
            c1 := Counter(10);
            c2 := Counter(20);
            c1.inc(2);
            c2.inc(5);
            [c1.get(), c2.get()]
        """) == [12, 25]

        with pytest.raises(Exception, match="Invalid defclass syntax"):
            toil.walk(r""" defclass 2 do 2 end """)
        with pytest.raises(Exception, match="Expected do"):
            toil.walk(r""" defclass Foo(x) end """)
        with pytest.raises(Exception, match="Invalid defmethod syntax"):
            toil.walk(r""" defclass Foo do defmethod 2 do end end """)

    def test_assert(self):
        assert toil.walk(r""" assert 2 == 2 else 1/0 end """) is None

        with pytest.raises(Exception, match="Assert exception"):
            toil.walk(r""" assert 2 == 3 else "Assert exception" end """)

        with pytest.raises(Exception, match="Expected else"):
            toil.walk(r""" assert 2 == 3 "Assert exception" end """)

        with pytest.raises(Exception, match="Expected end"):
            toil.walk(r""" assert 2 == 3 else "Assert exception" """)

    def test_read_load(self, tmp_path):
        assert toil.walk(r""" type(read("scripts/fib.toil")) """) == "str"
        assert toil.walk(r""" load("scripts/fib.toil")(4) """) == 3

    def test_eval_apply(self):
        assert toil.walk(r""" eval("2 + 3") """) == 5
        assert toil.walk(r""" eval_expr(tuple(Ident("add"), [2, 3])) """) == 5
        assert toil.walk(r""" apply(add, [2, 3]) """) == 5
        assert toil.walk(r""" apply(func a, b do a + b end, [2, 3]) """) == 5

    def test_stdlib(self):
        assert toil.walk(r""" a := range(2, 10, 1) """) == [2, 3, 4, 5, 6, 7, 8, 9]
        assert toil.walk(r""" b := range(2, 10, 3) """) == [2, 5, 8]
        assert toil.walk(r""" first(a) """) == 2
        assert toil.walk(r""" rest(a) """) == [3, 4, 5, 6, 7, 8, 9]
        assert toil.walk(r""" last(a) """) == 9
        assert toil.walk(r""" map(a, n -> n * 2) """) == [4, 6, 8, 10, 12, 14, 16, 18]
        assert toil.walk(r""" filter(a, n -> n % 2 == 0) """) == [2, 4, 6, 8]
        assert toil.walk(r""" reverse(a) """) == [9, 8, 7, 6, 5, 4, 3, 2]
        assert toil.walk(r""" reverse([]) """) == []
        assert toil.walk(r""" zip(a, [4, 5, 6]) """) == [[2, 4], [3, 5], [4, 6]]
        assert toil.walk(r""" enumerate(a) """) == [[0, 2], [1, 3], [2, 4], [3, 5], [4, 6], [5, 7], [6, 8], [7, 9]]
        assert toil.walk(r""" all([True, True], x -> x) """) is True
        assert toil.walk(r""" all([True, False], x -> x) """) is False
        assert toil.walk(r""" any([False, True], x -> x) """) is True
        assert toil.walk(r""" any([False, False], x -> x) """) is False

    def test_macro(self):
        assert toil.walk(r""" macro do 2 + 3 end () """) == 5
        assert toil.walk(r""" macro cond, body do tuple(Ident('if'), [cond, body, None]) end (2 == 3, 1/0) """) is None

        toil.walk(r""" when := macro cond, body do tuple(Ident('if'), [cond, body, None]) end """)
        toil.walk(r""" a := 2; b := 3 """)
        assert toil.walk(r""" when(a == b, 1 / 0) """) is None

        toil.walk(r"""
            def test_macro_scope() do
                local_when := macro cond, body do tuple(Ident('if'), [cond, body, None]) end;
                local_when(2 == 2, 3)
            end
        """)
        assert toil.walk(" test_macro_scope() ") == 3
        with pytest.raises(AssertionError, match="Undefined variable"):
            toil.walk(" local_when(2 == 2, 3) ")

        toil.walk(r""" def when_func(cond, body) do if cond then body end end """)
        with pytest.raises(Exception):
            toil.walk(r""" when_func(a == b, 1 / 0) """)

        toil.walk(r""" unless := macro cond, body do tuple(Ident('when'), [tuple(Ident('not'), [cond]), body]) end """)
        assert toil.walk(r""" unless(a == b, 2 + 3) """) == 5

        toil.walk(r""" obj := { when: func self, cond, body do "method called" end } """)
        assert toil.walk(r""" obj.when(True, "foo") """) == "method called"

        toil.walk(r"""
            multi_and := macro a, *rest do
                if len(rest) == 0 then
                    a
                else
                    tuple(Ident('if'), [a, tuple(Ident('multi_and'), rest), False])
                end
            end
        """)
        assert toil.walk(r""" multi_and(1 == 1) """) is True
        assert toil.walk(r""" multi_and(1 == 1, 2 == 2, 3 == 3) """) is True
        assert toil.walk(r""" multi_and(False, 1 / 0) """) is False

        with pytest.raises(AssertionError, match="Pattern mismatch"):
            toil.walk(r""" when(True) """)

    def test_quote(self):
        assert toil.walk(r""" quote 2 + 3 end """) == (Ident("add"), [2, 3])
        assert toil.walk(r""" a := 2; quote a + 3 end """) == (Ident("add"), [Ident("a"), 3])
        assert toil.walk(r""" quote !(2 + 3) end """) == 5
        assert toil.walk(r""" a := 2; quote !(a + 3) end """) == 5
        assert toil.walk(r""" quote [2, 3, 4, 5] end """) == [2, 3, 4, 5]
        assert toil.walk(r""" a := [3, 4]; quote [2, !!a, 5] end """) == [2, 3, 4, 5]
        assert toil.walk(r""" a := 2; quote {a: !a, b: 3} end """) == {'a': 2, 'b': 3}
        assert toil.walk(r""" a := [3, 4]; quote { list: [2, !!a, 5] } end """) == {'list': [2, 3, 4, 5]}
        with pytest.raises(AssertionError, match="Undefined variable"):
            toil.walk(r""" !(2 + 3) """)

        toil.walk(r""" when := macro cond, body do quote if !cond then !body else None end end end """)
        toil.walk(r""" a := 2; b := 3 """)
        assert toil.walk(r""" when(a == b, 1 / 0) """) is None

        toil.walk(r""" unless := macro cond, body do quote when(not !cond, !body) end end """)
        assert toil.walk(r""" unless(a == b, 2 + 3) """) == 5

        toil.walk(r"""
            multi_and := macro a, *rest do
                if rest == [] then a else
                    quote if !a then multi_and(!!rest) else False end end
                end
            end
        """)
        assert toil.walk(r""" multi_and(1 == 1) """) is True
        assert toil.walk(r""" multi_and(1 == 1, 2 == 2, 3 == 3) """) is True
        assert toil.walk(r""" multi_and(False, 1 / 0) """) is False

    def test_defmacro_(self):
        toil.walk(r""" defmacro_(MAGIC_NUMBER, 2) """)
        assert toil.walk(r""" MAGIC_NUMBER() + 3 """) == 5

        toil.walk(r""" defmacro_(when(cond, body),
            quote if !cond then !body else None end end
        ) """)
        toil.walk(r""" a := 2; b := 3 """)
        assert toil.walk(r""" when(a == b, 1 / 0) """) is None

        toil.walk(r""" defmacro_(unless(cond, body),
            quote when(not !cond, !body) end
        ) """)
        assert toil.walk(r""" unless(a == b, 2 + 3) """) == 5

        toil.walk(r""" defmacro_(multi_and(a, *rest),
            if rest == [] then a else
                quote if !a then multi_and(!!rest) else False end end
            end
        ) """)
        assert toil.walk(r""" multi_and(1 == 1, 2 == 2, 3 == 3) """) is True
        assert toil.walk(r""" multi_and(False, 1 / 0) """) is False

        with pytest.raises(Exception, match="Invalid defmacro syntax"):
            toil.walk(r""" defmacro_(2, 3) """)

        toil.walk(r"""
            def test_macro_scope() do
                defmacro_(local_macro(), 2);
                local_macro()
            end
        """)
        assert toil.walk(r""" test_macro_scope() """) == 2
        with pytest.raises(AssertionError, match="Undefined variable"):
            toil.walk(r""" local_macro() """)

    def test_def_(self):
        toil.walk(r""" def_(myadd(a, b), a + b) """)
        assert toil.walk(r""" myadd(2, 3) """) == 5

        toil.walk(r""" def_(say_hello(), "hello") """)
        assert toil.walk(r""" say_hello() """) == "hello"

        toil.walk(r""" def_(say_world, "world") """)
        assert toil.walk(r""" say_world() """) == "world"

        with pytest.raises(Exception, match="Invalid def syntax"):
            toil.walk(r""" def_(2, 3) """)

    def test_whitespace(self):
        assert toil.walk(r"""   2 """) == 2
        assert toil.walk(r""" 2   """) == 2
        assert toil.walk("""\n  2  \n""") == 2

    def test_comment(self):
        assert toil.walk(r""" 2 # 3 """) == 2
        assert toil.walk(r"""
            # 2
            3
            # 4
          """) == 3

    def test_empty_source(self):
        with pytest.raises(AssertionError, match="Unexpected token"):
            toil.walk(r"""  """)

    def test_invalid_character(self):
        with pytest.raises(AssertionError, match="Invalid character"):
            toil.walk(r""" ~ """)

    def test_extra_token(self):
        with pytest.raises(AssertionError, match="Extra token"):
            toil.walk(r""" 2 3 """)

class TestExamples:
    def test_recursion_gcd(self):
        toil.walk(r"""
            def gcd(a, b) do
                if b == 0 then a else gcd(b, a % b) end
            end
        """)
        assert toil.walk(r"""gcd(12, 18)""") == 6

    def test_iteration_gcd(self):
        toil.walk(r"""
            def gcd(a, b) do
                while b > 0 do
                    tmp := b; b = a % b; a = tmp
                end;
                a
            end
        """)
        assert toil.walk(r"""gcd(12, 18)""") == 6

    def test_recursion_fac(self):
        toil.walk(r"""
            def fac(n) do
                if n == 0 then 1 else n * fac(n - 1) end
            end
        """)
        assert toil.walk(r"""fac(0)""") == 1
        assert toil.walk(r"""fac(1)""") == 1
        assert toil.walk(r"""fac(4)""") == 24

    def test_iteration_fac(self):
        toil.walk(r"""
            def fac(n) do
                result := 1;
                for n in range(1, n + 1, 1) do
                    result = result * n
                then result end
            end
        """)
        assert toil.walk(r"""fac(0)""") == 1
        assert toil.walk(r"""fac(1)""") == 1
        assert toil.walk(r"""fac(4)""") == 24

    def test_recursion_fib(self):
        toil.walk(r"""
            def fib(n) do
                if n == 0 then 0
                elif n == 1 then 1
                else fib(n - 1) + fib(n - 2)
                end
            end
        """)
        assert toil.walk(r"""fib(0)""") == 0
        assert toil.walk(r"""fib(1)""") == 1
        assert toil.walk(r"""fib(6)""") == 8

    def test_iteration_fib(self):
        toil.walk(r"""
            def fib(n) do
                a := 0; b := 1;
                for n in range(0, n, 1) do
                    tmp := b; b = a + b; a = tmp
                then a end
            end
        """)
        assert toil.walk(r"""fib(0)""") == 0
        assert toil.walk(r"""fib(1)""") == 1
        assert toil.walk(r"""fib(6)""") == 8

    def test_mutual_recursion(self):
        toil.walk(r"""
            def even(n) do if n == 0 then True else odd(n - 1) end end;
            def odd(n) do if n == 0 then False else even(n - 1) end end
        """)
        assert toil.walk(r"""even(2)""") is True
        assert toil.walk(r"""even(3)""") is False
        assert toil.walk(r"""odd(2)""") is False
        assert toil.walk(r"""odd(3)""") is True

    def test_closure_counter(self):
        toil.walk(r"""
            def make_counter do
                count := 0;
                func do count = count + 1 end
            end;

            c1 := make_counter();
            c2 := make_counter()
        """)
        assert toil.walk(r"""c1()""") == 1
        assert toil.walk(r"""c1()""") == 2
        assert toil.walk(r"""c2()""") == 1
        assert toil.walk(r"""c2()""") == 2

    def test_bubblesort(self):
        assert toil.walk(r"""
            def bubblesort(a) do
                n := len(a);
                for i in range(0, n, 1) do
                    for j in range(0, n - i - 1, 1) do
                        if a[j] > a[j + 1] then
                            tmp := a[j]; a[j] = a[j + 1]; a[j + 1] = tmp
                        end
                    end
                then a end
            end;

            bubblesort([5, 3, 8, 4, 2])
        """) == [2, 3, 4, 5, 8]

    def test_quicksort(self):
        assert toil.walk(r"""
            def quicksort(a) do
                if len(a) <= 1 then a else
                    pivot := first(a); rem := rest(a);
                    left := rem.filter(x -> x < pivot);
                    right := rem.filter(x -> x >= pivot);
                    quicksort(left) + [pivot] + quicksort(right)
                end
            end;

            quicksort([5, 3, 8, 4, 2])
        """) == [2, 3, 4, 5, 8]

    def test_sieve(self):
        assert toil.walk(r"""
            def sieve(n) do
                s := [False, False] + [True] * (n - 2);
                i := 2; while i * i < n do
                    if s[i] then
                        for j in range(i * i, n, i) do s[j] = False end
                    end;
                    i = i + 1
                end;

                enumerate(s).filter(last).map(first)
            end;

            sieve(10)
        """) == [2, 3, 5, 7]

    def test_poor_mans_object(self, capsys):
        toil.walk(r"""
            def Animal(name) do
                self := {};
                self._name = name;
                self.introduce = func self do print("I am", self._name) end;
                self.make_sound = func self do print("crying") end;
                self
            end
        """)
        toil.walk(r"""
            animal1 := Animal("Rocky");
            animal2 := Animal("Lucy");
            animal1.introduce();
            animal1.make_sound();
            animal2.introduce();
            animal2.make_sound()
        """)
        assert capsys.readouterr().out == "I am Rocky\ncrying\nI am Lucy\ncrying\n"

        toil.walk(r"""
            def Dog(name) do
                self := Animal(name);
                self.make_sound = func self do print("woof") end;
                self
            end
        """)
        toil.walk(r"""
            dog1 := Dog("Leo");
            dog1.introduce();
            dog1.make_sound()
        """)
        assert capsys.readouterr().out == "I am Leo\nwoof\n"

    def test_lazy_evaluation_with_thunks(self):
        assert toil.walk(r"""
            def force(thunk) do thunk() end;
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
                tuple(n, [] -> count_from(n + 1))
            end;

            take(5, count_from(1))
        """) == [1, 2, 3, 4, 5]

if __name__ == "__main__":
    pytest.main([__file__])
