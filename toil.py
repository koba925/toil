def new_env():
    return {}

def define(env, name, val):
    env[name] = val
    return val

def lookup(env, name):
    assert name in env, f"Undefined variable @ lookup(): {name}"
    return env[name]


def evaluate(expr, env):
    match expr:
        case None | bool() | int():
            return expr
        case str(name):
            return lookup(env, name)
        case ("define", name, val):
            return define(env, name, evaluate(val, env))
        case ("if", cond_expr, then_expr, else_expr):
            return evaluate_if(cond_expr, then_expr, else_expr, env)
        case unexpected:
            assert False, f"Unexpected expression @ evaluate(): {unexpected}"

def evaluate_if(cond_expr, then_expr, else_expr, env):
    if evaluate(cond_expr, env):
        return evaluate(then_expr, env)
    else:
        return evaluate(else_expr, env)

if __name__ == "__main__":
    env = new_env()

    print(evaluate(("define", "a", 2), env))        # 2
    print(evaluate("a", env))                       # 2

    print(evaluate(("define", "b", True), env))     # True
    print(evaluate(("if", "b", 2, 3), env))         # 2


    print(evaluate(("define", "c", ("if", False, 2, 3)), env))  # 3
    print(evaluate("c", env))                       # 3


