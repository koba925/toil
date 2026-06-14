def is_ident_first(c): return c.isalpha() or c == "_"
def is_ident_rest(c): return c.isalnum() or c == "_"
def is_ident(s): return is_ident_first(s[0])

class Scanner:
    def __init__(self, src):
        self._src = src
        self._start_pos = 0
        self._current_pos = 0
        self._tokens = []

    def tokenize(self):
        while True:
            while self._current_char().isspace(): self._advance()

            if self._current_char() == "#":
                while self._current_char() not in ("\n", "$EOF"):
                    self._advance()
                continue

            self._start_pos = self._current_pos
            match self._current_char():
                case "$EOF":
                    self._tokens.append("$EOF")
                    break
                case c if c.isdecimal(): self._number()
                case c if is_ident_first(c): self._ident()
                case c if c in "=:":
                    self._advance()
                    if self._current_char() == "=": self._advance()
                    self._tokens.append(self._lexeme())
                case c if c in "+-*/%()<>,;":
                    self._tokens.append(c); self._advance()
                case invalid:
                    assert False, f"Invalid character @ tokenize(): {invalid}"

        return self._tokens

    def _number(self):
        while self._current_char().isdecimal(): self._advance()
        self._tokens.append(int(self._lexeme()))

    def _ident(self):
        self._advance()
        while is_ident_rest(self._current_char()): self._advance()
        match self._lexeme():
            case "None": self._tokens.append(None)
            case "True": self._tokens.append(True)
            case "False": self._tokens.append(False)
            case ident: self._tokens.append(ident)

    def _lexeme(self):
        return self._src[self._start_pos:self._current_pos]

    def _advance(self): self._current_pos += 1

    def _current_char(self):
        if self._current_pos < len(self._src):
            return self._src[self._current_pos]
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

    def _expression(self): return self._sequence()

    def _sequence(self):
        exprs = [self._define_assign()]
        while self._current_token() == ";":
            self._current_and_advance()
            exprs.append(self._define_assign())
        return exprs[0] if len(exprs) == 1 else ("seq", exprs)

    def _define_assign(self):
        return self._binary_right({
            ":=": "define", "=": "assign"
        }, self._comparison)

    def _comparison(self):
        return self._binary_left({
            "==": "equal", "<": "less", ">": "greater"
        }, self._add_sub)

    def _add_sub(self):
        return self._binary_left({"+": "add", "-": "sub"}, self._mul_div_mod)

    def _mul_div_mod(self):
        return self._binary_left({
            "*": "mul", "/": "div", "%": "mod"
        }, self._call)

    def _call(self):
        target = self._primary()
        while self._current_token() == "(":
            self._current_and_advance()
            target = (target, self._comma_separated_exprs(")"))
            self._consume(")")
        return target

    def _primary(self):
        match self._current_token():
            case None | bool() | int(): return self._current_and_advance()
            case "(": return self._group()
            case "func": return self._func()
            case "def": return self._def()
            case "scope": return self._scope()
            case "if": return self._if()
            case "while": return self._while()
            case str(name) if is_ident(name): return self._current_and_advance()
            case invalid:
                assert False, f"Invalid token @ _primary(): {invalid}"

    def _group(self):
        self._current_and_advance()
        expr = self._expression()
        self._consume(")")
        return expr

    def _func(self):
        self._current_and_advance()
        params = self._comma_separated_exprs("do")
        self._consume("do")
        body_expr = self._expression()
        self._consume("end")
        return ("func", [params, body_expr])

    def _def(self):
        self._current_and_advance()
        call_expr = self._expression()
        self._consume("do")
        body_expr = self._expression()
        self._consume("end")
        match call_expr:
            case (name, params):
                return ("define", [name, ("func", [params, body_expr])])
            case str():
                return ("define", [call_expr, ("func", [[], body_expr])])
            case _:
                assert False, f"Invalid def syntax @ _def(): {call_expr}"

    def _scope(self):
        self._current_and_advance()
        body_expr = self._expression()
        self._consume("end")
        return ("scope", [body_expr])

    def _if(self):
        self._current_and_advance()
        cond_expr = self._expression()
        self._consume("then")
        then_expr = self._expression()
        self._consume("else")
        else_expr = self._expression()
        self._consume("end")
        return ("if", [cond_expr, then_expr, else_expr])

    def _while(self):
        self._current_and_advance()
        cond_expr = self._expression()
        self._consume("do")
        body_expr = self._expression()
        self._consume("end")
        return ("while", [cond_expr, body_expr])

    def _binary_left(self, ops, sub_elem):
        left = sub_elem()
        while type(op := self._current_token()) is str and op in ops:
            self._current_and_advance()
            right = sub_elem()
            left = (ops[op], [left, right])
        return left

    def _binary_right(self, ops, sub_elem):
        left = sub_elem()
        if type(self._current_token()) is str and \
                (op := self._current_token()) in ops:
            self._current_and_advance()
            right = self._binary_right(ops, sub_elem)
            return (ops[op], [left, right])
        return left

    def _comma_separated_exprs(self, terminator):
        cse = []
        if self._current_token() != terminator:
            cse.append(self._expression())
            while self._current_token() == ",":
                self._current_and_advance()
                cse.append(self._expression())
        return cse

    def _consume(self, expected):
        assert self._current_token() == expected, \
            f"Expected {expected} @ _consume(): {self._current_token()}"
        return self._current_and_advance()

    def _current_token(self): return self._tokens[self._pos]

    def _current_and_advance(self):
        self._pos += 1
        return self._tokens[self._pos - 1]


