import pytest
from toil import Interpreter

toil = Interpreter()

class TestEvaluator:
    def test_constants(self):
        assert toil.eval(None) is None
        assert toil.eval(True) is True
        assert toil.eval(False) is False
        assert toil.eval(2) == 2

        with pytest.raises(AssertionError, match="Unexpected expression"):
            toil.eval([])

    def test_sequence(self, capsys):
        assert toil.eval(("seq", [])) is None
        assert toil.eval(("seq", [("add", [2, 3])])) == 5

        assert toil.eval(("seq", [("print", [2]), 3])) == 3
        assert capsys.readouterr().out == "2\n"

        assert toil.eval(("seq", [("print", [2]), ("seq", [("print", [3]), 4])])) == 4
        assert capsys.readouterr().out == "2\n3\n"

    def test_if(self):
        assert toil.eval(("if", [("equal", [2, 2]), 3, 4])) == 3
        assert toil.eval(("if", [("equal", [2, 3]), 4, 5])) == 5
        assert toil.eval(("if", [True, ("seq", [2, 3]), 4])) == 3
        assert toil.eval(("if", [False, 2, ("if", [True, 3, 4])])) == 3

    def test_variable(self):
        assert toil.eval(("define", ["a", ("add", [2, 3])])) == 5
        assert toil.eval("a") == 5
        assert toil.eval(("if", [("equal", ["a", 5]), 2, 3])) == 2
        assert toil.eval(("define", ["a", 6])) == 6
        assert toil.eval("a") == 6

    def test_scope_and_assign(self, capsys):
        toil.eval(("define", ["a", 2]))
        assert toil.eval(("assign", ["a", 3])) == 3
        assert toil.eval("a") == 3

        with pytest.raises(AssertionError, match="Undefined variable"):
            toil.eval(("assign", ["b", 2]))

        assert toil.eval(("scope", ["a"])) == 3

        toil.eval(("scope", [("seq", [
            ("define", ["a", 4]),
            ("print", ["a"])
        ])]))
        assert capsys.readouterr().out == "4\n"

        assert toil.eval("a") == 3

        toil.eval(("scope", [("seq", [
            ("assign", ["a", 4]),
            ("print", ["a"])
        ])]))
        assert capsys.readouterr().out == "4\n"

        assert toil.eval("a") == 4

        toil.eval(("scope", [("seq", [
            ("define", ["b", 2]),
            ("print", ["b"])
        ])]))
        assert capsys.readouterr().out == "2\n"

        with pytest.raises(AssertionError, match="Undefined variable"):
            toil.eval("b")

    def test_builtins(self, capsys):
        assert toil.eval(("add", [2, 3])) == 5
        assert toil.eval(("sub", [3, 2])) == 1
        assert toil.eval(("mul", [2, 3])) == 6
        assert toil.eval(("div", [6, 3])) == 2
        assert toil.eval(("mod", [7, 3])) == 1

        assert toil.eval(("equal", [2, 2])) is True
        assert toil.eval(("equal", [2, 3])) is False

        assert toil.eval(("less", [2, 2])) is False
        assert toil.eval(("less", [2, 3])) is True

        assert toil.eval(("greater", [2, 2])) is False
        assert toil.eval(("greater", [3, 2])) is True

        assert toil.eval(("print", [2])) is None
        assert capsys.readouterr().out == "2\n"

        assert toil.eval(("print", [2, 3])) is None
        assert capsys.readouterr().out == "2 3\n"

        assert toil.eval(("print", [("equal", [("add", [2, 3]), 5])])) is None
        assert capsys.readouterr().out == "True\n"

        assert callable(toil.eval("add"))
        toil.eval(("define", ["myadd", "add"]))
        assert toil.eval(("myadd", [2, 3])) == 5

        with pytest.raises(AssertionError, match=r"Undefined variable @ val\(\): not_defined"):
            toil.eval(("not_defined", []))

    def test_user_functions(self):
        toil.eval(("define", ["myadd", ("func", [["a", "b"], ("add", ["a", "b"])])]))
        assert toil.eval(("myadd", [2, 3])) == 5

        assert toil.eval(("myadd", [("myadd", [2, 3]), ("add", [4, 5])])) == 14

        assert toil.eval((
            ("func", [["a", "b"], ("add", ["a", "b"])]),
            [2, 3]
        )) == 5

        assert toil.eval(("seq", [
            ("define", ["twice", ("func", [["f", "x"], ("f", [("f", ["x"])])])]),
            ("define", ["double", ("func", [["x"], ("mul", ["x", 2])])]),
            ("twice", ["double", 3])
        ])) == 12

        with pytest.raises(AssertionError, match="Undefined variable"):
            toil.eval(("not_defined", []))
        with pytest.raises(AssertionError, match="Invalid operator"):
            toil.eval((2, [3, 4]))

        assert toil.eval(("seq", [
            ("define", ["a", 2]),
            ("define", ["f", ("func", [[], "a"])]),
            ("define", ["g", ("func", [[], ("seq", [
                ("define", ["a", 3]),
                ("f", [])
            ])])]),
            ("g", [])
        ])) == 2

        assert toil.eval(("seq", [
            ("define", ["a", 2]),
            ("define", ["f", ("func", [[], "a"])]),
            ("f", [])
        ])) == 2

        assert toil.eval(("scope", [("seq", [
            ("define", ["a", 3]),
            ("f", [])
        ])])) == 2

    def test_while(self, capsys):
        assert toil.eval(("seq", [
            ("define", ["i", 1]),
            ("while", [
                ("less", ["i", 4]),
                ("seq", [
                    ("print", ["i"]),
                    ("assign", ["i", ("add", ["i", 1])])
                ])
            ])
        ])) == 4
        assert capsys.readouterr().out == "1\n2\n3\n"

        assert toil.eval(("seq", [
            ("define", ["i", 1]), ("define", ["sum", 0]),
            ("while", [
                ("less", ["i", 4]),
                ("seq", [
                    ("assign", ["sum", ("add", ["sum", "i"])]),
                    ("assign", ["i", ("add", ["i", 1])])
                ])
            ]),
            "sum"
        ])) == 6

        assert toil.eval(("while", [False, ("div", [1, 0])])) is None

        assert toil.eval(("seq", [
            ("define", ["i", 0]),
            ("while", [
                ("less", ["i", 2]),
                ("seq", [
                    ("define", ["j", 0]),
                    ("while", [
                        ("less", ["j", 3]),
                        ("seq", [
                            ("print", ["i", "j"]),
                            ("assign", ["j", ("add", ["j", 1])])
                        ])
                    ]),
                    ("assign", ["i", ("add", ["i", 1])])
                ])
            ])
        ])) == 2
        assert capsys.readouterr().out == "0 0\n0 1\n0 2\n1 0\n1 1\n1 2\n"

