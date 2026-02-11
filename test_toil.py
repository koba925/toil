import pytest
from toil import evaluate, new_env


def test_evaluate_value():
    env = new_env()
    assert evaluate(None, env) is None
    assert evaluate(5, env) == 5
    assert evaluate(True, env) is True
    assert evaluate(False, env) is False

def test_evaluate_if():
    env = new_env()
    assert evaluate(("if", True, 2, 3), env) == 2
    assert evaluate(("if", False, 2, 3), env) == 3
    assert evaluate(("if", ("if", True, True, False), 2, 3), env) == 2
    assert evaluate(("if", True, ("if", True, 2, 3), 4), env) == 2
    assert evaluate(("if", False, 2, ("if", False, 3, 4)), env) == 4

def test_evaluate_variable():
    env = new_env()
    assert evaluate(("define", "a", 2), env) == 2
    assert evaluate("a", env) == 2

    assert evaluate(("define", "b", True), env) == True
    assert evaluate(("if", "b", 2, 3), env) == 2

    assert evaluate(("define", "c", ("if", False, 2, 3)), env) == 3
    assert evaluate("c", env) == 3


def test_evaluate_undefined_variable():
    env = new_env()
    with pytest.raises(AssertionError):
        evaluate("a", env)
