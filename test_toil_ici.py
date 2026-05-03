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
        assert i.code(""" 2 """) == [('const', 2), ('halt',)]
        assert i.execute([('const', 2), ('halt',)]) == 2
        assert i.run(r""" 2 """) == 2

    def test_const(self):
        assert i.run(r""" 2 """) == 2
        assert i.run(r""" None """) is None
        assert i.run(r""" True """) is True
        assert i.run(r""" 'hello' """) == "hello"

    def test_seq(self, capsys):
        assert i.run(r""" 2; 3 """) == 3
        assert i.run(r""" 2; 3; 4 """) == 4
        assert i.run(r""" (2; 3); (4; 5) """) == 5

        i.run(r""" print(2); print(3); 4 """)
        assert capsys.readouterr().out == "2\n3\n"

        with pytest.raises(AssertionError, match="Empty sequence @ compile"):
            i.compile((Ident("seq"), []))

if __name__ == "__main__":
    pytest.main([__file__])
