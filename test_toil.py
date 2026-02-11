import pytest
from toil import evaluate, Environment, init_env


def test_evaluate_value():
    env = Environment()
    assert evaluate(None, env) is None
    assert evaluate(5, env) == 5
    assert evaluate(True, env) is True
    assert evaluate(False, env) is False

def test_seq(capsys):
    env = init_env()
    evaluate(("seq", [
        ("print", [2]),
        ("print", [3])
    ]), env)
    assert capsys.readouterr().out == "2\n3\n"

def test_evaluate_if():
    env = Environment()
    assert evaluate(("if", True, 2, 3), env) == 2
    assert evaluate(("if", False, 2, 3), env) == 3
    assert evaluate(("if", ("if", True, True, False), 2, 3), env) == 2
    assert evaluate(("if", True, ("if", True, 2, 3), 4), env) == 2
    assert evaluate(("if", False, 2, ("if", False, 3, 4)), env) == 4

def test_evaluate_variable():
    env = Environment()
    assert evaluate(("define", "a", 2), env) == 2
    assert evaluate("a", env) == 2

    assert evaluate(("define", "b", True), env) == True
    assert evaluate(("if", "b", 2, 3), env) == 2

    assert evaluate(("define", "c", ("if", False, 2, 3)), env) == 3
    assert evaluate("c", env) == 3

def test_evaluate_undefined_variable():
    env = Environment()
    with pytest.raises(AssertionError):
        evaluate("a", env)

def test_evaluate_scope(capsys):
    env = init_env()

    evaluate(("define", "a", 2), env)
    assert evaluate("a", env) == 2

    assert evaluate(("scope", ("seq", [
        ("define", "a", 3),
        ("print", ["a"]),
        ("define", "b", 4),
        ("print", ["b"]),
        "b"
    ])), env) == 4
    assert capsys.readouterr().out == "3\n4\n"

    assert evaluate("a", env) == 2

    with pytest.raises(AssertionError):
        evaluate("b", env)

def test_builtin_functions(capsys):
    env = init_env()

    assert evaluate(("add", [2, 3]), env) == 5
    assert evaluate(("sub", [5, 3]), env) == 2
    assert evaluate(("mul", [2, 3]), env) == 6

    assert evaluate(("equal", [2, 2]), env) is True
    assert evaluate(("equal", [2, 3]), env) is False

    assert evaluate(("add", [2, ("mul", [3, 4])]), env) == 14

    evaluate(("print", [2, 3]), env)
    assert capsys.readouterr().out == "2 3\n"

    evaluate(("print", [("add", [5, 5])]), env)
    assert capsys.readouterr().out == "10\n"
