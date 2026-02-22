def is_name_first(c): return c.isalpha() or c == "_"
def is_name_rest(c): return c.isalnum() or c == "_"
def is_name(expr): return isinstance(expr, str) and is_name_first(expr[0])

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
                case c if is_name_first(c):
                    self._name()
                case ch if ch in "=!<>:":
                    start = self._pos
                    self._advance()
                    if self._current_char() == "=":
                        self._advance()
                    self._tokens.append(self._src[start:self._pos])
                case ch if ch in "+-*/%();,":
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

    def _name(self):
        start = self._pos
        self._advance()
        while is_name_rest(self._current_char()):
            self._advance()
        token = self._src[start:self._pos]
        match token:
            case "None": self._tokens.append(None)
            case "True": self._tokens.append(True)
            case "False": self._tokens.append(False)
            case _: self._tokens.append(token)

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
        return self._sequence()

    def _sequence(self):
        exprs = [self._define()]
        while self._current_token() == ";":
            self._advance()
            exprs.append(self._define())
        return exprs[0] if len(exprs) == 1 else ("seq", exprs)

    def _define(self):
        left = self._not()
        if self._current_token() == ":=":
            self._advance()
            return ("define", left, self._define())
        return left

    def _not(self):
        if self._current_token() != "not":
            return self._comparison()
        self._advance()
        return ("not", [self._not()])

    def _comparison(self):
        ops = {
            "==": "equal", "!=": "not_equal",
            "<": "less", ">": "greater",
            "<=": "less_equal", ">=": "greater_equal"
        }

        left = self._add_sub()
        while (op := self._current_token()) in ops:
            self._advance()
            right = self._add_sub()
            left = (ops[op], [left, right])
        return left

    def _add_sub(self):
        ops = {"+": "add", "-": "sub"}
        left = self._mul_div_mod()
        while (op := self._current_token()) in ops:
            self._advance()
            right = self._mul_div_mod()
            left = (ops[op], [left, right])
        return left

    def _mul_div_mod(self):
        ops = {"*": "mul", "/": "div", "%": "mod"}
        left = self._neg()
        while (op := self._current_token()) in ops:
            self._advance()
            right = self._neg()
            left = (ops[op], [left, right])
        return left

    def _neg(self):
        if self._current_token() != "-":
            return self._call()
        self._advance()
        return ("neg", [self._neg()])

    def _call(self):
        func = self._primary()
        while self._current_token() == "(":
            self._advance()
            func = (func, self._comma_separated_exprs(")"))
        return func

    def _primary(self):
        match self._current_token():
            case "(":
                return self._paren()
            case None | bool() | int():
                return self._advance()
            case "func":
                return self._func()
            case "if":
                return self._if()
            case str(name) if is_name(name):
                return self._advance()
            case unexpected:
                assert False, f"Unexpected token @ _primary(): {unexpected}"

    def _paren(self):
        self._advance()
        expr = self._expression()
        self._consume(")")
        return expr

    def _func(self):
        self._advance()
        params = self._comma_separated_exprs("do")
        body = self._expression()
        self._consume("end")
        return ("func", params, body)

    def _if(self):
        self._advance()
        cond_expr = self._expression()
        self._consume("then")
        then_expr = self._expression()
        self._consume("else")
        else_expr = self._expression()
        self._consume("end")
        return ("if", cond_expr, then_expr, else_expr)

    def _comma_separated_exprs(self, terminate):
        cse = []
        if self._current_token() != terminate:
            cse.append(self._expression())
            while self._current_token() == ",":
                self._advance()
                cse.append(self._expression())
        self._consume(terminate)
        return cse

    def _consume(self, expected):
        assert self._current_token() == expected, \
            f"Expected `{expected}` @ consume: {self._current_token()}"
        return self._advance()

    def _current_token(self):
        return self._tokens[self._pos]

    def _advance(self):
        self._pos += 1
        return self._tokens[self._pos - 1]


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
        self._env.define("neg", lambda args: -args[0])

        self._env.define("equal", lambda args: args[0] == args[1])
        self._env.define("not_equal", lambda args: args[0] != args[1])
        self._env.define("less", lambda args: args[0] < args[1])
        self._env.define("greater", lambda args: args[0] > args[1])
        self._env.define("less_equal", lambda args: args[0] <= args[1])
        self._env.define("greater_equal", lambda args: args[0] >= args[1])
        self._env.define("not", lambda args: not args[0])

        self._env.define("print", lambda args: print(*args))

        self._env = Environment(self._env)
        return self

    def scan(self, src):
        return Scanner(src).tokenize()

    def parse(self, tokens):
        return Parser(tokens).parse()

    def ast(self, src):
        return self.parse(self.scan(src))

    def evaluate(self, expr):
        return Evaluator().evaluate(expr, self._env)

    def go(self, src):
        return self.evaluate(self.ast(src))


if __name__ == "__main__":
    i = Interpreter().init_env()

    print(i.ast(""" func do 2 end """)) # -> ('func', [], 2)
    print(i.go(""" func do 2 end """)) # -> ('closure', [], 2, ...)
    print(i.go(""" func do 2 end () """)) # -> 2

    print(i.ast(""" func a do a + 2 end """)) # -> ('func', ['a'], ('add', ['a', 2]))
    print(i.go(""" func a do a + 2 end """)) # -> ('closure', ['a'], ('add', ['a', 2]), ...)
    print(i.go(""" func a do a + 2 end (3) """)) # -> 5

    # print(i.ast(""" func a 2 end """)) # -> Error
    # print(i.ast(""" func a do 2 """)) # -> Error

    i.go("""
        fac := func n do
            if n == 1 then 1 else n * fac(n - 1) end
        end;
        print(fac(5))
    """) # prints 120

    i.go("""
        fib := func n do
            if n < 2 then n else fib(n - 1) + fib(n - 2) end
        end;
        print(fib(7))
    """) # prints 13

    i.go("""
        gcd := func a, b do
            if a == 0 then b else gcd(b % a, a) end
        end;
        print(gcd(24, 36))
    """) # prints 12

    i.go("""
        is_even := func n do
            if n == 0 then True else is_odd(n - 1) end
        end;
        is_odd := func n do
            if n == 0 then False else is_even(n - 1) end
        end;
        print(is_even(10));
        print(is_odd(10))
    """) # prints True, then False
