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
        case ("scope", expr):
            return evaluate(expr, Environment(env))
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

if __name__ == "__main__":
    env = Environment()

    program = ("seq", [
        ("define", "a", 2),
        ("define", "b", ("if", ("if", True, False, True), 3, 4)),
        "b"
    ])
    print(evaluate(program, env)) # 4
    print(evaluate("a", env))     # 2
