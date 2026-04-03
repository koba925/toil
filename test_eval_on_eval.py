import pytest
from eval_on_eval import i

class TestCons:
    def test_cons_car_cdr(self):
        i.eval(("define", "p", ("cons", [2, 3])))
        assert i.eval(("car", ["p"])) == 2
        assert i.eval(("cdr", ["p"])) == 3

    def test_linear_list(self):
        i.eval(("define", "l", ("cons", [1, ("cons", [2, None])])))
        assert i.eval(("car", ["l"])) == 1
        assert i.eval(("car", [("cdr", ["l"])])) == 2
        assert i.eval(("cdr", [("cdr", ["l"])])) == None


if __name__ == "__main__":
    pytest.main([__file__])