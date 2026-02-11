from toil import evaluate

def test_evaluate_value():
    assert evaluate(None) is None
    assert evaluate(5) == 5
    assert evaluate(True) is True
    assert evaluate(False) is False

def test_evaluate_if():
    assert evaluate(("if", True, 2, 3)) == 2
    assert evaluate(("if", False, 2, 3)) == 3
    assert evaluate(("if", ("if", True, True, False), 2, 3)) == 2
    assert evaluate(("if", True, ("if", True, 2, 3), 4)) == 2
    assert evaluate(("if", False, 2, ("if", False, 3, 4))) == 4


