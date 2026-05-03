import pytest
from toil import Interpreter, Ident

i = Interpreter()

@pytest.fixture(autouse=True)
def reset_env():
    i.init_env()

class TestICI:
    def test_overall_structure(self):
        assert i.scan(r""" 2 """) == [2, Ident('$EOF')]
        assert i.parse([2, Ident('$EOF')]) == 2
        assert i.ast(r""" 2 """) == 2
        assert i.compile(""" 2 """) == [('const', 2), ('halt',)]
        assert i.execute([('const', 2), ('halt',)]) == 2
        assert i.run(r""" 2 """) == 2

    def test_const(self):
        assert i.run(r""" 2 """) == 2
        assert i.run(r""" None """) is None
        assert i.run(r""" True """) is True
        assert i.run(r""" 'hello' """) == "hello"

if __name__ == "__main__":
    pytest.main([__file__])
