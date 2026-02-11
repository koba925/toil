import pytest
from toil import evaluate, Environment


def test_evaluate_value():
    env = Environment()
    assert evaluate(None, env) is None
    assert evaluate(5, env) == 5
    assert evaluate(True, env) is True
    assert evaluate(False, env) is False

def test_seq():
    env = Environment()
    assert evaluate(("seq", [2, 3]), env) == 3

    assert evaluate(("seq", [
        ("define", "a", 2),
        ("define", "b", 3),
    ]), env) == 3
    assert evaluate("a", env) == 2
    assert evaluate("b", env) == 3

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

def test_evaluate_scope():
    env = Environment()
    evaluate(("define", "a", 2), env)
    assert evaluate(("scope", ("seq", [
        ("define", "a", 3),
        ("define", "b", 4),
        "a"
    ])), env) == 3
    assert evaluate("a", env) == 2

    with pytest.raises(AssertionError):
        evaluate("b", env)
