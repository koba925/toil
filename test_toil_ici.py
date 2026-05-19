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

    def test_while(self, capsys):
        assert toil.run(r""" i := 0; while i < 3 do i = i + 1 then i + 1 end """) == 4
        assert toil.run(r""" i := 0; while i < 3 do print(i); i = i + 1 end """) is None
        assert capsys.readouterr().out == "0\n1\n2\n"

    def test_continue(self, capsys):
        toil.run(r""" i := 0; while i < 3 do i = i + 1; if i == 2 then continue end; print(i) end """)
        assert capsys.readouterr().out == "1\n3\n"

        toil.run(r"""
            i := 0; while i < 2 do
                j := 0; while j < 3 do
                    j = j + 1; if j == 2 then continue end;
                    print(i); print(j)
                end;
                i = i + 1
            end
        """)
        assert capsys.readouterr().out == "0\n1\n0\n3\n1\n1\n1\n3\n"

        toil.run(r"""
            i := 0; while i < 3 do
                i = i + 1;
                scope
                    if i == 2 then continue end;
                    print(i)
                end
            end
        """)
        assert capsys.readouterr().out == "1\n3\n"

        with pytest.raises(AssertionError, match="Continue outside of loop"):
            toil.run(r""" continue """)

    def test_break(self, capsys):
        assert toil.run(r""" i := 0; while i < 3 do if i == 1 then break end; print(i); i = i + 1 end """) is None
        assert capsys.readouterr().out == "0\n"

        assert toil.run(r""" i := 0; while i < 3 do if i == 1 then break end; print(i); i = i + 1 then i * 2 else i * 3 end """) == 3
        assert capsys.readouterr().out == "0\n"

        toil.run(r"""
            i := 0; while i < 2 do
                j := 0; while j < 3 do
                    if i == 0 then if j == 1 then break end end;
                    print(i); print(j);
                    j = j + 1
                end;
                i = i + 1
            end
        """)
        assert capsys.readouterr().out == "0\n0\n1\n0\n1\n1\n1\n2\n"

        toil.run(r"""
            i := 0; while i < 2 do
                j := 0; while j < 3 do
                    if i == 1 then if j == 1 then break end end;
                    print(i); print(j);
                    j = j + 1
                else break end;
                i = i + 1
            end
        """)
        assert capsys.readouterr().out == "0\n0\n0\n1\n0\n2\n1\n0\n"

        toil.run(r"""
            i := 0; while i < 3 do
                scope
                    if i == 1 then break end;
                    print(i)
                end;
                i = i + 1
            end
        """)
        assert capsys.readouterr().out == "0\n"

        with pytest.raises(AssertionError, match="Break outside of loop"):
            toil.run(r""" break """)

    def test_builtins(self, capsys):
        assert toil.run(r""" add(mul(2, 3), 4) """) == 10

        assert toil.run(r""" list() """) == []
        assert toil.run(r""" list(2, 3, 4) """) == [2, 3, 4]

        toil.run(r""" print() """)
        assert capsys.readouterr().out == "\n"
        toil.run(r""" print(2, 3, 4) """)
        assert capsys.readouterr().out == "2 3 4\n"

        assert toil.run(r""" myadd := add; myadd(2, 3) """) == 5

if __name__ == "__main__":
    pytest.main([__file__])
