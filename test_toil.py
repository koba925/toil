from toil import evaluate

def test_evaluate_value():
    assert evaluate(None) is None
    assert evaluate(5) == 5
    assert evaluate(True) is True
    assert evaluate(False) is False
