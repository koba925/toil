class Scanner:
    def __init__(self, src):
        self._src = src
        self._pos = 0
        self._tokens = []

    def tokenize(self):
        while True:
            while self._current_char().isspace():
                self._advance()

            match self._current_char():
                case "$EOF":
                    self._tokens.append("$EOF")
                    break
                case ch if ch.isnumeric():
                    self._number()
                case ch if ch in "+-*/%":
                    self._tokens.append(ch)
                    self._advance()
                case invalid:
                    assert False, f"Invalid character @ tokenize(): {invalid}"

        return self._tokens

    def _number(self):
        start = self._pos
        while self._current_char().isnumeric():
            self._advance()
        self._tokens.append(int(self._src[start:self._pos]))

    def _advance(self):
        self._pos += 1

    def _current_char(self):
        if self._pos < len(self._src):
            return self._src[self._pos]
        else:
            return "$EOF"


class Parser:
    def __init__(self, tokens):
        self._tokens = tokens
        self._pos = 0

    def parse(self):
        expr = self._expression()
        assert self._current_token() == "$EOF", \
            f"Extra token @ parse(): {self._current_token()}"
        return expr

    def _expression(self):
        ops = {"+": "add", "-": "sub"}
        left = self._mul_div_mod()
        while (op := self._current_token()) in ops:
            self._advance()
            right = self._mul_div_mod()
            left = (ops[op], [left, right])
        return left

    def _mul_div_mod(self):
        ops = {"*": "mul", "/": "div", "%": "mod"}
        left = self._primary()
        while (op := self._current_token()) in ops:
            self._advance()
            right = self._primary()
            left = (ops[op], [left, right])
        return left

    def _primary(self):
        match self._current_token():
            case int():
                return self._advance()
            case unexpected:
                assert False, f"Unexpected token @ _primary(): {unexpected}"

    def _advance(self):
        self._pos += 1
        return self._tokens[self._pos - 1]

    def _current_token(self):
        return self._tokens[self._pos]

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

class Evaluator:
    def evaluate(self, expr, env):
        match expr:
            case None | bool() | int():
                return expr
            case str(name):
                return env.lookup(name)
            case ("define", str(name), val):
                return env.define(name, self.evaluate(val, env))
            case ("seq", exprs):
                return self._evaluate_seq(exprs, env)
            case ("if", cond_expr, then_expr, else_expr):
                return self._evaluate_if(cond_expr, then_expr, else_expr, env)
            case ("func", params, body):
                return ("closure", params, body, env)
            case ("scope", expr):
                return self.evaluate(expr, Environment(env))
            case (op_expr, args_expr):
                return self._eval_op(op_expr, args_expr, env)
            case unexpected:
                assert False, f"Unexpected expression @ evaluate(): {unexpected}"

    def _evaluate_seq(self, exprs, env):
        val = None
        for expr in exprs:
            val = self.evaluate(expr, env)
        return val

    def _evaluate_if(self, cond_expr, then_expr, else_expr, env):
        if self.evaluate(cond_expr, env):
            return self.evaluate(then_expr, env)
        else:
            return self.evaluate(else_expr, env)

    def _eval_op(self, op_expr, args_expr, env):
        op_val = self.evaluate(op_expr, env)
        args_val = [self.evaluate(arg, env) for arg in args_expr]

        match op_val:
            case c if callable(c):
                return c(args_val)
            case ("closure", params, body, closure_env):
                new_env = Environment(closure_env)
                for param, arg in zip(params, args_val):
                    new_env.define(param, arg)
                return self.evaluate(body, new_env)
            case _:
                assert False, f"Illegal operator @ eval_op(): {op_val}"

class Interpreter:
    def __init__(self):
        self._env = Environment()

    def init_env(self):
        self._env.define("__builtins__", None)
        self._env.define("add", lambda args: args[0] + args[1])
        self._env.define("sub", lambda args: args[0] - args[1])
        self._env.define("mul", lambda args: args[0] * args[1])
        self._env.define("div", lambda args: args[0] // args[1])
        self._env.define("mod", lambda args: args[0] % args[1])
        self._env.define("equal", lambda args: args[0] == args[1])
        self._env.define("print", lambda args: print(*args))

        self._env = Environment(self._env)
        return self

    def scan(self, src):
        return Scanner(src).tokenize()

    def parse(self, tokens):
        return Parser(tokens).parse()

    def evaluate(self, expr):
        return Evaluator().evaluate(expr, self._env)

    def go(self, src):
        tokens = self.scan(src)
        expr = self.parse(tokens)
        return self.evaluate(expr)


if __name__ == "__main__":
    i = Interpreter().init_env()

    print(i.parse(i.scan("""2 * 3"""))) # -> ('mul', [2, 3])
    print(i.parse(i.scan("""6 / 3"""))) # -> ('div', [6, 3])
    print(i.parse(i.scan("""7 % 3"""))) # -> ('mod', [7, 3])
    print(i.parse(i.scan("""2 * 3 + 4"""))) # -> ('add', [('mul', [2, 3]), 4])
    print(i.parse(i.scan("""2 + 3 * 4"""))) # -> ('add', [2, ('mul', [3, 4])])

    print(i.go("""2 * 3""")) # -> 6
    print(i.go("""6 / 3""")) # -> 2
    print(i.go("""7 % 3""")) # -> 1
    print(i.go("""2 * 3 + 4""")) # -> 10
    print(i.go("""2 + 3 * 4""")) # -> 14
