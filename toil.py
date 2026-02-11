def evaluate(expr):
    match expr:
        case None | bool() | int():
            return expr
        case ("if", cond_expr, then_expr, else_expr):
            return evaluate_if(cond_expr, then_expr, else_expr)
    return expr

def evaluate_if(cond_expr, then_expr, else_expr):
    if evaluate(cond_expr):
        return evaluate(then_expr)
    else:
        return evaluate(else_expr)