class TestExamples:
    def test_factorial(self):
        toil.eval(("define", ["factorial_rec", ("func", [["n"],
            ("if", [("equal", ["n", 0]),
                1,
                ("mul", ["n", ("factorial_rec", [("sub", ["n", 1])])])
            ])
        ])]))
        assert toil.eval(("factorial_rec", [0])) == 1
        assert toil.eval(("factorial_rec", [1])) == 1
        assert toil.eval(("factorial_rec", [4])) == 24

        toil.eval(("define", ["factorial_iter", ("func", [["n"], ("seq", [
                ("define", ["result", 1]),
                ("while", [("greater", ["n", 0]), ("seq", [
                    ("assign", ["result", ("mul", ["result", "n"])]),
                    ("assign", ["n", ("sub", ["n", 1])]),
                ])]),
                "result"
        ])])]))
        assert toil.eval(("factorial_iter", [0])) == 1
        assert toil.eval(("factorial_iter", [1])) == 1
        assert toil.eval(("factorial_iter", [4])) == 24

    def test_fibonacci(self):
        toil.eval(("define", ["fib_rec", ("func", [["n"],
            ("if", [("equal", ["n", 0]), 0,
            ("if", [("equal", ["n", 1]), 1,
            ("add", [
                ("fib_rec", [("sub", ["n", 1])]),
                ("fib_rec", [("sub", ["n", 2])])
            ])])])
        ])]))
        assert toil.eval(("fib_rec", [0])) == 0
        assert toil.eval(("fib_rec", [1])) == 1
        assert toil.eval(("fib_rec", [6])) == 8

        toil.eval(("define", ["fib_iter", ("func", [["n"], ("seq", [
            ("define", ["a", 0]),
            ("define", ["b", 1]),
            ("while", [("greater", ["n", 0]), ("seq", [
                ("define", ["tmp", "b"]),
                ("assign", ["b", ("add", ["a", "b"])]),
                ("assign", ["a", "tmp"]),
                ("assign", ["n", ("sub", ["n", 1])])
            ])]),
            "a"
        ])])]))
        assert toil.eval(("fib_iter", [0])) == 0
        assert toil.eval(("fib_iter", [1])) == 1
        assert toil.eval(("fib_iter", [6])) == 8

    def test_GCD(self):
        toil.eval(("define", ["gcd_rec", ("func", [["a", "b"],
            ("if", [("equal", ["b", 0]),
                "a",
                ("gcd_rec", ["b", ("mod", ["a", "b"])])
            ])
        ])]))
        assert toil.eval(("gcd_rec", [12, 18])) == 6

        toil.eval(("define", ["gcd_iter", ("func", [["a", "b"],
            ("while", [("greater", ["b", 0]), ("seq", [
                ("define", ["tmp", "b"]),
                ("assign", ["b", ("mod", ["a", "b"])]),
                ("assign", ["a", "tmp"])
            ])])
        ])]))
        assert toil.eval(("gcd_iter", [12, 18])) == 6

    def test_mutual_recursion(self):
        toil.eval(("define", ["even", ("func", [["n"],
            ("if", [("equal", ["n", 0]), True, ("odd", [("sub", ["n", 1])])])
        ])]))
        toil.eval(("define", ["odd", ("func", [["n"],
            ("if", [("equal", ["n", 0]), False, ("even", [("sub", ["n", 1])])])
        ])]))
        assert toil.eval(("even", [2])) is True
        assert toil.eval(("even", [3])) is False
        assert toil.eval(("odd", [2])) is False
        assert toil.eval(("odd", [3])) is True

    def test_counter(self):
        toil.eval(("define", ["make_counter", ("func", [[], ("seq", [
            ("define", ["count", 0]),
            ("func", [[], ("assign", ["count", ("add", ["count", 1])])])
        ])])]))
        toil.eval(("define", ["c1", ("make_counter", [])]))
        toil.eval(("define", ["c2", ("make_counter", [])]))
        assert toil.eval(("c1", [])) == 1
        assert toil.eval(("c1", [])) == 2
        assert toil.eval(("c2", [])) == 1
        assert toil.eval(("c2", [])) == 2

    def test_binary_search_tree(self, capsys):
        toil.eval(("define", ["node", ("func", [["val", "left", "right"], ("seq", [
            ("func", [["op"],
                ("if", [("equal", ["op", 1]), "val",
                ("if", [("equal", ["op", 2]), "left",
                "right"])])
            ])
        ])])]))

        toil.eval(("define", ["n1", ("node", [2, 3, 4])]))
        assert toil.eval(("n1", [1])) == 2
        assert toil.eval(("n1", [2])) == 3
        assert toil.eval(("n1", [3])) == 4

        toil.eval(("define", ["bst_put", ("func", [["bst", "val"],
            ("if", [("equal", ["bst", None]),
                ("node", ["val", None, None]),
                ("seq", [
                    ("define", ["cur_val", ("bst", [1])]),
                    ("if", [("equal", ["val", "cur_val"]),
                        "bst",
                    ("if", [("less", ["val", "cur_val"]),
                        ("node", ["cur_val", ("bst_put", [("bst", [2]), "val"]), ("bst", [3])]),
                        ("node", ["cur_val", ("bst", [2]), ("bst_put", [("bst", [3]), "val"])])
                    ])])
                ])
            ])
        ])]))
        toil.eval(("define",["bst", None]))
        toil.eval(("define",["bst", ("bst_put", ["bst", 7])]))
        toil.eval(("define",["bst", ("bst_put", ["bst", 3])]))
        toil.eval(("define",["bst", ("bst_put", ["bst", 1])]))
        toil.eval(("define",["bst", ("bst_put", ["bst", 9])]))
        toil.eval(("define",["bst", ("bst_put", ["bst", 5])]))

        toil.eval(("define", ["bst_walk", ("func", [["bst"],
            ("if", [("equal", ["bst", None]),
                None,
                ("seq", [
                    ("bst_walk", [("bst", [2])]),
                    ("print", [("bst", [1])]),
                    ("bst_walk", [("bst", [3])]),
                ])
            ])
        ])]))
        toil.eval(("define", ["bst_find", ("func", [["bst", "val"],
            ("if", [("equal", ["bst", None]),
                False,
                ("seq", [
                    ("define", ["cur_val", ("bst", [1])]),
                    ("if", [("equal", ["val", "cur_val"]),
                        "val",
                    ("if", [("less", ["val", "cur_val"]),
                        ("bst_find", [("bst", [2]), "val"]),
                        ("bst_find", [("bst", [3]), "val"])
                    ])])
                ])
            ])
        ])]))

        toil.eval(("bst_walk",["bst"]))
        assert capsys.readouterr().out == "1\n3\n5\n7\n9\n"

        toil.eval(("seq", [
            ("define", ["i", 0]),
            ("while", [("less", ["i", 10]), ("seq", [
                ("print", [("bst_find",["bst", "i"])]),
                ("assign", ["i", ("add", ["i", 1])])
            ])])
        ]))
        assert capsys.readouterr().out == "False\n1\nFalse\n3\nFalse\n5\nFalse\n7\nFalse\n9\n"

if __name__ == "__main__":
    pytest.main([__file__])
