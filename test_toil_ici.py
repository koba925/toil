import pytest
from toil import Interpreter, Ident


class TestBase:
    @pytest.fixture(autouse=True)
    def set_interpreter(self):
        self.i = Interpreter().init_env()

    def scan(self, src): return self.i.scan(src)
    def parse(self, tokens): return self.i.parse(tokens)
    def ast(self, src): return self.i.ast(src)
    def compile(self, expr): return self.i.compile(expr)
    def execute(self, code): return self.i.execute(code)
    def run(self, src): return self.i.run(src)
    def go(self, src): return self.i.run(src)


class TestICI(TestBase):
    def test_overall_structure(self):
        assert self.scan(r""" 2 """) == [2, Ident('$EOF')]
        assert self.parse([2, Ident('$EOF')]) == 2
        assert self.ast(r""" 2 """) == 2
        assert self.compile(2) == [('const', 2), ('halt',)]
        assert self.execute([('const', 2), ('halt',)]) == 2
        assert self.run(r""" 2 """) == 2
        assert self.go(r""" 2 """) == 2

    def test_const(self):
        assert self.go(r""" 2 """) == 2
        assert self.go(r""" None """) is None
        assert self.go(r""" True """) is True
        assert self.go(r""" 'hello' """) == "hello"

if __name__ == "__main__":
    pytest.main([__file__])
