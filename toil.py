class Environment:
    def __init__(self, parent=None):
        self.parent = parent
        self.vars = {}

def define(env, name, val):
    env.vars[name] = val
    return val

def lookup(env, name):
    if name in env.vars:
        return env.vars[name]
    elif env.parent is not None:
        return lookup(env.parent, name)
    else:
        assert False, f"Undefined variable @ lookup(): {name}"


def evaluate(expr, env):
    match expr:
        case None | bool() | int():
            return expr
        case str(name):
            return lookup(env, name)
        case ("define", name, val):
            return define(env, name, evaluate(val, env))
        case ("seq", exprs):
            return evaluate_seq(exprs, env)
        case ("if", cond_expr, then_expr, else_expr):
            return evaluate_if(cond_expr, then_expr, else_expr, env)
        case ("func", params, body):
            return expr
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
        case ("func", params, body):
            new_env = Environment(env)
            for param, arg in zip(params, args_val):
                define(new_env, param, arg)
            return evaluate(body, new_env)
        case _:
            assert False, f"Illegal operator @ eval_op(): {op_val}"

def init_env():
    env = Environment()

    define(env, "add", lambda args: args[0] + args[1])
    define(env, "sub", lambda args: args[0] - args[1])
    define(env, "mul", lambda args: args[0] * args[1])
    define(env, "equal", lambda args: args[0] == args[1])
    define(env, "print", lambda args: print(*args))

    return env

if __name__ == "__main__":
    env = init_env()

    evaluate(("print", [
        ("define", "add2", ("func",["a"], ("add", ["a", 2]))
    )]), env)
    evaluate(("print", [("add2", [3])]), env)

    evaluate(("define", "sum3", ("func", ["a", "b", "c"],
            ("add", ["a", ("add", ["b", "c"])]))
    ), env)
    evaluate(("print", [("sum3", [2, 3, 4])]), env)

    evaluate(("define", "fac", ("func",["n"],
        ("if", ("equal", ["n", 1]),
            1,
            ("mul", ["n", ("fac", [("sub", ["n", 1])])])
        )
    )), env)
    evaluate(("print", [("fac", [1])]), env)
    evaluate(("print", [("fac", [3])]), env)
    evaluate(("print", [("fac", [5])]), env)
