import pytest
from toil import Ident
from toil_on_toil import i


class TestFunctions:
    def test_isalpha(self):
        assert i.walk(""" isalpha("a") """) is True
        assert i.walk(""" isalpha("z") """) is True
        assert i.walk(""" isalpha("A") """) is True
        assert i.walk(""" isalpha("Z") """) is True
        assert i.walk(""" isalpha("0") """) is False
        assert i.walk(""" isalpha("9") """) is False
        assert i.walk(""" isalpha("_") """) is False
        assert i.walk(""" isalpha("$") """) is False
        assert i.walk(""" isalpha(" ") """) is False
        assert i.walk(""" isalpha("\n") """) is False
        assert i.walk(r""" isalpha("\n") """) is False

    def test_isdigit(self):
        assert i.walk(""" isdigit("a") """) is False
        assert i.walk(""" isdigit("z") """) is False
        assert i.walk(""" isdigit("A") """) is False
        assert i.walk(""" isdigit("Z") """) is False
        assert i.walk(""" isdigit("0") """) is True
        assert i.walk(""" isdigit("9") """) is True
        assert i.walk(""" isdigit("_") """) is False
        assert i.walk(""" isdigit("$") """) is False
        assert i.walk(""" isdigit(" ") """) is False
        assert i.walk(""" isdigit("\n") """) is False
        assert i.walk(r""" isdigit("\n") """) is False

    def test_isalnum(self):
        assert i.walk(""" isalnum("a") """) is True
        assert i.walk(""" isalnum("z") """) is True
        assert i.walk(""" isalnum("A") """) is True
        assert i.walk(""" isalnum("Z") """) is True
        assert i.walk(""" isalnum("0") """) is True
        assert i.walk(""" isalnum("9") """) is True
        assert i.walk(""" isalnum("_") """) is False
        assert i.walk(""" isalnum("$") """) is False
        assert i.walk(""" isalnum(" ") """) is False
        assert i.walk(""" isalnum("\n") """) is False
        assert i.walk(r""" isalnum("\n") """) is False

    def test_isspace(self):
        assert i.walk(""" isspace("a") """) is False
        assert i.walk(""" isspace("z") """) is False
        assert i.walk(""" isspace("A") """) is False
        assert i.walk(""" isspace("Z") """) is False
        assert i.walk(""" isspace("0") """) is False
        assert i.walk(""" isspace("9") """) is False
        assert i.walk(""" isspace("_") """) is False
        assert i.walk(""" isspace("$") """) is False
        assert i.walk(""" isspace(" ") """) is True
        assert i.walk(""" isspace("\n") """) is True
        assert i.walk(r""" isspace("\n") """) is True

    def test_is_ident_first(self):
        assert i.walk(""" is_ident_first("a") """) is True
        assert i.walk(""" is_ident_first("z") """) is True
        assert i.walk(""" is_ident_first("A") """) is True
        assert i.walk(""" is_ident_first("Z") """) is True
        assert i.walk(""" is_ident_first("0") """) is False
        assert i.walk(""" is_ident_first("9") """) is False
        assert i.walk(""" is_ident_first("_") """) is True
        assert i.walk(""" is_ident_first("$") """) is False
        assert i.walk(""" is_ident_first(" ") """) is False
        assert i.walk(""" is_ident_first("\n") """) is False
        assert i.walk(r""" is_ident_first("\n") """) is False

    def test_is_ident_rest(self):
        assert i.walk(""" is_ident_rest("a") """) is True
        assert i.walk(""" is_ident_rest("z") """) is True
        assert i.walk(""" is_ident_rest("A") """) is True
        assert i.walk(""" is_ident_rest("Z") """) is True
        assert i.walk(""" is_ident_rest("0") """) is True
        assert i.walk(""" is_ident_rest("9") """) is True
        assert i.walk(""" is_ident_rest("_") """) is True
        assert i.walk(""" is_ident_rest("$") """) is False
        assert i.walk(""" is_ident_rest(" ") """) is False
        assert i.walk(""" is_ident_rest("\n") """) is False
        assert i.walk(r""" is_ident_rest("\n") """) is False

    def test_is_ident(self):
        assert i.walk(""" is_ident("a") """) is True
        assert i.walk(""" is_ident("_abc") """) is True
        assert i.walk(""" is_ident("0a") """) is False
        assert i.walk(""" is_ident("$a") """) is False
        assert i.walk(""" is_ident(" a") """) is False

    def test_in(self):
        assert i.walk(""" in(2, [1, 2, 3]) """) is True
        assert i.walk(""" in(4, [1, 2, 3]) """) is False
        assert i.walk(""" 2.in([1, 2, 3]) """) is True
        assert i.walk(""" 4.in([1, 2, 3]) """) is False
        assert i.walk(""" 'a'.in({'a': 2, 'b': 3}) """) is True
        assert i.walk(""" 'c'.in({'a': 2, 'b': 3}) """) is False


