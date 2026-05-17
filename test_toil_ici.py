import pytest
from toil import Interpreter, Ident

toil = Interpreter()


@pytest.fixture(autouse=True)
def setup_toil():
    global toil
    toil = Interpreter().init_env().stdlib()

class TestICI:
    def test_overall_structure(self):
        assert toil.scan(r""" 2 """) == [2, Ident('$EOF')]
        assert toil.parse([2, Ident('$EOF')]) == 2
        assert toil.ast(r""" 2 """) == 2
        assert toil.code(""" 2 """) == [('const', 2), ('halt',)]
        assert toil.execute([('const', 2), ('halt',)]) == 2
        assert toil.run(r""" 2 """) == 2

    def test_const(self):
        assert toil.run(r""" 2 """) == 2
        assert toil.run(r""" None """) is None
        assert toil.run(r""" True """) is True
        assert toil.run(r""" 'hello' """) == "hello"

    def test_sequence(self, capsys):
        assert toil.run(r""" print(2); print(3); 4 """) == 4
        assert capsys.readouterr().out == "2\n3\n"

        assert toil.run(r""" (2; 3); (4; 5) """) == 5

        with pytest.raises(AssertionError, match="Empty sequence"):
            toil.compile((Ident("seq"), []))

    def test_if(self):
        assert toil.run(r""" if 2 == 2 then 4 + 5 else 6 + 7  end """) == 9
        assert toil.run(r""" if 2 == 3 then 4 + 5 else 6 + 7  end """) == 13
        assert toil.run(r""" if False then 2 elif False then 3 else 4 end """) == 4

    def test_scope(self, capsys):
        assert toil.run(r""" a := 2; scope a end """) == 2
        assert toil.run(r""" a := 2; scope scope a end end """) == 2

        assert toil.run(r""" a := 2; scope a := 3 end """) == 3
        assert toil.run(r""" a """) == 2

        assert toil.run(r""" a := 2; scope a = 3 end """) == 3
        assert toil.run(r""" a """) == 3

        assert toil.run(r""" a := 2; scope d := 3 end """) == 3
        with pytest.raises(AssertionError, match="Undefined variable"):
            toil.run(r""" d """)


if __name__ == "__main__":
    pytest.main([__file__])
