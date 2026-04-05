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
        i.walk(""" tot.init_env() """)

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

    def test_whitespace(self):
        assert self.walk(r"""   2 """) == 2
        assert self.walk(r""" 2   """) == 2
        assert self.walk("""\n  2  \n""") == 2

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

        assert self.walk(r""" 2 * 3 """) == 6
        assert self.walk(r""" 4 / 2 * 3 """) == 6
        assert self.walk(r""" 2 * 3 % 4 """) == 2
        assert self.walk(r""" 2 + 3 * add(4, 5) """) == 29

    def test_grouping(self):
        assert self.walk(r""" (2 + 3) * 4 """) == 20
        assert self.walk(r""" (2) * 3 """) == 6

    def test_unary_operations(self):
        assert self.walk(r""" -2 """) == -2
        assert self.walk(r""" --2 """) == 2
        assert self.walk(r""" 3--2 """) == 5
        assert self.walk(r""" -add(2, 3) * 4 """) == -20

    def test_numbers(self):
        assert self.walk(r"""2""") == 2
        assert self.walk(r"""23""") == 23
        assert self.walk(r"""0""") == 0
        assert self.walk(r"""023""") == 23

    def test_bool_none(self):
        assert self.walk(r""" None """) is None
        assert self.walk(r""" True """) is True
        assert self.walk(r""" False """) is False

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

        assert self.walk("func a, b do add(a, b) end (2, 3, 4)") == 5

        with pytest.raises(AssertionError, match="Undefined variable @ val: b"):
            self.walk("func a, b do add(a, b) end (2)")

        with pytest.raises(AssertionError, match="Expected do @ consume: add"):
            self.walk("func a add(a, 2) end")

        with pytest.raises(AssertionError, match="Expected end @ consume: \\$EOF"):
            self.walk("func a do add(a, 2)")

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

    def test_empty_source(self):
        with pytest.raises(AssertionError, match="Unexpected token"):
            self.walk(r"""  """)

    def test_invalid_character(self):
        with pytest.raises(AssertionError, match="Invalid character"):
            self.walk(r""" ~ """)

    def test_extra_token(self):
        with pytest.raises(AssertionError, match="Extra token"):
            self.walk(r""" 2 3 """)

class TestProblemsWithFunctions(TestBase):
    def test_recursion_gcd(self):
        self.walk("""
            gcd := func a, b do
                if equal(b, 0) then
                    a
                else
                    gcd(b, mod(a, b))
                end
            end
        """)
        assert self.walk("gcd(12, 18)") == 6

    def test_recursion_fac(self):
        self.walk("""
            fac := func n do
                if equal(n, 0) then 1
                else mul(n, fac(sub(n, 1)))
                end
            end
        """)
        assert self.walk("fac(0)") == 1
        assert self.walk("fac(1)") == 1
        assert self.walk("fac(4)") == 24

    def test_recursion_fib(self):
        self.walk("""
            fib := func n do
                if equal(n, 0) then 0
                elif equal(n, 1) then 1
                else add(fib(sub(n, 1)), fib(sub(n, 2)))
                end
            end
        """)
        assert self.walk("fib(0)") == 0
        assert self.walk("fib(1)") == 1
        assert self.walk("fib(6)") == 8

    def test_mutual_recursion(self):
        self.walk("""
            even := func n do
                if equal(n, 0) then True else odd(sub(n, 1)) end
            end;

            odd := func n do
                if equal(n, 0) then False else even(sub(n, 1)) end
            end
        """)
        assert self.walk("even(2)") is True
        assert self.walk("even(3)") is False
        assert self.walk("odd(2)") is False
        assert self.walk("odd(3)") is True

    def test_closure_counter(self):
        self.walk("""
            make_counter := func do
                count := 0;
                func do
                    count = add(count, 1);
                    count
                end
            end;

            c1 := make_counter();
            c2 := make_counter()
        """)
        assert self.walk("c1()") == 1
        assert self.walk("c1()") == 2
        assert self.walk("c2()") == 1
        assert self.walk("c2()") == 2

    def test_iteration_gcd(self):
        self.walk("""
            gcd := func a, b do
                while greater(b, 0) do
                    tmp := b; b = mod(a, b); a = tmp
                end;
                a
            end
        """)
        assert self.walk("gcd(12, 18)") == 6

    def test_iteration_fac(self):
        self.walk("""
            fac := func n do
                result := 1;
                while greater(n, 0) do
                    result = mul(result, n);
                    n = sub(n, 1)
                end;
                result
            end
        """)
        assert self.walk("fac(0)") == 1
        assert self.walk("fac(1)") == 1
        assert self.walk("fac(4)") == 24

    def test_iteration_fib(self):
        self.walk("""
            fib := func n do
                a := 0; b := 1;
                while greater(n, 0) do
                    tmp := b; b = add(a, b); a = tmp;
                    n = sub(n, 1)
                end;
                a
            end
        """)
        assert self.walk("fib(0)") == 0
        assert self.walk("fib(1)") == 1
        assert self.walk("fib(6)") == 8

if __name__ == "__main__":
    pytest.main([__file__])
