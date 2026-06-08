import pytest
from toil import Interpreter

@pytest.fixture(autouse=True)
def setup_toil():
    global toil
    toil = Interpreter()

class TestIntermediateCodeInterpreter:
    # Ensure test independence
    def test_env_isolation_step1(self):
        assert toil.run(r""" a := 2 """) == 2
    def test_env_isolation_step2(self):
        with pytest.raises(AssertionError, match="Undefined variable"):
            toil.run(r""" a """)

    def test_constants(self):
        assert toil.run(r""" 2 """) == 2
        assert toil.run(r""" None """) is None
        assert toil.run(r""" True """) is True
        assert toil.run(r""" False """) is False

    def test_variable_definition(self):
        assert toil.run(r""" a := 2 """) == 2
        assert toil.run(r""" a """) == 2

        assert toil.run(r""" a := b := 2 == 2 """) is True
        assert toil.run(r""" a """) is True
        assert toil.run(r""" b """) is True

        assert toil.run(r""" a := 2; b := 3; a * b """) == 6

        with pytest.raises(AssertionError, match="Undefined variable"):
            toil.run(r""" c """)

    def test_sequence(self, capsys):
        assert toil.run(r""" 2; 3; 4 """) == 4

        assert toil.run(r""" print(2); print(3) """) is None
        assert capsys.readouterr().out == "2\n3\n"

        with pytest.raises(Exception, match="Empty sequence"):
            toil.compile(("seq", []))

    def test_assignment_scope(self):
        assert toil.run(r""" a := 2; a = 3 + 4 """) == 7
        assert toil.run(r""" a """) == 7

        assert toil.run(r""" a := 2; b := 3; a = b = 4 """) == 4
        assert toil.run(r""" a """) == 4
        assert toil.run(r""" b """) == 4

        assert toil.run(r""" a := 2; scope a + 3 end """) == 5

        assert toil.run(r""" a := 2; scope scope a + 3 end end """) == 5

        assert toil.run(r""" a := 2; scope a := 3 end """) == 3
        assert toil.run(r""" a """) == 2

        assert toil.run(r""" a := 2; scope a = 3 end """) == 3
        assert toil.run(r""" a """) == 3

        with pytest.raises(AssertionError, match="Undefined variable"):
            toil.run(r""" scope d = 3 end """)
        with pytest.raises(AssertionError, match="Undefined variable"):
            toil.run(r""" scope c := 2 end; c """)

    def test_if(self):
        assert toil.run(r""" if 2 == 2 then 4 + 5 else 6 + 7 end """) == 9
        assert toil.run(r""" if 2 == 3 then 4 + 5 else 6 + 7 end """) == 13
        assert toil.run(r""" if True then 3 else 4 end * 5 """) == 15
        assert toil.run(r""" if True then if True then 3 else 4 end else 5 end """) == 3
        assert toil.run(r""" if True then if False then 3 else 4 end else 5 end """) == 4
        assert toil.run(r""" if False then 3 else if True then 4 else 5 end end """) == 4
        assert toil.run(r""" if False then 3 else if False then 4 else 5 end end """) == 5

    def test_while(self, capsys):
        assert toil.run(r""" i := 1; while i < 3 do i = i + 1 end """) == 3

        assert toil.run(r"""
            sum := 0;
            i := 1; while i < 4 do sum = sum + i; i = i + 1 end;
            sum
        """) == 6

        toil.run(r"""
            i := 1; while i < 3 do
                j := 1; while j < 3 do print(i); print(j); j = j + 1 end;
                i = i + 1
            end
        """)
        assert capsys.readouterr().out == "1\n1\n1\n2\n2\n1\n2\n2\n"

        assert toil.run(r""" while False do 1/0 end """) is None

    def test_pseudo_func(self, capsys):
        assert toil.run(r""" 2 + 3 """) == 5
        assert toil.run(r""" 2 + 3 * 4 """) == 14
        assert toil.run(r""" (2 + 3) * 4 """) == 20
        assert toil.run(r""" 2 + 3 == 2 * 3 """) is False
        assert toil.run(r""" 2 + 3 < 2 * 3 """) is True

        assert toil.run(r""" print(2 + 3) """) is None
        assert capsys.readouterr().out == "5\n"

    def test_invalid_expression(self):
        with pytest.raises(Exception, match="Invalid stack state"):
            toil.execute([('halt',)]) # ->
        with pytest.raises(Exception, match="Invalid stack state"):
            toil.execute([('const', 2), ('const', 3), ('halt',)])
        with pytest.raises(Exception, match="Invalid instruction"):
            toil.execute([('not_op',), ('halt',)])
        with pytest.raises(Exception, match="Unsupported expression"):
            toil.compile((2, 3, 4))


import os, sys, io, runpy

class TestCommandLine:
    def test_from_file(self, tmp_path, capsys, monkeypatch):
        script_file = tmp_path / "test.toil"
        script_file.write_text("0")

        toil_script = os.path.join(os.path.dirname(__file__), "toil.py")
        monkeypatch.setattr(sys, "argv", ["toil.py", "--run", str(script_file)])

        with pytest.raises(SystemExit) as e:
            runpy.run_path(toil_script, run_name="__main__")

        assert e.value.code == 0
        assert capsys.readouterr().out == ""

    def test_repl(self, capsys, monkeypatch):
        toil_script = os.path.join(os.path.dirname(__file__), "toil.py")
        monkeypatch.setattr(sys, "argv", ["toil.py", "--rcepl"])
        monkeypatch.setattr(sys, "stdin", io.StringIO("0\n"))

        with pytest.raises(SystemExit) as e:
            runpy.run_path(toil_script, run_name="__main__")

        out = capsys.readouterr().out
        assert "AST:\n0" in out
        assert "Code:" in out
        assert "Output:" in out
        assert "Result:\n0\n" in out
        assert e.value.code == 0


if __name__ == "__main__":
    pytest.main([__file__])
