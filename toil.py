class Environment:
    def __init__(self, parent=None):
        self._parent = parent
        self._vars = {}

    def __repr__(self):
        content = "__builtins__" if "__builtins__" in self._vars else \
                  ", ".join(self._vars)
        return f"[{content}]" + (f" < {self._parent}" if self._parent else "")

    def define(self, name, val):
        self._vars[name] = val
        return val

    def lookup(self, name):
        if name in self._vars:
            return self._vars[name]
        elif self._parent is not None:
            return self._parent.lookup(name)
        else:
            assert False, f"Undefined variable @ lookup(): {name}"


def evaluate(expr, env):
    match expr:
        case None | bool() | int():
            return expr
        case str(name):
            return env.lookup(name)
        case ("define", str(name), val):
            return env.define(name, evaluate(val, env))
        case ("seq", exprs):
            return evaluate_seq(exprs, env)
        case ("if", cond_expr, then_expr, else_expr):
            return evaluate_if(cond_expr, then_expr, else_expr, env)
        case ("func", params, body):
            return ("closure", params, body, env)
        case ("scope", expr):
            return evaluate(expr, Environment(env))
        case (op_expr, args_expr):
            return eval_op(op_expr, args_expr, env)
        case unexpected:
            assert False, f"Unexpected expression @ evaluate(): {unexpected}"

def evaluate_seq(exprs, env):
    val = None
    for expr in exprs:
        val = evaluate(expr, env)
    return val

def evaluate_if(cond_expr, then_expr, else_expr, env):
    if evaluate(cond_expr, env):
        return evaluate(then_expr, env)
    else:
        return evaluate(else_expr, env)

def eval_op(op_expr, args_expr, env):
    op_val = evaluate(op_expr, env)
    args_val = [evaluate(arg, env) for arg in args_expr]

    match op_val:
        case c if callable(c):
            return c(args_val)
        case ("closure", params, body, closure_env):
            new_env = Environment(closure_env)
            for param, arg in zip(params, args_val):
                new_env.define(param, arg)
            return evaluate(body, new_env)
        case _:
            assert False, f"Illegal operator @ eval_op(): {op_val}"

def init_env():
    env = Environment()

    env.define("__builtins__", None)
    env.define("add", lambda args: args[0] + args[1])
    env.define("sub", lambda args: args[0] - args[1])
    env.define("mul", lambda args: args[0] * args[1])
    env.define("equal", lambda args: args[0] == args[1])
    env.define("print", lambda args: print(*args))

    return Environment(env)

if __name__ == "__main__":
    env = init_env()

    evaluate(("print", [
        ("define", "add2", ("func",["a"], ("add", ["a", 2]))
    )]), env) # -> ('closure', ...)
    evaluate(("print", [("add2", [3])]), env) # -> 5

    evaluate(("define", "sum3", ("func", ["a", "b", "c"],
            ("add", ["a", ("add", ["b", "c"])]))
    ), env)
    evaluate(("print", [("sum3", [2, 3, 4])]), env) # -> 9

    evaluate(("define", "fac", ("func",["n"],
        ("if", ("equal", ["n", 1]),
            1,
            ("mul", ["n", ("fac", [("sub", ["n", 1])])])
        )
    )), env)
    evaluate(("print", [("fac", [1])]), env) # -> 1
    evaluate(("print", [("fac", [3])]), env) # -> 6
    evaluate(("print", [("fac", [5])]), env) # -> 120

    evaluate(("define", "make_adder", ("func", ["x"],
        ("func", ["y"], ("add", ["x", "y"]))
    )), env)
    evaluate(("define", "add10", ("make_adder", [10])), env)
    evaluate(("print", [("add10", [5])]), env) # -> 15
