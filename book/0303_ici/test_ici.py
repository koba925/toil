import pytest
from toil import Interpreter

@pytest.fixture(autouse=True)
def setup_toil():
    global toil
    toil = Interpreter()

class TestIntermediateCodeInterpreter:
    def test_constants(self):
        assert toil.run(r""" 2 """) == 2
        assert toil.run(r""" None """) is None
        assert toil.run(r""" True """) is True
        assert toil.run(r""" False """) is False

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
