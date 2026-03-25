import pytest
from toil import Sym
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

    def test_is_name_first(self):
        assert i.walk(""" is_name_first("a") """) is True
        assert i.walk(""" is_name_first("z") """) is True
        assert i.walk(""" is_name_first("A") """) is True
        assert i.walk(""" is_name_first("Z") """) is True
        assert i.walk(""" is_name_first("0") """) is False
        assert i.walk(""" is_name_first("9") """) is False
        assert i.walk(""" is_name_first("_") """) is True
        assert i.walk(""" is_name_first("$") """) is False
        assert i.walk(""" is_name_first(" ") """) is False
        assert i.walk(""" is_name_first("\n") """) is False
        assert i.walk(r""" is_name_first("\n") """) is False

    def test_is_name_rest(self):
        assert i.walk(""" is_name_rest("a") """) is True
        assert i.walk(""" is_name_rest("z") """) is True
        assert i.walk(""" is_name_rest("A") """) is True
        assert i.walk(""" is_name_rest("Z") """) is True
        assert i.walk(""" is_name_rest("0") """) is True
        assert i.walk(""" is_name_rest("9") """) is True
        assert i.walk(""" is_name_rest("_") """) is True
        assert i.walk(""" is_name_rest("$") """) is False
        assert i.walk(""" is_name_rest(" ") """) is False
        assert i.walk(""" is_name_rest("\n") """) is False
        assert i.walk(r""" is_name_rest("\n") """) is False

    def test_is_sym(self):
        assert i.walk(""" is_sym(sym("a")) """) is True
        assert i.walk(""" is_sym(sym("_abc")) """) is True
        assert i.walk(""" is_sym(sym("0a")) """) is False
        assert i.walk(""" is_sym(sym("$a")) """) is False
        assert i.walk(""" is_sym(sym(" a")) """) is False
        assert i.walk(""" is_sym("a") """) is False

    def test_in(self):
        assert i.walk(""" in(2, [1, 2, 3]) """) is True
        assert i.walk(""" in(4, [1, 2, 3]) """) is False
        assert i.walk(""" 2.in([1, 2, 3]) """) is True
        assert i.walk(""" 4.in([1, 2, 3]) """) is False
        assert i.walk(""" 'a'.in({'a': 2, 'b': 3}) """) is True
        assert i.walk(""" 'c'.in({'a': 2, 'b': 3}) """) is False

class TestToT:
    @pytest.fixture(scope="class", autouse=True)
    def setup_tot(self):
        i.walk(""" tot := Interpreter() """)

    def scan(self, src): return i.walk(f""" tot.scan('{src}') """)
    def parse(self, tokens): return i.walk(f""" tot.parse({tokens}) """)
    def ast(self, src): return i.walk(f""" tot.ast('{src}') """)
    def eval(self, ast): return i.walk(f""" tot.eval({ast}) """)
    def walk(self, src): return i.walk(f""" tot.walk('{src}') """)

    def test_overall_structure(self):
        assert self.scan(r""" 2 """) == [2, Sym('$EOF')]
        assert self.parse(r""" [2, sym('$EOF')] """) == 2
        assert self.ast(r""" 2 """) == 2
        assert self.eval(r""" 2 """) == 2
        assert self.walk(r""" 2 """) == 2

    def test_numbers(self):
        assert self.walk(r"""2""") == 2
        assert self.walk(r"""23""") == 23
        assert self.walk(r"""0""") == 0
        assert self.walk(r"""023""") == 23

    def test_bool_none(self):
        assert self.walk(r""" None """) is None
        assert self.walk(r""" True """) is True
        assert self.walk(r""" False """) is False

    def test_whitespace(self):
        assert self.walk(r"""   2 """) == 2
        assert self.walk(r""" 2   """) == 2
        assert self.walk("""\n  2  \n""") == 2

    def test_variable(self):
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

    def test_seq(self):
        assert self.walk(r""" if True then 2 end; if True then 3 end """) == 3
        assert self.walk(r""" if True then 2 end; if True then 3 end; 4 """) == 4

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

if __name__ == "__main__":
    pytest.main([__file__])
