#! /usr/bin/env python3

class Sym(str):
    def __repr__(self): return self

class Expr(tuple):
    def __repr__(self):
        return "{" + " ".join(map(repr, self)) + "}"


def is_name_first(c): return c.isalpha() or c == "_"
def is_name_rest(c): return c.isalnum() or c == "_"
def is_name(expr): return isinstance(expr, Sym) and is_name_first(expr[0])


class Scanner:
    def __init__(self, src):
        self._src = src
        self._pos = 0
        self._tokens = []

    def tokenize(self):
        while True:
            while self._current_char().isspace():
                self._advance()

            if self._current_char() == "#":
                while self._current_char() not in ("\n", Sym("$EOF")):
                    self._advance()
                continue

            match self._current_char():
                case Sym("$EOF"):
                    self._tokens.append(Sym("$EOF"))
                    break
                case ch if ch.isnumeric():
                    self._number()
                case c if is_name_first(c):
                    self._name()
                case ("=" | "!" | "<" | ">" | ":") as ch:
                    start = self._pos
                    self._advance()
                    if self._current_char() == "=":
                        self._advance()
                    self._tokens.append(Sym(self._src[start:self._pos]))
                case ("+" | "-" | "*" | "/" | "%" | "(" | ")" | "[" | "]" | ";" | ",") as ch:
                    self._tokens.append(Sym(ch))
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
            case _: self._tokens.append(Sym(token))

    def _advance(self):
        self._pos += 1

    def _current_char(self):
        if self._pos < len(self._src):
            return self._src[self._pos]
        else:
            return Sym("$EOF")