class Environment:
    def __init__(self, parent=None):
        self._parent = parent
        self._vars = {}

    def define(self, name, val):
        self._vars[name] = val
        return val

    def assign(self, name, val):
        if name in self._vars:
            self._vars[name] = val
            return val
        elif self._parent:
            return self._parent.assign(name, val)
        else:
            assert False, f"Undefined variable @ assign(): {name}"

    def val(self, name):
        if name in self._vars: return self._vars[name]
        elif self._parent:
            return self._parent.val(name)
        else:
            assert False, f"Undefined variable @ val(): {name}"

    def bind(self, params, args):
        for param, arg in zip(params, args):
            self.define(param, arg)


class Evaluator:
    def eval(self, expr, env):
        match expr:
            case None | bool() | int(): return expr
            case ("func", [params, body_expr]):
                return ("closure", [params, body_expr, env])
            case str(name): return env.val(name)
            case ("scope", [body_expr]):
                return self.eval(body_expr, Environment(env))
            case ("define", [name, expr]):
                return env.define(name, self.eval(expr, env))
            case ("assign", [name, expr]):
                return env.assign(name, self.eval(expr, env))
            case ("seq", exprs): return self._seq(exprs, env)
            case ("if", [cond_expr, then_expr, else_expr]):
                return self._if(cond_expr, then_expr, else_expr, env)
            case ("while", [cond_expr, body_expr]):
                return self._while(cond_expr, body_expr, env)
            case (op_expr, args_expr):
                return self._op(op_expr, args_expr, env)
            case _:
                assert False, f"Unexpected expression @ eval(): {expr}"

    def _seq(self, exprs, env):
        val = None
        for expr in exprs: val = self.eval(expr, env)
        return val

    def _if(self, cond_expr, then_expr, else_expr, env):
        if self.eval(cond_expr, env):
            return self.eval(then_expr, env)
        else:
            return self.eval(else_expr, env)

    def _while(self, cond_expr, body_expr, env):
        val = None
        while self.eval(cond_expr, env): val = self.eval(body_expr, env)
        return val

    def _op(self, op_expr, args_expr, env):
        op_val = self.eval(op_expr, env)
        args_val = [self.eval(arg, env) for arg in args_expr]
        match op_val:
            case f if callable(f): return f(args_val)
            case ("closure", [params, body_expr, closure_env]):
                new_env = Environment(closure_env)
                new_env.bind(params, args_val)
                return self.eval(body_expr, new_env)
            case _:
                assert False, f"Invalid operator @ _op(): {op_val}"


class VM:
    def __init__(self, code):
        self._code = code
        self._ip = 0
        self._stack = []

    def execute(self):
        while (inst := self._code[self._ip]) != ("halt",):
            self._ip += 1
            match inst:
                case ("const", val): self._stack.append(val)
                case _:
                    assert False, f"Invalid instruction @ execute(): {inst}"
        assert len(self._stack) == 1, f"Invalid stack state @ execute(): {self._stack}"
        return self._stack.pop()


class Interpreter:
    def __init__(self):
        self._env = Environment()
        self._builtins()

    def _builtins(self):
        self._env.define("add", lambda args: args[0] + args[1])
        self._env.define("sub", lambda args: args[0] - args[1])
        self._env.define("mul", lambda args: args[0] * args[1])
        self._env.define("div", lambda args: args[0] // args[1])
        self._env.define("mod", lambda args: args[0] % args[1])
        self._env.define("equal", lambda args: args[0] == args[1])
        self._env.define("less", lambda args: args[0] < args[1])
        self._env.define("greater", lambda args: args[0] > args[1])
        self._env.define("print", lambda args: print(*args))

        self._env = Environment(self._env)

    def scan(self, src):
        return Scanner(src).tokenize()

    def parse(self, tokens):
        return Parser(tokens).parse()

    def ast(self, src):
        return self.parse(self.scan(src))

    def eval(self, expr):
        return Evaluator().eval(expr, self._env)

    def walk(self, src):
        return self.eval(self.ast(src))

    def execute(self, code):
        return VM(code).execute()


if __name__ == "__main__":
    import sys

    toil = Interpreter()

    def repl():
        while True:
            print("\nInput source and enter Ctrl+D (Linux/Mac) or Ctrl+Z (Windows):")
            if (src := sys.stdin.read()) == "":
                exit(0)
            try:
                expr = toil.ast(src)
                print("AST:", expr, sep="\n")
                print("Output:")
                result = toil.eval(expr)
                print("Result:", result, sep="\n")
            except AssertionError as e:
                print("Error:", e, sep="\n")

    def from_file(filename):
        with open(filename, "r") as f: result = toil.walk(f.read())
        exit(result if isinstance(result, int) else 255)

    match sys.argv:
        case [_]: pass
        case [_, "--repl"]: repl()
        case [_, filename]: from_file(filename)
        case _: assert False, f"Invalid command line: {sys.argv}"

    # Example

    print("Stack machine:")
    print(toil.execute([('const', 2), ('halt',)])) # -> 2
    print(toil.execute([('const', None), ('halt',)])) # -> None
    print(toil.execute([('const', True), ('halt',)])) # -> True
    print(toil.execute([('const', False), ('halt',)])) # -> False

    # toil.execute([('halt',)]) # -> Invalid stack state
    # toil.execute([('const', 2), ('const', 3), ('halt',)]) # -> Invalid stack state
    # toil.execute([('not_op',), ('halt',)]) # -> Invalid instruction