class TestBase:
    @pytest.fixture(scope="class", autouse=True)
    def setup_tot(self):
        i.walk(""" tot := Interpreter() """)

    @pytest.fixture(autouse=True)
    def setup_env(self):
        i.walk(""" tot.init_env().stdlib() """)

    def scan(self, src): return i.walk(f""" tot.scan('{src}') """)
    def parse(self, tokens): return i.walk(f""" tot.parse({tokens}) """)
    def ast(self, src): return i.walk(f""" tot.ast('{src}') """)
    def eval(self, ast): return i.walk(f""" tot.eval({ast}) """)
    def walk(self, src): return i.walk(f""" tot.walk('{src}') """)
    def go(self, src): return self.walk(src)



class TestToT(TestBase):
    def test_overall_structure(self):
        assert self.scan(r""" 2 """) == [2, Ident('$EOF')]
        assert self.parse(r""" [2, Ident('$EOF')] """) == 2
        assert self.ast(r""" 2 """) == 2
        assert self.eval(r""" 2 """) == 2
        assert self.walk(r""" 2 """) == 2
        assert self.go(r""" 2 """) == 2

    def test_sequence(self):
        assert self.go(r""" if True then 2 end; if True then 3 end """) == 3
        assert self.go(r""" if True then 2 end; if True then 3 end; 4 """) == 4

    def test_define_assign(self):
        assert self.go(r""" a := 2 """) == 2
        assert self.go(r""" a """) == 2

        assert self.go(r""" a = 3 """) == 3
        assert self.go(r""" a """) == 3

        assert self.go(r""" a := b := 4 """) == 4
        assert self.go(r""" a """) == 4
        assert self.go(r""" b """) == 4

        assert self.go(r""" a = b = 5 """) == 5
        assert self.go(r""" a """) == 5
        assert self.go(r""" b """) == 5

        assert self.go(r""" a = c := 6 """) == 6
        assert self.go(r""" a """) == 6
        assert self.go(r""" c """) == 6

        with pytest.raises(AssertionError, match="Undefined variable"):
            self.go(r""" undefined_variable """)
        with pytest.raises(AssertionError, match="Undefined variable"):
            self.go(r""" undefined_variable = 2 """)
        with pytest.raises(AssertionError, match="Unexpected token"):
            self.go(r""" a := """)

    def test_destructure_variable_and_literal(self):
        # Variable pattern
        assert self.go(r""" a := 2; a """) == 2
        assert self.go(r""" _ := 2; _ """) == 2

        # Literal pattern
        assert self.go(r""" a := 2; 2 := a """) == 2
        assert self.go(r""" None := None """) is None
        assert self.go(r""" True := True """) is True
        assert self.go(r""" "hello" := "hello" """) == "hello"

        with pytest.raises(Exception, match="Pattern mismatch"):
            self.go(r""" "hello" := "world" """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.go(r""" a := 3; 2 := a """)

    def test_destructure_list(self):
        assert self.go(r""" [a, b] := [3, 4]; [a, b] """) == [3, 4]
        assert self.go(r""" [] := [] """) == []
        assert self.go(r""" [_, b, _] := [2, 3, 4]; b """) == 3

        with pytest.raises(Exception, match="Pattern mismatch"):
            self.go(r""" [a, b] := [2] """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.go(r""" [a, b] := [4, 5, 6] """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.go(r""" [] := [1] """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.go(r""" [a] := 2 """)

        # Rest parameters
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

        with pytest.raises(Exception, match="Pattern mismatch"):
            self.go(r""" [a, *b] := [] """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.go(r""" [*a, b] := [] """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.go(r""" [a, *b, c] := [2] """)
        with pytest.raises(Exception, match="Pattern mismatch"):
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

        with pytest.raises(Exception, match="Pattern mismatch"):
            self.go(r""" {a} := {b: 2} """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.go(r""" {a, b, c} := {a: 2, b: 3} """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.go(r""" {a, *rest} := {b: 2} """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.go(r""" {a} := 2 """)

    def test_destructure_ident_and_expr(self):
        assert self.go(r""" Ident("aaa") := Ident("aaa") """) == Ident("aaa")
        assert self.go(r""" Ident(a) := Ident("aaa"); a """) == "aaa"

        with pytest.raises(Exception, match="Pattern mismatch"):
            self.go(r""" Ident("aaa") := Ident("bbb") """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.go(r""" Ident(a) := "aaa" """)

        assert self.go(r""" tuple(Ident("add"), [int(a), int(b)]) := quote(2 + 3); [a, b] """) == [2, 3]
        assert self.go(r""" tuple(Ident("add"), [Ident(name1), Ident(name2)]) := quote(a + b); [name1, name2] """) == ['a', 'b']

        with pytest.raises(Exception, match="Pattern mismatch"):
            self.go(r""" tuple(Ident("add"), [Ident(name1), Ident(name2)]) := 2 + 3 """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.go(r""" tuple(Ident("add"), [Ident(name1), Ident(name2)]) := tuple(Ident("add")) """)

    def test_destructure_type(self):
        assert self.go(r""" int(a) := 2; a """) == 2
        assert self.go(r""" str(a) := "aaa"; a """) == "aaa"
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.go(r""" int(a) := "2" """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.go(r""" str(a) := [] """)

    def test_destructure_or(self):
        assert self.go(r""" int(a) or str(a) := 2; a """) == 2
        assert self.go(r""" int(a) or str(a) := "aaa"; a """) == "aaa"
        assert self.go(r""" int(a) or str(a) or list(a):= [2]; a """) == [2]
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.go(r""" int(a) or str(a) := [2] """)

    def test_destructure_combination(self):
        assert self.go(r""" [{a: b}, c] := [{a: 2, b: 3}, 4]; [b, c] """) == [2, 4]
        assert self.go(r""" {a: [b, c]} := {a: [5, 6]}; [b, c] """) == [5, 6]

    def test_list_assign(self):
        self.go(""" b := [2, 3, [4, 5]] """)
        self.go(""" b[0] = 6 """)
        assert self.go(""" b[0] """) == 6
        self.go(""" b[2][1] = 7 """)
        assert self.go(""" b[2][1] """) == 7
        assert self.go(""" b """) == [6, 3, [4, 7]]

        assert self.go(""" a := [1, 2]; b := [3, 4]; a[0] = b[1] = 5; [a, b] """) == [[5, 2], [3, 5]]

    def test_arrow_function(self):
        assert self.go(""" ([] -> 2)() """) == 2
        assert self.go(""" ([a] -> a + 2)(3) """) == 5
        assert self.go(""" (a -> a + 2)(3) """) == 5
        assert self.go(""" ([[a, b]] -> a + b)([2, 3]) """) == 5
        assert self.go(""" ([a, b] -> a + b)(2, 3) """) == 5
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.go(""" ([a, b] -> a + b)(2) """)

        assert self.go(""" ([a, *b] -> b)(2, 3, 4) """) == [3, 4]
        assert self.go(""" ({a} -> a + 2)({a: 3}) """) == 5
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.go(""" ({a} -> a + 2)({b: 3}) """)

        assert self.go(""" (int(a) -> a + 2)(3) """) == 5
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.go(""" (int(a) -> a + 2)("aaa") """)

        assert self.go(""" (x -> x or 2)(False) """) == 2
        assert self.go(""" (a -> b -> a + b)(2)(3) """) == 5

        assert self.go(""" inc := a -> a + 1; inc(2) """) == 3
        assert self.go(""" myadd := [a, b] -> a + b; myadd(2, 3) """) == 5

    def test_logical_operations(self, capsys):
        assert self.go(r""" True and False """) is False
        assert self.go(r""" False and True """) is False
        assert self.go(r""" True or False """) is True
        assert self.go(r""" False or True """) is True

        assert self.go(r""" True and 2 """) == 2
        assert self.go(r""" 0 and 2 / 0 """) == 0
        assert self.go(r""" False or 2 """) == 2
        assert self.go(r""" 1 or 2 / 0 """) == 1

        assert self.go(r""" print(2) and 3 """) is None
        assert capsys.readouterr().out == "2\n"
        assert self.go(r""" not print(2) or 3 """) is True
        assert capsys.readouterr().out == "2\n"

        assert self.go(r""" not True """) is False
        assert self.go(r""" not False """) is True
        assert self.go(r""" not not True """) is True

        assert self.go(r""" a := not 2 == 2 or True """) is True

    def test_comparison_operations(self):
        assert self.go(r""" 2 + 5 == 3 + 4 """) is True
        assert self.go(r""" 2 + 3 == 3 + 4 """) is False
        assert self.go(r""" 2 + 5 != 3 + 4 """) is False
        assert self.go(r""" 2 + 3 != 3 + 4 """) is True

        assert self.go(r""" 2 + 4 < 3 + 4 """) is True
        assert self.go(r""" 2 + 5 < 3 + 4 """) is False
        assert self.go(r""" 2 + 5 < 2 + 4 """) is False

        assert self.go(r""" 2 + 4 > 3 + 4 """) is False
        assert self.go(r""" 2 + 5 > 3 + 4 """) is False
        assert self.go(r""" 2 + 5 > 2 + 4 """) is True

        assert self.go(r""" 2 + 4 <= 3 + 4 """) is True
        assert self.go(r""" 2 + 5 <= 3 + 4 """) is True
        assert self.go(r""" 2 + 5 <= 2 + 4 """) is False

        assert self.go(r""" 2 + 4 >= 3 + 4 """) is False
        assert self.go(r""" 2 + 5 >= 3 + 4 """) is True
        assert self.go(r""" 2 + 5 >= 2 + 4 """) is True

        assert self.go(r""" 2 == 2 == 2 """) is False
        assert self.go(r""" a := 2 == 3 + 4 """) is False

        assert self.go(r""" True == True """) is True
        assert self.go(r""" None == None """) is True
        assert self.go(r""" False != True """) is True

    def test_arithmetic_operations(self):
        assert self.go(r""" 2 + 3 """) == 5
        assert self.go(r""" 2 + 3 - 4 """) == 1
        assert self.go(r""" a := 2 + sub(4, 3) """) == 3

    def test_mul_div_mod(self):
        assert self.go(r""" 2 * 3 """) == 6
        assert self.go(r""" 4 / 2 * 3 """) == 6
        assert self.go(r""" 2 * 3 % 4 """) == 2
        assert self.go(r""" 2 + 3 * add(4, 5) """) == 29

    def test_unary_operations(self):
        assert self.go(r""" -2 """) == -2
        assert self.go(r""" --2 """) == 2
        assert self.go(r""" 3--2 """) == 5
        assert self.go(r""" -add(2, 3) * 4 """) == -20

    def test_call_index(self):
        assert self.go(r""" neg(2) """) == -2
        assert self.go(r""" add(2, 3) """) == 5

        self.go(""" a := [2, 3, [4, 5]] """)
        assert self.go(""" a[2][0] """) == 4
        assert self.go(""" a[2][-1] """) == 5

        self.go(""" c := func do [add, sub] end """)
        assert self.go(""" c()[0](2, 3) """) == 5

        self.go(""" e := [1] """)
        with pytest.raises(Exception):
            self.go(""" e[None] = 2 """)
        with pytest.raises(Exception):
            self.go(""" None[2] = 3 """)
        with pytest.raises(Exception):
            self.go(""" [1, 2][5] """)
        with pytest.raises(Exception):
            self.go(""" [1, 2][None] """)
        with pytest.raises(Exception):
            self.go(""" None[0] """)

    def test_dot_notation(self):
        self.go(r""" a := {aaa: 2, bbb: 3} """)
        assert self.go(r""" a.aaa """) == 2

        self.go(r""" a.bbb = 4 """)
        assert self.go(r""" a """) == {'aaa': 2, 'bbb': 4}
        self.go(r""" a.ccc = 5 """)
        assert self.go(r""" a """) == {'aaa': 2, 'bbb': 4, 'ccc': 5}

        with pytest.raises(AssertionError):
            self.go(r""" a.not_found """)
        with pytest.raises(AssertionError, match="Invalid attribute"):
            self.go(r""" a.1 """)
        with pytest.raises(Exception):
            self.go(r""" [2, 3].aaa """)
        with pytest.raises(Exception):
            self.go(r""" [2, 3].aaa = 4 """)

    def test_ufcs(self):
        assert self.go(r""" 2.add(3) """) == 5
        assert self.go(r""" [2, 3, 4].len() """) == 3
        assert self.go(r""" [2, 3, 4].len().add(5) """) == 8

        self.go(r""" def myadd(a, b) do a + b end """)
        assert self.go(r""" 2.myadd(3) """) == 5

        with pytest.raises(AssertionError, match="Undefined variable"):
            self.go(r""" 2.not_found() """)
        with pytest.raises(AssertionError, match="Invalid operator"):
            self.go(r""" foo := 2; 3.foo() """)

    def test_method_notation(self):
        self.go(r""" obj := {
            set: func self, val do self.val = val end,
            add: func self, a do self.val + a end,
            val: None
        } """)
        self.go(r""" obj.set(2) """)
        assert self.go(r""" obj.val """) == 2
        assert self.go(r""" obj.add(3) """) == 5

        assert self.go(r""" {a: 2, b: 3}.keys() """) == ['a', 'b']
        assert self.go(r""" { len: func self do "local" end }.len() """) == "local"

    def test_none_bool(self):
        assert self.go(r""" None """) is None
        assert self.go(r""" True """) is True
        assert self.go(r""" False """) is False

    def test_numbers(self):
        assert self.go(r"""2""") == 2
        assert self.go(r"""23""") == 23
        assert self.go(r"""0""") == 0
        assert self.go(r"""023""") == 23

    def test_raw_string(self):
        assert i.walk(r""" tot.walk(" 'hello, world' ") """) == "hello, world"
        assert i.walk(r""" tot.walk(" '' ") """) == ""
        assert i.walk(r""" tot.walk(" 'if ; #\"\\n' ") """) == 'if ; #"\\n'
        assert i.walk(" tot.walk(\" 'a\nb' \") ") == "a\nb"

        with pytest.raises(AssertionError, match="Unterminated string"):
            i.walk(r""" tot.walk(" ' ") """)

    def test_string(self):
        assert i.walk(r""" tot.walk(' "hello, world" ') """) == "hello, world"
        assert i.walk(r""" tot.walk(' "" ') """) == ""
        assert i.walk(r""" tot.walk(' "if ; #\"\\\n" ') """) == 'if ; #"\\\n'
        assert i.walk(" tot.walk(' \"a\nb\" ') ") == "a\nb"

        with pytest.raises(AssertionError, match="Unterminated string"):
            i.walk(r""" tot.walk(' " ') """)

        with pytest.raises(AssertionError, match="Unterminated string"):
            i.walk(r""" tot.walk(' "\" ') """)

    def test_string_functions(self):
        assert self.go(r""" join(["ab", "cd", "ef"], ",") """) == "ab,cd,ef"

    def test_grouping(self):
        assert self.go(r""" (2 + 3) * 4 """) == 20
        assert self.go(r""" (2) * 3 """) == 6

    def test_list(self, capsys):
        assert self.go(""" [] """) == []
        assert self.go(""" [2 + 3] """) == [5]
        assert self.go(""" [2, 3, [4, 5]] """) == [2, 3, [4, 5]]
        self.go(""" [print(2), print(3)] """)
        assert capsys.readouterr().out == "2\n3\n"

    def test_list_functions(self, capsys):
        self.go(""" d := [2, 3, 4] """)
        assert self.go(""" len(d) """) == 3
        assert self.go(""" index(d, 2) """) == 4
        assert self.go(""" slice(d, 1, None) """) == [3, 4]
        assert self.go(""" slice(d, 1, 2) """) == [3]
        assert self.go(""" slice(d, None, 2) """) == [2, 3]
        assert self.go(""" slice(d, None, None) """) == [2, 3, 4]
        assert self.go(""" push(d, 5) """) is None
        assert self.go(""" d """) == [2, 3, 4, 5]
        assert self.go(""" pop(d) """) == 5
        assert self.go(""" d """) == [2, 3, 4]
        assert self.go(""" in(2, d) """) is True
        assert self.go(""" in(5, d) """) is False
        assert self.go(""" dd := copy(d); dd[0] = 6; [d, dd] """) == [[2, 3, 4], [6, 3, 4]]

        assert self.go(""" [2, 3] + [4, 5] """) == [2, 3, 4, 5]
        assert self.go(""" [2, 3] * 3 """) == [2, 3, 2, 3, 2, 3]

    def test_dict(self):
        assert self.go(r""" {} """) == {}

        self.go(r""" ccc := 1 """)
        assert self.go(r""" a := {"aaa": 2 + 3, bbb: 4, ccc} """) == {'aaa': 5, 'bbb': 4, 'ccc': 1}
        assert self.go(r""" a["aaa"] """) == 5

        self.go(r""" a["aaa"] = 6 """)
        self.go(r""" a["ddd"] = 7 """)
        assert self.go(r""" a """) == {'aaa': 6, 'bbb': 4, 'ccc': 1, 'ddd': 7}

        assert self.go(r""" {outer: {inner: 1}} """) == {'outer': {'inner': 1}}

        with pytest.raises(AssertionError, match="Expected :"):
            self.go(r""" {"aaa"} """)
        with pytest.raises(AssertionError, match="Invalid key"):
            self.go(r""" {2: 3} """)
        with pytest.raises(KeyError):
            self.go(r""" a["eee"] """)
        with pytest.raises(AssertionError, match="Undefined variable"):
            self.go(r""" {undefined_var} """)

    def test_dict_functions(self):
        assert self.go(r""" a := dict([["aaa", 2], ["bbb", 3], ["ccc", 4]]) """) == {'aaa': 2, 'bbb': 3, 'ccc': 4}
        assert self.go(r""" len(a) """) == 3
        assert self.go(r""" in("aaa", a) """) is True
        assert self.go(r""" in("ddd", a) """) is False
        assert self.go(r""" keys(a) """) == ['aaa', 'bbb', 'ccc']
        assert self.go(r""" items(a) """) == [['aaa', 2], ['bbb', 3], ['ccc', 4]]

    def test_type_functions(self):
        assert self.go(r""" type(None) """) == "NoneType"
        assert self.go(r""" type(True) """) == "bool"
        assert self.go(r""" type(5) """) == "int"
        assert i.walk(r""" tot.walk(" type('') ") """) == "str"
        assert self.go(r""" type("") """) == "str"
        assert self.go(r""" type([]) """) == "list"
        assert self.go(r""" type({}) """) == "dict"

        assert self.go(r""" bool(True) """) is True
        assert self.go(r""" bool(1) """) is True
        assert self.go(r""" int(2) """) == 2
        assert self.go(r""" int("2") """) == 2
        assert self.go(r""" str("a") """) == "a"
        assert self.go(r""" str(2) """) == "2"
        assert self.go(r""" list([2, 3]) """) == [2, 3]
        assert self.go(r""" list({a: 2, b: 3}) """) == ["a", "b"]
        assert self.go(r""" dict({a: 2, b: 3}) """) == {"a": 2, "b": 3}
        assert self.go(r""" dict([["a", 2], ["b", 3]]) """) == {"a": 2, "b": 3}

    def test_quote(self, capsys):
        assert self.go(r""" quote(hello_world) """) == Ident("hello_world")
        assert self.go(r""" quote(if 2 == 3 then 4 else 5 end) """) == (
            Ident("if"), [(Ident("equal"), [2, 3]), 4, 5]
        )

    def test_scope(self):
        assert self.go(r""" a := 2; scope a end """) == 2
        assert self.go(r""" a := 2; scope scope a end end """) == 2

        assert self.go(r""" a := 2; scope a := 3 end """) == 3
        assert self.go(r""" a """) == 2

        assert self.go(r""" a := 2; scope a = 3 end """) == 3
        assert self.go(r""" a """) == 3

        assert self.go(r""" a := 2; scope d := 3 end """) == 3
        with pytest.raises(AssertionError, match="Undefined variable"):
            self.go(r""" d """)

    def test_func(self):
        assert self.go("func do 2 end ()") == 2
        assert self.go("func a do add(a, 2) end (3)") == 5
        assert self.go("func a, b do add(a, b) end (2, 3)") == 5

        assert self.go("func a, b do add(a, b) end (add(2, 3), 4; 5)") == 10
        assert self.go("""
           myadd := func a, b do add(a, b) end;
           myadd(2, 3)
        """) == 5

        with pytest.raises(AssertionError, match="Pattern mismatch"):
            self.go("func a, b do add(a, b) end (2)")

        with pytest.raises(AssertionError, match="Expected do @ consume: add"):
            self.go("func a add(a, 2) end")

        with pytest.raises(AssertionError, match="Expected end @ consume: \\$EOF"):
            self.go("func a do add(a, 2)")

    def test_destructure_function_arguments(self):
        assert self.go(r""" func a, *rest do [a, rest] end (2, 3, 4) """) == [2, [3, 4]]
        assert self.go(r""" func {a: d, *rest}, e do [d, e, rest] end ({a: 2, b: 3, c: 4}, 5) """) == [2, 5, {'b': 3, 'c': 4}]

        assert self.go(r""" def foo(int(a), str(b)) do [a, b] end; foo(2, "a") """) == [2, "a"]

        with pytest.raises(Exception, match="Pattern mismatch"):
            self.go(r""" def bar(int(a), str(b)) do [a, b] end; bar(2, 3) """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.go(r""" func a, b do [a, b] end (2) """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.go(r""" func a do a end (2, 3) """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.go(r""" func do 2 end (2) """)

        assert self.go(r""" func do "ok" end () """) == "ok"

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
        assert self.go(""" fib(6) """) == 8

        assert self.go(""" func do return() end () """) is None

        with pytest.raises(Exception):
            self.go(""" return() """)

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

    def test_def(self):
        self.go(r""" def myadd(a, b) do a + b end """)
        assert self.go(r""" myadd(2, 3) """) == 5

        self.go(r""" def say_hello do "hello" end """)
        assert self.go(r""" say_hello() """) == "hello"

        self.go(r"""
            def fact(n) do n * fact(n - 1) end;
            def fact(0) do 1 end
        """)
        assert self.go(r""" fact(0) """) == 1
        assert self.go(r""" fact(3) """) == 6

        with pytest.raises(Exception, match="Invalid def syntax"):
            self.go(r""" def 2 do 3 end """)

    def test_if(self):
        assert self.go(r""" if True then 2 end """) == 2
        assert self.go(r""" if False then 2 end """) is None
        assert self.go(r""" if True then 2 else 3 end """) == 2
        assert self.go(r""" if False then 2 else 3 end """) == 3
        assert self.go(r""" if True then 2 elif True then 3 end """) == 2
        assert self.go(r""" if False then 2 elif True then 3 end """) == 3
        assert self.go(r""" if False then 2 elif False then 3 end """) is None
        assert self.go(r""" if False then 2 elif True then 3 else 4 end """) == 3
        assert self.go(r""" if True then 2 elif True then 3 else 4 end """) == 2
        assert self.go(r""" if False then 2 elif False then 3 else 4 end """) == 4
        assert self.go(r""" if False then 2 elif False then 3 elif True then 4 else 5 end """) == 4

        assert self.go(r""" if 2; True then 1; 2 else 2; 3 end """) == 2
        assert self.go(r""" if 2; False then 1; 2 else 2; 3 end """) == 3

        with pytest.raises(AssertionError, match="Expected then"):
            self.go(r""" if True 2 end """)
        with pytest.raises(AssertionError, match="Expected end"):
            self.go(r""" if True then 2 """)
        with pytest.raises(AssertionError, match="Expected end"):
            self.go(r""" if True then 2 3 end """)
        with pytest.raises(AssertionError, match="Expected end"):
            self.go(r""" if True then 2 else 3 """)
        with pytest.raises(AssertionError, match="Expected then"):
            self.go(r""" if False then 2 elif True 3 end """)
        with pytest.raises(AssertionError, match="Expected end"):
            self.go(r""" if False then 2 elif True then 3 """)

    def test_match_syntax(self):
        assert self.go(r""" match 2 end """) is None

        with pytest.raises(Exception, match="Expected end"):
            self.go(r""" match end """)
        with pytest.raises(Exception, match="Expected end"):
            self.go(r""" match 2 case 2 then 3 """)
        with pytest.raises(Exception, match="Expected end"):
            self.go(r""" match 2 then 3 end """)
        with pytest.raises(Exception, match="Expected then"):
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

        assert self.go(r""" match quote(a + b) case tuple(Ident("add"), [Ident(name1), Ident(name2)]) then [name1, name2] end """) == ["a", "b"]
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

        with pytest.raises(Exception, match="Expected do"):
            self.go(""" while do 2 then 3 else 4 end """)
        with pytest.raises(Exception, match="Expected do"):
            self.go(""" while True 2 then 3 else 4 end """)
        with pytest.raises(Exception, match="Expected end"):
            self.go(""" while True do 2 3 else 4 end """)
        with pytest.raises(Exception, match="Expected end"):
            self.go(""" while True do 2 then 3 4 end """)
        with pytest.raises(Exception, match="Expected end"):
            self.go(""" while True do 2 then 3 else end """)
        with pytest.raises(Exception, match="Expected end"):
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

        with pytest.raises(Exception, match="Continue at top level"):
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

        with pytest.raises(Exception, match="Break at top level"):
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

        assert self.go("""
            a := [];
            keys := ["a", "b", "c"];
            values := [2, 3, 4];
            for [k, v] in zip(keys, values) do push(a, [k, v]) then a end
        """) == [['a', 2], ['b', 3], ['c', 4]]

        assert self.go(""" for i in [] do 1/0 then 2 end """) == 2

        with pytest.raises(Exception):
            self.go(""" for in [] do 2 then 3 else 4 end """)
        with pytest.raises(Exception):
            self.go(""" for i [] do 2 then 3 else 4 end """)
        with pytest.raises(Exception, match="Expected do"):
            self.go(""" for i in do 2 then 3 else 4 end """)
        with pytest.raises(Exception, match="Expected end"):
            self.go(""" for i in [] do then 3 else 4 end """)
        with pytest.raises(Exception, match="Expected end"):
            self.go(""" for i in [] do 2 3 else 4 end """)
        with pytest.raises(Exception, match="Expected end"):
            self.go(""" for i in [] do 2 then else 4 end """)
        with pytest.raises(Exception, match="Expected end"):
            self.go(""" for i in [] do 2 then 3 4 end """)
        with pytest.raises(Exception, match="Expected end"):
            self.go(""" for i in [] do 2 then 3 else end """)
        with pytest.raises(Exception, match="Expected end"):
            self.go(""" for i in [] do 2 then 3 else 4 """)

    def test_for_continue(self):
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

    def test_for_break(self):
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

    def test_try_except(self):
        assert self.go(""" try 2; 3 end """) == 3
        assert self.go(""" try 2; 3 except e then e end """) == 3
        assert self.go(""" try 2; raise(2 + 3); 3 except e then e end """) == 5

        assert self.go("""
            try
                raise(["foo", 3])
            except ["foo", val] then ["foo", val]
            except ["bar", val] then ["bar", val]
            end
        """) == ['foo', 3]

        assert self.go("""
            try
                raise(["bar", 3])
            except ["foo", val] then ["foo", val]
            except ["bar", val] then ["bar", val]
            end
        """) == ['bar', 3]

        with pytest.raises(Exception):
            self.go("""
                try
                    raise(["baz", 3])
                except ["foo", val] then ["foo", val]
                end
            """)

        assert self.go(""" try raise(2) except _ then 3 end """) == 3

        assert self.go(""" func do try return(2) except _ then 3 end end () """) == 2

        assert self.go("""
            a := 0; while a < 5 do
                try a = a + 1; if a == 3 then break() end
                except _ then a = 10 end
            end; a
        """) == 3

        assert self.go("""
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

        assert self.go("""
            try
                try
                    raise("outer")
                except "inner" then "caught inner"
                end
            except "outer" then "caught outer"
            end
        """) == "caught outer"

    def test_defclass(self):
        assert self.go(r"""
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
            self.go(""" defclass 2 do 2 end """)
        with pytest.raises(Exception, match="Expected do"):
            self.go(""" defclass Foo(x) end """)
        with pytest.raises(Exception, match="Invalid defmethod syntax"):
            self.go(""" defclass Foo do defmethod 2 do end end """)

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

    def test_read_load(self, tmp_path):
        assert self.go(""" type(read("lib/fib.toil")) """) == "str"
        assert self.go(""" load("lib/fib.toil")(4) """) == 3

    def test_eval_apply(self):
        assert self.go(""" eval("2 + 3") """) == 5
        assert self.go(""" eval_expr(tuple(Ident("add"), [2, 3])) """) == 5
        assert self.go(""" apply(add, [2, 3]) """) == 5
        assert self.go(""" apply(func a, b do a + b end, [2, 3]) """) == 5

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
        assert self.go(""" reverse([]) """) == []
        assert self.go(""" zip(a, [4, 5, 6]) """) == [[2, 4], [3, 5], [4, 6]]
        assert self.go(""" enumerate(a) """) == [[0, 2], [1, 3], [2, 4], [3, 5], [4, 6], [5, 7], [6, 8], [7, 9]]

    def test_whitespace(self):
        assert self.go(r"""   2 """) == 2
        assert self.go(r""" 2   """) == 2
        assert self.go("""\n  2  \n""") == 2

    def test_empty_source(self):
        with pytest.raises(AssertionError, match="Unexpected token"):
            self.go(r"""  """)

    def test_invalid_character(self):
        with pytest.raises(AssertionError, match="Invalid character"):
            self.go(r""" ~ """)

    def test_extra_token(self):
        with pytest.raises(AssertionError, match="Extra token"):
            self.go(r""" 2 3 """)

class TestExamples(TestBase):
    def test_recursion_gcd(self):
        self.go("""
            def gcd(a, b) do
                if b == 0 then a else gcd(b, a % b) end
            end
        """)
        assert self.go("gcd(12, 18)") == 6

    def test_iteration_gcd(self):
        self.go("""
            def gcd(a, b) do
                while b > 0 do
                    tmp := b; b = a % b; a = tmp
                end;
                a
            end
        """)
        assert self.go("gcd(12, 18)") == 6

    def test_recursion_fac(self):
        self.go("""
            def fac(n) do
                if n == 0 then 1 else n * fac(n - 1) end
            end
        """)
        assert self.go("fac(0)") == 1
        assert self.go("fac(1)") == 1
        assert self.go("fac(4)") == 24

    def test_iteration_fac(self):
        self.go("""
            def fac(n) do
                result := 1;
                for n in range(1, n + 1, 1) do
                    result = result * n
                then result end
            end
        """)
        assert self.go("fac(0)") == 1
        assert self.go("fac(1)") == 1
        assert self.go("fac(4)") == 24

    def test_recursion_fib(self):
        self.go("""
            def fib(n) do
                if n == 0 then 0
                elif n == 1 then 1
                else fib(n - 1) + fib(n - 2)
                end
            end
        """)
        assert self.go("fib(0)") == 0
        assert self.go("fib(1)") == 1
        assert self.go("fib(6)") == 8

    def test_iteration_fib(self):
        self.go("""
            def fib(n) do
                a := 0; b := 1;
                for n in range(0, n, 1) do
                    tmp := b; b = a + b; a = tmp
                then a end
            end
        """)
        assert self.go("fib(0)") == 0
        assert self.go("fib(1)") == 1
        assert self.go("fib(6)") == 8

    def test_mutual_recursion(self):
        self.go("""
            def even(n) do if n == 0 then True else odd(n - 1) end end;
            def odd(n) do if n == 0 then False else even(n - 1) end end
        """)
        assert self.go("even(2)") is True
        assert self.go("even(3)") is False
        assert self.go("odd(2)") is False
        assert self.go("odd(3)") is True

    def test_closure_counter(self):
        self.go("""
            def make_counter do
                count := 0;
                func do count = count + 1 end
            end;

            c1 := make_counter();
            c2 := make_counter()
        """)
        assert self.go("c1()") == 1
        assert self.go("c1()") == 2
        assert self.go("c2()") == 1
        assert self.go("c2()") == 2

    def test_bubblesort(self):
        assert self.go("""
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
        assert self.go("""
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
        assert self.go("""
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
        self.go("""
            def Animal(name) do
                self := {};
                self._name = name;
                self.introduce = func self do print("I am", self._name) end;
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
        assert capsys.readouterr().out == "I am Rocky\ncrying\nI am Lucy\ncrying\n"

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
        assert capsys.readouterr().out == "I am Leo\nwoof\n"

    def test_lazy_evaluation_with_thunks(self):
        assert self.go("""
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