class Parser:
    def __init__(self, tokens):
        self._tokens = tokens
        self._pos = 0

    def parse(self):
        expr = self._expression()
        assert self._current_token() == Sym("$EOF"), \
            f"Extra token @ parse(): {self._current_token()}"
        return expr

    def _expression(self):
        return self._sequence()

    def _sequence(self):
        exprs = [self._define_assign()]
        while self._current_token() == Sym(";"):
            self._advance()
            exprs.append(self._define_assign())
        return exprs[0] if len(exprs) == 1 else Expr((Sym("seq"), exprs))

    def _define_assign(self):
        return self._binary_right({
            Sym(":="): Sym("define"), Sym("="): Sym("assign")
        }, self._and_or)

    def _and_or(self):
        left = self._not()
        while (op := self._current_token()) in (Sym("and"), Sym("or")):
            self._advance()
            right = self._not()
            if op == Sym("and"):
                left = Expr((Sym("if"), left, right, left))
            else:
                left = Expr((Sym("if"), left, left, right))
        return left

    def _not(self):
        return self._unary({
            Sym("not"): Sym("not")
        }, self._comparison)

    def _comparison(self):
        return self._binary_left({
            Sym("=="): Sym("equal"), Sym("!="): Sym("not_equal"),
            Sym("<"): Sym("less"), Sym(">"): Sym("greater"),
            Sym("<="): Sym("less_equal"), Sym(">="): Sym("greater_equal")
        }, self._add_sub)

    def _add_sub(self):
        return self._binary_left({
            Sym("+"): Sym("add"), Sym("-"): Sym("sub")
        }, self._mul_div_mod)

    def _mul_div_mod(self):
        return self._binary_left({
            Sym("*"): Sym("mul"), Sym("/"): Sym("div"), Sym("%"): Sym("mod")
        }, self._neg)

    def _neg(self):
        return self._unary({Sym("-"): Sym("neg")}, self._call_index)

    def _call_index(self):
        target = self._primary()
        while self._current_token() in (Sym("("), Sym("[")):
            match self._current_token():
                case Sym("("):
                    self._advance()
                    target = Expr((target, self._comma_separated_exprs(Sym(")"))))
                case Sym("["):
                    self._advance()
                    index = self._expression()
                    self._consume(Sym("]"))
                    target = Expr((Sym("index"), [target, index]))
        return target

    def _primary(self):
        match self._current_token():
            case Sym("("): return self._paren()
            case None | bool() | int(): return self._advance()
            case Sym("func"): return self._func()
            case Sym("scope"): return self._scope()
            case Sym("if"): return self._if()
            case Sym("while"): return self._while()
            case Sym("deffunc"): return self._deffunc()
            case Sym(name) if is_name(name): return self._advance()
            case unexpected:
                assert False, f"Unexpected token @ _primary(): {unexpected}"

    def _paren(self):
        self._advance()
        expr = self._expression()
        self._consume(Sym(")"))
        return expr

    def _func(self):
        self._advance()
        params = self._comma_separated_exprs(Sym("do"))
        body_expr = self._expression()
        self._consume(Sym("end"))
        return Expr((Sym("func"), params, body_expr))

    def _scope(self):
        self._advance()
        body_expr = self._expression()
        self._consume(Sym("end"))
        return Expr((Sym("scope"), body_expr))

    def _if(self):
        self._advance()
        cond_expr = self._expression()
        self._consume(Sym("then"))
        then_expr = self._expression()
        if self._current_token() == Sym("elif"):
            else_expr = self._if()
        elif self._current_token() == Sym("else"):
            self._advance()
            else_expr = self._expression()
            self._consume(Sym("end"))
        else:
            else_expr = None
            self._consume(Sym("end"))
        return Expr((Sym("if"), cond_expr, then_expr, else_expr))

    def _while(self):
        self._advance()
        cond_expr = self._expression()
        self._consume(Sym("do"))
        body_expr = self._expression()
        self._consume(Sym("end"))
        return Expr((Sym("while"), cond_expr, body_expr))

    def _deffunc(self):
        self._advance()
        name = self._advance()
        assert is_name(name), f"Expected function name @ deffunc: {name}"
        self._consume(Sym("params"))
        params = self._comma_separated_exprs(Sym("do"))
        body_expr = self._expression()
        self._consume(Sym("end"))
        return Expr((Sym("define"), [name, Expr((Sym("func"), params, body_expr))]))

    def _binary_left(self, ops, sub_elem):
        left = sub_elem()
        while (op := self._current_token()) in ops:
            self._advance()
            right = sub_elem()
            left = Expr((ops[op], [left, right]))
        return left

    def _binary_right(self, ops, sub_elem):
        left = sub_elem()
        if (op := self._current_token()) in ops:
            self._advance()
            right = self._binary_right(ops, sub_elem)
            return Expr((ops[op], [left, right]))
        return left

    def _unary(self, ops, sub_elem):
        if (op := self._current_token()) in ops:
            self._advance()
            return Expr((ops[op], [self._unary(ops, sub_elem)]))
        else:
            return sub_elem()

    def _comma_separated_exprs(self, terminate):
        cse = []
        if self._current_token() != terminate:
            cse.append(self._expression())
            while self._current_token() == Sym(","):
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
        content = "__builtins__" if Sym("__builtins__") in self._vars else \
                  ", ".join(self._vars)
        return f"[{content}]" + (f" < {self._parent}" if self._parent else "")

    def define(self, name, val):
        self._vars[name] = val
        return val

    def lookup(self, name):
        if name in self._vars:
            return self
        elif self._parent is not None:
            return self._parent.lookup(name)
        else:
            return None

    def val(self, name):
        assert name in self._vars, f"Undefined variable @ val(): {name}"
        return self._vars[name]

    def set_val(self, name, val):
        assert name in self._vars, f"Undefined variable @ set_val(): {name}"
        self._vars[name] = val
        return val


