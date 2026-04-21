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


class TestToT(TestBase):
    def test_overall_structure(self):
        assert self.scan(r""" 2 """) == [2, Ident('$EOF')]
        assert self.parse(r""" [2, Ident('$EOF')] """) == 2
        assert self.ast(r""" 2 """) == 2
        assert self.eval(r""" 2 """) == 2
        assert self.walk(r""" 2 """) == 2

    def test_sequence(self):
        assert self.walk(r""" if True then 2 end; if True then 3 end """) == 3
        assert self.walk(r""" if True then 2 end; if True then 3 end; 4 """) == 4

    def test_define_assign(self):
        assert self.walk(r""" a := 2 """) == 2
        assert self.walk(r""" a """) == 2

        assert self.walk(r""" a = 3 """) == 3
        assert self.walk(r""" a """) == 3

        assert self.walk(r""" a := b := 4 """) == 4
        assert self.walk(r""" a """) == 4
        assert self.walk(r""" b """) == 4

        assert self.walk(r""" a = b = 5 """) == 5
        assert self.walk(r""" a """) == 5
        assert self.walk(r""" b """) == 5

        assert self.walk(r""" a = c := 6 """) == 6
        assert self.walk(r""" a """) == 6
        assert self.walk(r""" c """) == 6

        with pytest.raises(AssertionError, match="Undefined variable"):
            self.walk(r""" undefined_variable """)
        with pytest.raises(AssertionError, match="Undefined variable"):
            self.walk(r""" undefined_variable = 2 """)
        with pytest.raises(AssertionError, match="Unexpected token"):
            self.walk(r""" a := """)

    def test_destructure_variable_and_literal(self):
        # Variable pattern
        assert self.walk(r""" a := 2; a """) == 2
        assert self.walk(r""" _ := 2; _ """) == 2

        # Literal pattern
        assert self.walk(r""" a := 2; 2 := a """) == 2
        assert self.walk(r""" None := None """) is None
        assert self.walk(r""" True := True """) is True
        assert self.walk(r""" "hello" := "hello" """) == "hello"

        with pytest.raises(Exception, match="Pattern mismatch"):
            self.walk(r""" "hello" := "world" """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.walk(r""" a := 3; 2 := a """)

    def test_destructure_list(self):
        assert self.walk(r""" [a, b] := [3, 4]; [a, b] """) == [3, 4]
        assert self.walk(r""" [] := [] """) == []
        assert self.walk(r""" [_, b, _] := [2, 3, 4]; b """) == 3

        with pytest.raises(Exception, match="Pattern mismatch"):
            self.walk(r""" [a, b] := [2] """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.walk(r""" [a, b] := [4, 5, 6] """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.walk(r""" [] := [1] """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.walk(r""" [a] := 2 """)

        # Rest parameters
        assert self.walk(r""" [a, *b] := [2]; [a, b] """) == [2, []]
        assert self.walk(r""" [a, *b] := [3, 4]; [a, b] """) == [3, [4]]
        assert self.walk(r""" [a, *b] := [4, 5, 6]; [a, b] """) == [4, [5, 6]]
        assert self.walk(r""" [*a] := [4, 5, 6]; a """) == [4, 5, 6]

        assert self.walk(r""" [*a, b] := [2]; [a, b] """) == [[], 2]
        assert self.walk(r""" [*a, b] := [2, 3]; [a, b] """) == [[2], 3]
        assert self.walk(r""" [*a, b] := [2, 3, 4]; [a, b] """) == [[2, 3], 4]

        assert self.walk(r""" [a, *b, c] := [3, 4]; [a, b, c] """) == [3, [], 4]
        assert self.walk(r""" [a, *b, c] := [4, 5, 6]; [a, b, c] """) == [4, [5], 6]
        assert self.walk(r""" [a, *b, c] := [5, 6, 7, 8]; [a, b, c] """) == [5, [6, 7], 8]

        with pytest.raises(Exception, match="Pattern mismatch"):
            self.walk(r""" [a, *b] := [] """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.walk(r""" [*a, b] := [] """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.walk(r""" [a, *b, c] := [2] """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.walk(r""" [a, *b, *c, d] := [5, 6, 7, 8] """)

    def test_destructure_dict(self):
        assert self.walk(r""" {a} := {a: 2, b: 3}; a """) == 2
        assert self.walk(r""" {a, b} := {a: 2, b: 3}; [a, b] """) == [2, 3]
        assert self.walk(r""" {a: c, b: d} := {a: 3, b: 4}; [c, d] """) == [3, 4]
        assert self.walk(r""" {a} := {"a": 5, b: 6}; a """) == 5
        assert self.walk(r""" {a: _, b} := {a: 2, b: 3}; b """) == 3
        assert self.walk(r""" {} := {a: 2, b: 3} """) == {'a': 2, 'b': 3}

        assert self.walk(r""" {a, *rest} := {a: 2}; [a, rest] """) == [2, {}]
        assert self.walk(r""" {a, *rest} := {a: 2, b: 3}; [a, rest] """) == [2, {'b': 3}]
        assert self.walk(r""" {a, *rest} := {a: 2, b: 3, c: 4}; [a, rest] """) == [2, {'b': 3, 'c': 4}]

        with pytest.raises(Exception, match="Pattern mismatch"):
            self.walk(r""" {a} := {b: 2} """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.walk(r""" {a, b, c} := {a: 2, b: 3} """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.walk(r""" {a, *rest} := {b: 2} """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.walk(r""" {a} := 2 """)

    def test_destructure_ident_and_expr(self):
        assert str(self.walk(r""" Ident("aaa") := Ident("aaa") """)) == "aaa"
        assert str(self.walk(r""" Ident(a) := Ident("aaa"); a """)) == "aaa"

        with pytest.raises(Exception, match="Pattern mismatch"):
            self.walk(r""" Ident("aaa") := Ident("bbb") """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.walk(r""" Ident(a) := "aaa" """)

        assert self.walk(r""" Expr(Ident("add"), [int(a), int(b)]) := quote(2 + 3); [a, b] """) == [2, 3]
        assert self.walk(r""" Expr(Ident("add"), [Ident(name1), Ident(name2)]) := quote(a + b); [name1, name2] """) == ['a', 'b']

        with pytest.raises(Exception, match="Pattern mismatch"):
            self.walk(r""" Expr(Ident("add"), [Ident(name1), Ident(name2)]) := 2 + 3 """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.walk(r""" Expr(Ident("add"), [Ident(name1), Ident(name2)]) := Expr(Ident("add")) """)

    def test_destructure_type(self):
        assert self.walk(r""" int(a) := 2; a """) == 2
        assert self.walk(r""" str(a) := "aaa"; a """) == "aaa"
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.walk(r""" int(a) := "2" """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.walk(r""" str(a) := [] """)

    def test_destructure_or(self):
        assert self.walk(r""" int(a) or str(a) := 2; a """) == 2
        assert self.walk(r""" int(a) or str(a) := "aaa"; a """) == "aaa"
        assert self.walk(r""" int(a) or str(a) or list(a):= [2]; a """) == [2]
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.walk(r""" int(a) or str(a) := [2] """)

    def test_destructure_combination(self):
        assert self.walk(r""" [{a: b}, c] := [{a: 2, b: 3}, 4]; [b, c] """) == [2, 4]
        assert self.walk(r""" {a: [b, c]} := {a: [5, 6]}; [b, c] """) == [5, 6]

    def test_list_assign(self):
        self.walk(""" b := [2, 3, [4, 5]] """)
        self.walk(""" b[0] = 6 """)
        assert self.walk(""" b[0] """) == 6
        self.walk(""" b[2][1] = 7 """)
        assert self.walk(""" b[2][1] """) == 7
        assert self.walk(""" b """) == [6, 3, [4, 7]]

        assert self.walk(""" a := [1, 2]; b := [3, 4]; a[0] = b[1] = 5; [a, b] """) == [[5, 2], [3, 5]]

    def test_logical_operations(self, capsys):
        assert self.walk(r""" True and False """) is False
        assert self.walk(r""" False and True """) is False
        assert self.walk(r""" True or False """) is True
        assert self.walk(r""" False or True """) is True

        assert self.walk(r""" True and 2 """) == 2
        assert self.walk(r""" 0 and 2 / 0 """) == 0
        assert self.walk(r""" False or 2 """) == 2
        assert self.walk(r""" 1 or 2 / 0 """) == 1

        assert self.walk(r""" print(2) and 3 """) is None
        assert capsys.readouterr().out == "2\n"
        assert self.walk(r""" not print(2) or 3 """) is True
        assert capsys.readouterr().out == "2\n"

        assert self.walk(r""" not True """) is False
        assert self.walk(r""" not False """) is True
        assert self.walk(r""" not not True """) is True

        assert self.walk(r""" a := not 2 == 2 or True """) is True

    def test_comparison_operations(self):
        assert self.walk(r""" 2 + 5 == 3 + 4 """) is True
        assert self.walk(r""" 2 + 3 == 3 + 4 """) is False
        assert self.walk(r""" 2 + 5 != 3 + 4 """) is False
        assert self.walk(r""" 2 + 3 != 3 + 4 """) is True

        assert self.walk(r""" 2 + 4 < 3 + 4 """) is True
        assert self.walk(r""" 2 + 5 < 3 + 4 """) is False
        assert self.walk(r""" 2 + 5 < 2 + 4 """) is False

        assert self.walk(r""" 2 + 4 > 3 + 4 """) is False
        assert self.walk(r""" 2 + 5 > 3 + 4 """) is False
        assert self.walk(r""" 2 + 5 > 2 + 4 """) is True

        assert self.walk(r""" 2 + 4 <= 3 + 4 """) is True
        assert self.walk(r""" 2 + 5 <= 3 + 4 """) is True
        assert self.walk(r""" 2 + 5 <= 2 + 4 """) is False

        assert self.walk(r""" 2 + 4 >= 3 + 4 """) is False
        assert self.walk(r""" 2 + 5 >= 3 + 4 """) is True
        assert self.walk(r""" 2 + 5 >= 2 + 4 """) is True

        assert self.walk(r""" 2 == 2 == 2 """) is False
        assert self.walk(r""" a := 2 == 3 + 4 """) is False

        assert self.walk(r""" True == True """) is True
        assert self.walk(r""" None == None """) is True
        assert self.walk(r""" False != True """) is True

    def test_arithmetic_operations(self):
        assert self.walk(r""" 2 + 3 """) == 5
        assert self.walk(r""" 2 + 3 - 4 """) == 1
        assert self.walk(r""" a := 2 + sub(4, 3) """) == 3

    def test_mul_div_mod(self):
        assert self.walk(r""" 2 * 3 """) == 6
        assert self.walk(r""" 4 / 2 * 3 """) == 6
        assert self.walk(r""" 2 * 3 % 4 """) == 2
        assert self.walk(r""" 2 + 3 * add(4, 5) """) == 29

    def test_unary_operations(self):
        assert self.walk(r""" -2 """) == -2
        assert self.walk(r""" --2 """) == 2
        assert self.walk(r""" 3--2 """) == 5
        assert self.walk(r""" -add(2, 3) * 4 """) == -20

    def test_call_index(self):
        assert self.walk(r""" neg(2) """) == -2
        assert self.walk(r""" add(2, 3) """) == 5

        self.walk(""" a := [2, 3, [4, 5]] """)
        assert self.walk(""" a[2][0] """) == 4
        assert self.walk(""" a[2][-1] """) == 5

        self.walk(""" c := func do [add, sub] end """)
        assert self.walk(""" c()[0](2, 3) """) == 5

        self.walk(""" e := [1] """)
        with pytest.raises(Exception):
            self.walk(""" e[None] = 2 """)
        with pytest.raises(Exception):
            self.walk(""" None[2] = 3 """)
        with pytest.raises(Exception):
            self.walk(""" [1, 2][5] """)
        with pytest.raises(Exception):
            self.walk(""" [1, 2][None] """)
        with pytest.raises(Exception):
            self.walk(""" None[0] """)

    def test_none_bool(self):
        assert self.walk(r""" None """) is None
        assert self.walk(r""" True """) is True
        assert self.walk(r""" False """) is False

    def test_numbers(self):
        assert self.walk(r"""2""") == 2
        assert self.walk(r"""23""") == 23
        assert self.walk(r"""0""") == 0
        assert self.walk(r"""023""") == 23

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
        assert self.walk(r""" join(["ab", "cd", "ef"], ",") """) == "ab,cd,ef"

    def test_grouping(self):
        assert self.walk(r""" (2 + 3) * 4 """) == 20
        assert self.walk(r""" (2) * 3 """) == 6

    def test_list(self, capsys):
        assert self.walk(""" [] """) == []
        assert self.walk(""" [2 + 3] """) == [5]
        assert self.walk(""" [2, 3, [4, 5]] """) == [2, 3, [4, 5]]
        self.walk(""" [print(2), print(3)] """)
        assert capsys.readouterr().out == "2\n3\n"

    def test_list_functions(self, capsys):
        self.walk(""" d := [2, 3, 4] """)
        assert self.walk(""" len(d) """) == 3
        assert self.walk(""" index(d, 2) """) == 4
        assert self.walk(""" slice(d, 1, None) """) == [3, 4]
        assert self.walk(""" slice(d, 1, 2) """) == [3]
        assert self.walk(""" slice(d, None, 2) """) == [2, 3]
        assert self.walk(""" slice(d, None, None) """) == [2, 3, 4]
        assert self.walk(""" push(d, 5) """) is None
        assert self.walk(""" d """) == [2, 3, 4, 5]
        assert self.walk(""" pop(d) """) == 5
        assert self.walk(""" d """) == [2, 3, 4]
        assert self.walk(""" in(2, d) """) is True
        assert self.walk(""" in(5, d) """) is False
        assert self.walk(""" dd := copy(d); dd[0] = 6; [d, dd] """) == [[2, 3, 4], [6, 3, 4]]

        assert self.walk(""" [2, 3] + [4, 5] """) == [2, 3, 4, 5]
        assert self.walk(""" [2, 3] * 3 """) == [2, 3, 2, 3, 2, 3]

    def test_dict(self):
        assert self.walk(r""" {} """) == {}

        self.walk(r""" ccc := 1 """)
        assert self.walk(r""" a := {"aaa": 2 + 3, bbb: 4, ccc} """) == {'aaa': 5, 'bbb': 4, 'ccc': 1}
        assert self.walk(r""" a["aaa"] """) == 5

        self.walk(r""" a["aaa"] = 6 """)
        self.walk(r""" a["ddd"] = 7 """)
        assert self.walk(r""" a """) == {'aaa': 6, 'bbb': 4, 'ccc': 1, 'ddd': 7}

        assert self.walk(r""" {outer: {inner: 1}} """) == {'outer': {'inner': 1}}

        with pytest.raises(AssertionError, match="Expected :"):
            self.walk(r""" {"aaa"} """)
        with pytest.raises(AssertionError, match="Invalid key"):
            self.walk(r""" {2: 3} """)
        with pytest.raises(KeyError):
            self.walk(r""" a["eee"] """)
        with pytest.raises(AssertionError, match="Undefined variable"):
            self.walk(r""" {undefined_var} """)

    def test_dict_functions(self):
        assert self.walk(r""" a := dict([["aaa", 2], ["bbb", 3], ["ccc", 4]]) """) == {'aaa': 2, 'bbb': 3, 'ccc': 4}
        assert self.walk(r""" len(a) """) == 3
        assert self.walk(r""" in("aaa", a) """) is True
        assert self.walk(r""" in("ddd", a) """) is False
        assert self.walk(r""" keys(a) """) == ['aaa', 'bbb', 'ccc']
        assert self.walk(r""" items(a) """) == [['aaa', 2], ['bbb', 3], ['ccc', 4]]

    def test_dot_notation(self):
        self.walk(r""" a := {aaa: 2, bbb: 3} """)
        assert self.walk(r""" a.aaa """) == 2

        self.walk(r""" a.bbb = 4 """)
        assert self.walk(r""" a """) == {'aaa': 2, 'bbb': 4}
        self.walk(r""" a.ccc = 5 """)
        assert self.walk(r""" a """) == {'aaa': 2, 'bbb': 4, 'ccc': 5}

        with pytest.raises(AssertionError):
            self.walk(r""" a.not_found """)
        with pytest.raises(AssertionError, match="Invalid attribute"):
            self.walk(r""" a.1 """)
        with pytest.raises(Exception):
            self.walk(r""" [2, 3].aaa """)
        with pytest.raises(Exception):
            self.walk(r""" [2, 3].aaa = 4 """)

    def test_ufcs(self):
        assert self.walk(r""" 2.add(3) """) == 5
        assert self.walk(r""" [2, 3, 4].len() """) == 3
        assert self.walk(r""" [2, 3, 4].len().add(5) """) == 8

        self.walk(r""" deffunc myadd params a, b do a + b end """)
        assert self.walk(r""" 2.myadd(3) """) == 5

        with pytest.raises(AssertionError, match="Undefined variable"):
            self.walk(r""" 2.not_found() """)
        with pytest.raises(AssertionError, match="Invalid operator"):
            self.walk(r""" foo := 2; 3.foo() """)

    def test_method_notation(self):
        self.walk(r""" obj := {
            set: func self, val do self.val = val end,
            add: func self, a do self.val + a end,
            val: None
        } """)
        self.walk(r""" obj.set(2) """)
        assert self.walk(r""" obj.val """) == 2
        assert self.walk(r""" obj.add(3) """) == 5

        assert self.walk(r""" {a: 2, b: 3}.keys() """) == ['a', 'b']
        assert self.walk(r""" { len: func self do "local" end }.len() """) == "local"

    def test_type_functions(self):
        assert self.walk(r""" type(None) """) == "NoneType"
        assert self.walk(r""" type(True) """) == "bool"
        assert self.walk(r""" type(5) """) == "int"
        assert i.walk(r""" tot.walk(" type('') ") """) == "str"
        assert self.walk(r""" type("") """) == "str"
        assert self.walk(r""" type([]) """) == "list"
        assert self.walk(r""" type({}) """) == "dict"

        assert self.walk(r""" bool(True) """) is True
        assert self.walk(r""" bool(1) """) is True
        assert self.walk(r""" int(2) """) == 2
        assert self.walk(r""" int("2") """) == 2
        assert self.walk(r""" str("a") """) == "a"
        assert self.walk(r""" str(2) """) == "2"
        assert self.walk(r""" list([2, 3]) """) == [2, 3]
        assert self.walk(r""" list({a: 2, b: 3}) """) == ["a", "b"]
        assert self.walk(r""" dict({a: 2, b: 3}) """) == {"a": 2, "b": 3}
        assert self.walk(r""" dict([["a", 2], ["b", 3]]) """) == {"a": 2, "b": 3}

    def test_quote(self, capsys):
        assert self.walk(r""" quote(hello_world) """) == Ident("hello_world")
        assert self.walk(r""" quote(if 2 == 3 then 4 else 5 end) """) == (
            Ident("if"), [(Ident("equal"), [2, 3]), 4, 5]
        )

    def test_scope(self):
        assert self.walk(r""" a := 2; scope a end """) == 2
        assert self.walk(r""" a := 2; scope scope a end end """) == 2

        assert self.walk(r""" a := 2; scope a := 3 end """) == 3
        assert self.walk(r""" a """) == 2

        assert self.walk(r""" a := 2; scope a = 3 end """) == 3
        assert self.walk(r""" a """) == 3

        assert self.walk(r""" a := 2; scope d := 3 end """) == 3
        with pytest.raises(AssertionError, match="Undefined variable"):
            self.walk(r""" d """)

    def test_func(self):
        assert self.walk("func do 2 end ()") == 2
        assert self.walk("func a do add(a, 2) end (3)") == 5
        assert self.walk("func a, b do add(a, b) end (2, 3)") == 5

        assert self.walk("func a, b do add(a, b) end (add(2, 3), 4; 5)") == 10
        assert self.walk("""
           myadd := func a, b do add(a, b) end;
           myadd(2, 3)
        """) == 5

        with pytest.raises(AssertionError, match="Pattern mismatch"):
            self.walk("func a, b do add(a, b) end (2)")

        with pytest.raises(AssertionError, match="Expected do @ consume: add"):
            self.walk("func a add(a, 2) end")

        with pytest.raises(AssertionError, match="Expected end @ consume: \\$EOF"):
            self.walk("func a do add(a, 2)")

    def test_destructure_function_arguments(self):
        assert self.walk(r""" func a, *rest do [a, rest] end (2, 3, 4) """) == [2, [3, 4]]
        assert self.walk(r""" func {a: d, *rest}, e do [d, e, rest] end ({a: 2, b: 3, c: 4}, 5) """) == [2, 5, {'b': 3, 'c': 4}]

        assert self.walk(r""" deffunc foo params int(a), str(b) do [a, b] end; foo(2, "a") """) == [2, "a"]

        with pytest.raises(Exception, match="Pattern mismatch"):
            self.walk(r""" deffunc bar params int(a), str(b) do [a, b] end; bar(2, 3) """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.walk(r""" func a, b do [a, b] end (2) """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.walk(r""" func a do a end (2, 3) """)
        with pytest.raises(Exception, match="Pattern mismatch"):
            self.walk(r""" func do 2 end (2) """)

        assert self.walk(r""" func do "ok" end () """) == "ok"


    def test_return(self):
        self.walk("""
            deffunc f params a do
                if a == 2 then return(3) end;
                4
            end
        """)
        assert self.walk(""" f(2) """) == 3
        assert self.walk(""" f(3) """) == 4

        self.walk("""
            deffunc fib params n do
                if n == 0 then return(0) end;
                if n == 1 then return(1) end;
                fib(n - 1) + fib(n - 2)
            end
        """)
        assert self.walk(""" fib(0) """) == 0
        assert self.walk(""" fib(1) """) == 1
        assert self.walk(""" fib(6) """) == 8

        assert self.walk(""" func do return() end () """) is None

        with pytest.raises(Exception):
            self.walk(""" return() """)

    def test_deffunc(self):
        self.walk(r""" deffunc myadd params a, b do a + b end """)
        assert self.walk(r""" myadd(2, 3) """) == 5

    def test_if(self):
        assert self.walk(r""" if True then 2 end """) == 2
        assert self.walk(r""" if False then 2 end """) is None
        assert self.walk(r""" if True then 2 else 3 end """) == 2
        assert self.walk(r""" if False then 2 else 3 end """) == 3
        assert self.walk(r""" if True then 2 elif True then 3 end """) == 2
        assert self.walk(r""" if False then 2 elif True then 3 end """) == 3
        assert self.walk(r""" if False then 2 elif False then 3 end """) is None
        assert self.walk(r""" if False then 2 elif True then 3 else 4 end """) == 3
        assert self.walk(r""" if True then 2 elif True then 3 else 4 end """) == 2
        assert self.walk(r""" if False then 2 elif False then 3 else 4 end """) == 4
        assert self.walk(r""" if False then 2 elif False then 3 elif True then 4 else 5 end """) == 4

        assert self.walk(r""" if 2; True then 1; 2 else 2; 3 end """) == 2
        assert self.walk(r""" if 2; False then 1; 2 else 2; 3 end """) == 3

        with pytest.raises(AssertionError, match="Expected then"):
            self.walk(r""" if True 2 end """)
        with pytest.raises(AssertionError, match="Expected end"):
            self.walk(r""" if True then 2 """)
        with pytest.raises(AssertionError, match="Expected end"):
            self.walk(r""" if True then 2 3 end """)
        with pytest.raises(AssertionError, match="Expected end"):
            self.walk(r""" if True then 2 else 3 """)
        with pytest.raises(AssertionError, match="Expected then"):
            self.walk(r""" if False then 2 elif True 3 end """)
        with pytest.raises(AssertionError, match="Expected end"):
            self.walk(r""" if False then 2 elif True then 3 """)

    def test_while(self):
        assert self.walk("""
            sum := i := 0;
            while i < 10 do
                sum = sum + i;
                i = i + 1
            end;
            sum
        """) == 45
        assert self.walk("""
            while False do 1 / 0 end
        """) == None

    def test_continue(self):
        assert self.walk("""
            a := [];
            i := 0; while i < 5 do
                i = i + 1;
                if i == 3 then continue() end;
                push(a, i)
            end;
            a
        """) == [1, 2, 4, 5]

        assert self.walk("""
            a := []; i := 0; while i < 2 do
                j := 0; while j < 3 do
                    j = j + 1; if j == 2 then continue() end; push(a, [i, j])
                end; i = i + 1
            end;
            a
        """) == [[0, 1], [0, 3], [1, 1], [1, 3]]

        with pytest.raises(Exception, match="Continue at top level"):
            self.walk(""" continue() """)

    def test_break(self):
        assert self.walk("""
            a := [];
            i := 0; while i < 5 do
                if i == 3 then break() end;
                push(a, i);
                i = i + 1
            end;
            a
        """) == [0, 1, 2]

        assert self.walk("""
            a := []; i := 0; while i < 2 do
                j := 0; while j < 3 do
                    if j == 2 then break() end; push(a, [i, j]); j = j + 1
                end; i = i + 1
            end;
            a
        """) == [[0, 0], [0, 1], [1, 0], [1, 1]]

        assert self.walk(""" while True do break() end """) is None
        assert self.walk(""" while True do break(2 + 3) end """) == 5

        with pytest.raises(Exception, match="Break at top level"):
            self.walk(""" break() """)

    def test_for(self, capsys):
        assert self.walk("""
            sum := 0;
            for n in [2, 3, 4] do sum = sum + n end;
            sum
        """) == 9

        assert self.walk("""
            for i in [2, 3, 4] do
                if i == 3 then break(5) end
            end
        """) == 5

        assert self.walk("""
            a := [];
            for i in [2, 3, 4] do
                if i == 3 then continue() end;
                push(a, i)
            end;
            a
        """) == [2, 4]

        self.walk("""
            keys := ["a", "b", "c"];
            values := [2, 3, 4];
            for [k, v] in zip(keys, values) do
                print(k, v)
            end
        """)
        assert capsys.readouterr().out == "a 2\nb 3\nc 4\n"

        self.walk("""
            dic := { "a": 2, "b": 3, "c": 4 };
            for [k, v] in dic.items() do
                print(k, v)
            end
        """)
        assert capsys.readouterr().out == "a 2\nb 3\nc 4\n"

    def test_stdlib(self):
        assert self.walk(""" a := range(2, 10, 1) """) == [2, 3, 4, 5, 6, 7, 8, 9]
        assert self.walk(""" b := range(2, 10, 3) """) == [2, 5, 8]
        assert self.walk(""" first(a) """) == 2
        assert self.walk(""" rest(a) """) == [3, 4, 5, 6, 7, 8, 9]
        assert self.walk(""" last(a) """) == 9
        assert self.walk(""" map(a, func n do n * 2 end) """) == [4, 6, 8, 10, 12, 14, 16, 18]
        assert self.walk(""" filter(a, func n do n % 2 == 0 end) """) == [2, 4, 6, 8]
        assert self.walk(""" reduce(a, add, 0) """) == 44
        assert self.walk(""" reverse(a) """) == [9, 8, 7, 6, 5, 4, 3, 2]
        assert self.walk(""" reverse([]) """) == []
        assert self.walk(""" zip(a, [4, 5, 6]) """) == [[2, 4], [3, 5], [4, 6]]
        assert self.walk(""" enumerate(a) """) == [[0, 2], [1, 3], [2, 4], [3, 5], [4, 6], [5, 7], [6, 8], [7, 9]]

    def test_whitespace(self):
        assert self.walk(r"""   2 """) == 2
        assert self.walk(r""" 2   """) == 2
        assert self.walk("""\n  2  \n""") == 2

    def test_empty_source(self):
        with pytest.raises(AssertionError, match="Unexpected token"):
            self.walk(r"""  """)

    def test_invalid_character(self):
        with pytest.raises(AssertionError, match="Invalid character"):
            self.walk(r""" ~ """)

    def test_extra_token(self):
        with pytest.raises(AssertionError, match="Extra token"):
            self.walk(r""" 2 3 """)

class TestExamples(TestBase):
    def test_recursion_gcd(self):
        self.walk("""
            deffunc gcd params a, b do
                if b == 0 then a else gcd(b, a % b) end
            end
        """)
        assert self.walk("gcd(12, 18)") == 6

    def test_iteration_gcd(self):
        self.walk("""
            deffunc gcd params a, b do
                while b > 0 do
                    tmp := b; b = a % b; a = tmp
                end;
                a
            end
        """)
        assert self.walk("gcd(12, 18)") == 6

    def test_recursion_fac(self):
        self.walk("""
            deffunc fac params n do
                if n == 0 then 1 else n * fac(n - 1) end
            end
        """)
        assert self.walk("fac(0)") == 1
        assert self.walk("fac(1)") == 1
        assert self.walk("fac(4)") == 24

    def test_iteration_fac(self):
        self.walk("""
            deffunc fac params n do
                result := 1;
                for n in range(1, n + 1, 1) do
                    result = result * n
                end;
                result
            end
        """)
        assert self.walk("fac(0)") == 1
        assert self.walk("fac(1)") == 1
        assert self.walk("fac(4)") == 24

    def test_recursion_fib(self):
        self.walk("""
            deffunc fib params n do
                if n == 0 then 0
                elif n == 1 then 1
                else fib(n - 1) + fib(n - 2)
                end
            end
        """)
        assert self.walk("fib(0)") == 0
        assert self.walk("fib(1)") == 1
        assert self.walk("fib(6)") == 8

    def test_iteration_fib(self):
        self.walk("""
            deffunc fib params n do
                a := 0; b := 1;
                for n in range(0, n, 1) do
                    tmp := b; b = a + b; a = tmp
                end;
                a
            end
        """)
        assert self.walk("fib(0)") == 0
        assert self.walk("fib(1)") == 1
        assert self.walk("fib(6)") == 8

    def test_mutual_recursion(self):
        self.walk("""
            deffunc even params n do if n == 0 then True else odd(n - 1) end end;
            deffunc odd params n do if n == 0 then False else even(n - 1) end end
        """)
        assert self.walk("even(2)") is True
        assert self.walk("even(3)") is False
        assert self.walk("odd(2)") is False
        assert self.walk("odd(3)") is True

    def test_closure_counter(self):
        self.walk("""
            make_counter := func do
                count := 0;
                func do count = count + 1 end
            end;

            c1 := make_counter();
            c2 := make_counter()
        """)
        assert self.walk("c1()") == 1
        assert self.walk("c1()") == 2
        assert self.walk("c2()") == 1
        assert self.walk("c2()") == 2

    def test_bubblesort(self):
        assert self.walk("""
            deffunc bubblesort params a do
                n := len(a);
                for i in range(0, n, 1) do
                    for j in range(0, n - i - 1, 1) do
                        if a[j] > a[j + 1] then
                            tmp := a[j]; a[j] = a[j + 1]; a[j + 1] = tmp
                        end
                    end
                end;
                a
            end;

            bubblesort([5, 3, 8, 4, 2])
        """) == [2, 3, 4, 5, 8]

    def test_quicksort(self):
        assert self.walk("""
            deffunc quicksort params a do
                if len(a) <= 1 then a else
                    pivot := first(a); rem := rest(a);
                    left := rem.filter(func x do x < pivot end);
                    right := rem.filter(func x do x >= pivot end);
                    quicksort(left) + [pivot] + quicksort(right)
                end
            end;

            quicksort([5, 3, 8, 4, 2])
        """) == [2, 3, 4, 5, 8]

    def test_sieve(self):
        assert self.walk("""
            deffunc sieve params n do
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
        self.walk("""
            deffunc Animal params name do
                self := {};
                self._name = name;
                self.introduce = func self do print("I am", self._name) end;
                self.make_sound = func self do print("crying") end;
                self
            end
        """)
        self.walk("""
            animal1 := Animal("Rocky");
            animal2 := Animal("Lucy");
            animal1.introduce();
            animal1.make_sound();
            animal2.introduce();
            animal2.make_sound()
        """)
        assert capsys.readouterr().out == "I am Rocky\ncrying\nI am Lucy\ncrying\n"

        self.walk("""
            deffunc Dog params name do
                self := Animal(name);
                self.make_sound = func self do print("woof") end;
                self
            end
        """)
        self.walk("""
            dog1 := Dog("Leo");
            dog1.introduce();
            dog1.make_sound()
        """)
        assert capsys.readouterr().out == "I am Leo\nwoof\n"


if __name__ == "__main__":
    pytest.main([__file__])