class Evaluator:
    def evaluate(self, expr, env):
        match expr:
            case None | bool() | int():
                return expr
            case Sym(name):
                frame = env.lookup(name)
                assert frame is not None, f"Undefined variable @ evaluate(): {name}"
                return frame.val(name)
            case Expr((Sym("define"), [Sym(name), val])):
                return env.define(name, self.evaluate(val, env))
            case Expr((Sym("assign"), [left_expr, right_expr])):
                return self._evaluate_assign(left_expr, right_expr, env)
            case Expr((Sym("seq"), exprs)):
                return self._evaluate_seq(exprs, env)
            case Expr((Sym("if"), cond_expr, then_expr, else_expr)):
                return self._evaluate_if(cond_expr, then_expr, else_expr, env)
            case Expr((Sym("while"), cond_expr, body_expr)):
                return self._evaluate_while(cond_expr, body_expr, env)
            case Expr((Sym("func"), params, body)):
                return Expr((Sym("closure"), params, body, env))
            case Expr((Sym("scope"), expr)):
                return self.evaluate(expr, Environment(env))
            case Expr((op_expr, args_expr)):
                return self._eval_op(op_expr, args_expr, env)
            case unexpected:
                assert False, f"Unexpected expression @ evaluate(): {unexpected}"

    def _evaluate_assign(self, left_expr, right_expr, env):
        right_val = self.evaluate(right_expr, env)
        match left_expr:
            case Sym(name):
                frame = env.lookup(name)
                assert frame is not None, \
                    f"Undefined variable @ _evaluate_assign(): {name}"
                return frame.set_val(name, right_val)
            case Expr((Sym("index"), [coll_expr, index_expr])):
                coll_val = self.evaluate(coll_expr, env)
                index_val = self.evaluate(index_expr, env)
                assert isinstance(coll_val, list), \
                    f"Index target not array @ _evaluate_assign(): {coll_val}"
                assert isinstance(index_val, int), \
                    f"Index not int @ _evaluate_assign(): {index_val}"
                coll_val[index_val] = right_val
                return right_val
            case unexpected:
                assert False, f"Illegal assign target @ _evaluate_assign(): {unexpected}"

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

    def _evaluate_while(self, cond_expr, body_expr, env):
        while self.evaluate(cond_expr, env):
            self.evaluate(body_expr, env)
        return None

    def _eval_op(self, op_expr, args_expr, env):
        op_val = self.evaluate(op_expr, env)
        args_val = [self.evaluate(arg, env) for arg in args_expr]

        match op_val:
            case c if callable(c):
                return c(args_val)
            case Expr((Sym("closure"), params, body, closure_env)):
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
        self._env.define(Sym("__builtins__"), None)

        self._env.define(Sym("add"), lambda args: args[0] + args[1])
        self._env.define(Sym("sub"), lambda args: args[0] - args[1])
        self._env.define(Sym("mul"), lambda args: args[0] * args[1])
        self._env.define(Sym("div"), lambda args: args[0] // args[1])
        self._env.define(Sym("mod"), lambda args: args[0] % args[1])
        self._env.define(Sym("neg"), lambda args: -args[0])

        self._env.define(Sym("equal"), lambda args: args[0] == args[1])
        self._env.define(Sym("not_equal"), lambda args: args[0] != args[1])
        self._env.define(Sym("less"), lambda args: args[0] < args[1])
        self._env.define(Sym("greater"), lambda args: args[0] > args[1])
        self._env.define(Sym("less_equal"), lambda args: args[0] <= args[1])
        self._env.define(Sym("greater_equal"), lambda args: args[0] >= args[1])
        self._env.define(Sym("not"), lambda args: not args[0])

        self._env.define(Sym("arr"), lambda args: args)
        self._env.define(Sym("len"), lambda args: len(args[0]))
        self._env.define(Sym("index"), lambda args: args[0][args[1]])
        self._env.define(Sym("slice"), lambda args: args[0][args[1]:args[2]])
        self._env.define(Sym("push"), lambda args: args[0].append(args[1]))
        self._env.define(Sym("pop"), lambda args: args[0].pop())

        self._env.define(Sym("print"), lambda args: print(*args))

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
    import sys

    i = Interpreter().init_env()

    def repl():
        while True:
            print("\nInput source and enter Ctrl+D:")
            if (src := sys.stdin.read()) == "":
                exit(0)
            try:
                ast = i.ast(src)
                print("AST:", ast, sep="\n")
                print("Output:")
                result = i.evaluate(ast)
                print("Result:", result, sep="\n")
            except AssertionError as e:
                print("Error:", e, sep="\n")

    def run(filename):
        with open(filename, "r") as f:
            result = i.go(f.read())
        exit(result if isinstance(result, int) else 0)

    if len(sys.argv) > 1:
        if sys.argv[1] == "--repl":
            repl()
        else:
            run(sys.argv[1])

    # Example

    print(i.ast(""" arr() """)) # -> {arr []}
    print(i.go(""" arr() """)) # -> []

    print(i.ast(""" arr(2) """)) # -> {arr [2]}
    print(i.go(""" arr(2) """)) # -> [2]
    print(i.go(""" arr(2)[0] """)) # -> 2

    print(i.ast(""" arr(2, 3, arr(4, 5)) """)) # -> {arr [2, 3, {arr [4, 5]}]}
    print(i.go(""" arr(2, 3, arr(4, 5)) """)) # -> [2, 3, [4, 5]]

    i.go(""" a := arr(2, 3, arr(4, 5)) """)
    print(i.ast(""" a[2][0] """)) # -> {index [{index [a, 2]}, 0]}
    print(i.go(""" a[2][0] """)) # -> 4
    print(i.go(""" a[2][-1] """)) # -> 5

    i.go(""" b := arr(2, 3, arr(4, 5)) """)
    print(i.ast(""" b[0] = 6 """)) # -> {assign [{index [b, 0]}, 6]}
    i.go(""" b[0] = 6 """)
    print(i.ast(""" b[2][1] = 7 """)) # -> {assign [{index [{index [b, 2]}, 1]}, 7]}
    i.go(""" b[2][1] = 7 """)
    print(i.go(""" b """)) # -> [6, 3, [4, 7]]

    i.go(""" c := func do arr(add, sub) end """)
    print(i.ast(""" c()[0](2, 3) """)) # ->{{index [{c []}, 0]} [2, 3]}
    print(i.go(""" c()[0](2, 3) """)) # -> 5

    i.go(""" d := arr(2, 3, 4) """)
    print(i.go(""" len(d) """)) # -> 3
    print(i.go(""" slice(d, 1, None) """)) # -> [3, 4]
    print(i.go(""" slice(d, 1, 2) """)) # -> [3]
    print(i.go(""" slice(d, None, 2) """)) # -> [2, 3]
    print(i.go(""" slice(d, None, None) """)) # -> [2, 3, 4]
    print(i.go(""" push(d, 5) """)) # -> None
    print(i.go(""" d """)) # -> [2, 3, 4, 5]
    print(i.go(""" pop(d) """)) # -> 5
    print(i.go(""" d """)) # -> [2, 3, 4]

    print(i.go(""" arr(2, 3) + arr(4, 5) """)) # -> [2, 3, 4, 5]
    print(i.go(""" arr(2, 3) * 3 """)) # -> [2, 3, 2, 3, 2, 3]

    print(i.go("""
        sieve := arr(False, False) + arr(True) * 98;
        i := 2; while i * i < 100 do
            if sieve[i] then
                j := i * i; while j < 100 do
                    sieve[j] = False;
                    j = j + i
                end
            end;
            i = i + 1
        end;

        primes := arr();
        i := 0; while i < 100 do
            if sieve[i] then
                push(primes, i)
            end;
            i = i + 1
        end;

        primes
    """)) # -> [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]

    # i.go(""" 2[3] """) # -> Error
    # i.go(""" 2 = 3 """) # -> Error
    # i.go(""" d[None] = 2 """) # -> Error
    # i.go(""" None[2] = 3 """) # -> Error
