from __future__ import annotations

class Ident:
    __match_args__ = ("name",)

    def __init__(self, name: str) -> None: self.name = name
    def __hash__(self): return hash(self.name)
    def __repr__(self): return self.name
    def __str__(self): return self.name
    def __eq__(self, other):
        return isinstance(other, Ident) and self.name == other.name

def is_ident_first(c): return c.isalpha() or c == "_"
def is_ident_rest(c): return c.isalnum() or c == "_"
def is_ident(s): return is_ident_first(s[0])

from typing import Callable

type Token = None | bool | int | Ident
type Expr = None | bool | int | Ident | tuple
type Value = None | bool | int | Callable | tuple
type Instruction = tuple

class Scanner:
    def __init__(self, src: str) -> None:
        self._src = src
        self._start_pos = 0
        self._current_pos = 0
        self._tokens: list[Token] = []

    def tokenize(self) -> list[Token]:
        while (c := self._current_char()) != "$EOF":
            self._start_pos = self._current_pos
            match c:
                case c if c.isspace(): self._advance()
                case "#": self._comment()
                case c if c.isdecimal(): self._number()
                case c if is_ident_first(c): self._ident()
                case c if c in "=<>!:":
                    self._advance()
                    if self._current_char() == "=": self._advance()
                    self._tokens.append(Ident(self._lexeme()))
                case c if c in "+-*/%(),;":
                    self._tokens.append(Ident(c)); self._advance()
                case invalid:
                    assert False, f"Invalid character @ tokenize(): {invalid}"

        self._tokens.append(Ident("$EOF"))
        return self._tokens

    def _comment(self):
        while self._current_char() not in ("\n", "$EOF"):
            self._advance()

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
            case ident: self._tokens.append(Ident(ident))

    def _lexeme(self):
        return self._src[self._start_pos:self._current_pos]

    def _advance(self): self._current_pos += 1

    def _current_char(self):
        if self._current_pos < len(self._src):
            return self._src[self._current_pos]
        else:
            return "$EOF"


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self._tokens = tokens
        self._pos = 0

    def parse(self) -> Expr:
        expr = self._expression()
        assert self._current_token() == Ident("$EOF"), \
            f"Extra token @ parse(): {self._current_token()}"
        return expr

    def _expression(self): return self._sequence()

    def _sequence(self):
        exprs = [self._define_assign()]
        while self._current_token() == Ident(";"):
            self._current_and_advance()
            exprs.append(self._define_assign())
        return exprs[0] if len(exprs) == 1 else (Ident("seq"), exprs)

    def _define_assign(self):
        return self._binary_right({
            Ident(":="): Ident("define"), Ident("="): Ident("assign")
        }, self._and_or)

    def _and_or(self):
        return self._binary_left({
            Ident("and"): Ident("and"), Ident("or"): Ident("or")
        }, self._not)

    def _not(self):
        return self._unary({Ident("not"): Ident("not")}, self._comparison)

    def _comparison(self):
        return self._binary_left({
            Ident("=="): Ident("equal"), Ident("!="): Ident("not_equal"),
            Ident("<"): Ident("less"), Ident(">"): Ident("greater"),
            Ident("<="): Ident("less_equal"), Ident(">="): Ident("greater_equal"),
        }, self._add_sub)

    def _add_sub(self):
        return self._binary_left({
            Ident("+"): Ident("add"), Ident("-"): Ident("sub")
        }, self._mul_div_mod)

    def _mul_div_mod(self):
        return self._binary_left({
            Ident("*"): Ident("mul"), Ident("/"): Ident("div"),
            Ident("%"): Ident("mod")
        }, self._unaries)

    def _unaries(self):
        return self._unary({Ident("-"): Ident("neg")}, self._call)

    def _call(self):
        target = self._primary()
        while self._current_token() == Ident("("):
            self._current_and_advance()
            target = (target, self._comma_separated_exprs(Ident(")")))
            self._consume(Ident(")"))
        return target

    def _primary(self):
        match self._current_token():
            case None | bool() | int(): return self._current_and_advance()
            case Ident("("): return self._group()
            case Ident("func"): return self._func()
            case Ident("def"): return self._def()
            case Ident("scope"): return self._scope()
            case Ident("if"): return self._if()
            case Ident("while"): return self._while()
            case Ident(name) if is_ident(name): return self._current_and_advance()
            case invalid:
                assert False, f"Invalid token @ _primary(): {invalid}"

    def _group(self):
        self._current_and_advance()
        expr = self._expression()
        self._consume(Ident(")"))
        return expr

    def _func(self):
        self._current_and_advance()
        params = self._comma_separated_exprs(Ident("do"))
        self._consume(Ident("do"))
        body_expr = self._expression()
        self._consume(Ident("end"))
        return (Ident("func"), [params, body_expr])

    def _def(self):
        self._current_and_advance()
        call_expr = self._expression()
        self._consume(Ident("do"))
        body_expr = self._expression()
        self._consume(Ident("end"))
        match call_expr:
            case (Ident() as ident, params):
                return (Ident("define"), [ident, (Ident("func"), [params, body_expr])])
            case Ident() as ident:
                return (Ident("define"), [ident, (Ident("func"), [[], body_expr])])
            case _:
                assert False, f"Invalid def syntax @ _def(): {call_expr}"

    def _scope(self):
        self._current_and_advance()
        body_expr = self._expression()
        self._consume(Ident("end"))
        return (Ident("scope"), [body_expr])

    def _if(self):
        self._current_and_advance()
        cond_expr = self._expression()
        self._consume(Ident("then"))
        then_expr = self._expression()
        if self._current_token() == Ident("elif"):
            else_expr = self._if()
        elif self._current_token() == Ident("else"):
            self._current_and_advance()
            else_expr = self._expression()
            self._consume(Ident("end"))
        else:
            else_expr = None
            self._consume(Ident("end"))
        return (Ident("if"), [cond_expr, then_expr, else_expr])

    def _while(self):
        self._current_and_advance()
        cond_expr = self._expression()
        self._consume(Ident("do"))
        body_expr = self._expression()
        self._consume(Ident("end"))
        return (Ident("while"), [cond_expr, body_expr])

    def _binary_left(self, ops, sub_elem):
        left = sub_elem()
        while type(op := self._current_token()) is Ident and op in ops:
            self._current_and_advance()
            left = (ops[op], [left, sub_elem()])
        return left

    def _binary_right(self, ops, sub_elem):
        left = sub_elem()
        if type(op := self._current_token()) is Ident and op in ops:
            self._current_and_advance()
            return (ops[op], [left, self._binary_right(ops, sub_elem)])
        else:
            return left

    def _unary(self, ops, sub_elem):
        if type(op := self._current_token()) is Ident and op in ops:
            self._current_and_advance()
            return (ops[op], [self._unary(ops, sub_elem)])
        else:
            return sub_elem()

    def _comma_separated_exprs(self, terminator):
        cse = []
        if self._current_token() != terminator:
            cse.append(self._expression())
            while self._current_token() == Ident(","):
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
    def __init__(self, parent: Environment | None = None) -> None:
        self._parent = parent
        self._vars: dict[Ident, Value] = {}

    def define(self, ident: Ident, val: Value) -> Value:
        self._vars[ident] = val
        return val

    def assign(self, ident: Ident, val: Value) -> Value:
        if ident in self._vars:
            self._vars[ident] = val
            return val
        elif self._parent:
            return self._parent.assign(ident, val)
        else:
            assert False, f"Undefined variable @ assign(): {ident}"

    def val(self, ident: Ident) -> Value:
        if ident in self._vars: return self._vars[ident]
        elif self._parent:
            return self._parent.val(ident)
        else:
            assert False, f"Undefined variable @ val(): {ident}"

    def bind(self, params: list[Ident], args: list[Value]) -> None:
        for param, arg in zip(params, args):
            self.define(param, arg)


class ReturnException(Exception):
    def __init__(self, val: Value = None) -> None: self.val = val

class BreakException(Exception): pass
class ContinueException(Exception): pass

class Evaluator:
    def eval(self, expr: Expr, env: Environment) -> Value:
        match expr:
            case None | bool() | int(): return expr
            case Ident("return"): raise ReturnException(None)
            case Ident("break"): raise BreakException()
            case Ident("continue"): raise ContinueException()
            case Ident() as ident: return env.val(ident)
            case (Ident("func"), [params, body_expr]):
                return (Ident("closure"), [params, body_expr, env])
            case (Ident("return"), args):
                raise ReturnException(self.eval(args[0], env))
            case (Ident("scope"), [body_expr]):
                return self.eval(body_expr, Environment(env))
            case (Ident("define"), [Ident() as ident, expr]):
                return env.define(ident, self.eval(expr, env))
            case (Ident("assign"), [Ident() as ident, expr]):
                return env.assign(ident, self.eval(expr, env))
            case (Ident("seq"), exprs): return self._seq(exprs, env)
            case (Ident("if"), [cond_expr, then_expr, else_expr]):
                return self._if(cond_expr, then_expr, else_expr, env)
            case (Ident("and"), [left_expr, right_expr]):
                return self.eval(left_expr, env) and self.eval(right_expr, env)
            case (Ident("or"), [left_expr, right_expr]):
                return self.eval(left_expr, env) or self.eval(right_expr, env)
            case (Ident("while"), [cond_expr, body_expr]):
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
        while self.eval(cond_expr, env):
            try:
                val = self.eval(body_expr, env)
            except ContinueException: continue
            except BreakException: return None
        return val

    def _op(self, op_expr, args_expr, env):
        op_val = self.eval(op_expr, env)
        args_val = [self.eval(arg, env) for arg in args_expr]
        match op_val:
            case f if callable(f): return f(args_val)
            case (Ident("closure"), [params, body_expr, closure_env]):
                new_env = Environment(closure_env)
                new_env.bind(params, args_val)
                try:
                    return self.eval(body_expr, new_env)
                except ReturnException as e: return e.val
            case _:
                assert False, f"Invalid operator @ _op(): {op_val}"


class Compiler:
    def __init__(self, expr: Expr) -> None:
        self._expr = expr
        self._code: list[Instruction] = []

    def compile(self) -> list[Instruction]:
        self._expression(self._expr)
        self._emit("ret")
        return self._code

    def _expression(self, expr):
        match expr:
            case None | bool() | int(): self._emit("const", expr)
            case Ident() as ident: self._emit("get", ident)
            case (Ident("func"), [params, body_expr]): self._func(params, body_expr)
            case (Ident("define"), [Ident() as ident, expr]):
                self._expression(expr)
                self._emit("def", ident)
            case (Ident("assign"), [Ident() as ident, expr]):
                self._expression(expr)
                self._emit("set", ident)
            case (Ident("scope"), [body_expr]): self._scope(body_expr)
            case (Ident("seq"), exprs): self._seq(exprs)
            case (Ident("if"), [cond_expr, then_expr, else_expr]):
                self._if(cond_expr, then_expr, else_expr)
            case (Ident("while"), [cond_expr, body_expr]):
                self._while(cond_expr, body_expr)
            case (op_expr, args_expr):
                self._op(op_expr, args_expr)
            case _: assert False, f"Unsupported expression @ compile(): {expr}"

    def _func(self, params, body_expr):
        body_code = Compiler(body_expr).compile()
        self._emit("make_closure", params, body_code)

    def _scope(self, body_expr):
        self._emit("enter_scope")
        self._expression(body_expr)
        self._emit("leave_scope")

    def _seq(self, exprs):
        assert len(exprs) > 0, f"Empty sequence @ compile(): {exprs}"
        for expr in exprs[:-1]:
            self._expression(expr)
            self._emit("pop")
        self._expression(exprs[-1])

    def _if(self, cond_expr, then_expr, else_expr):
        self._expression(cond_expr)
        else_jump = self._current_addr()
        self._emit("jump_if_false", None)
        self._expression(then_expr)
        end_jump = self._current_addr()
        self._emit("jump", None)
        self._set_operand(else_jump, self._current_addr())
        self._expression(else_expr)
        self._set_operand(end_jump, self._current_addr())

    def _while(self, cond_expr, body_expr):
        self._emit("const", None)
        loop_jump = self._current_addr()
        self._expression(cond_expr)
        cond_jump = self._current_addr()
        self._emit("jump_if_false", None)
        self._emit("pop")
        self._expression(body_expr)
        self._emit("jump", loop_jump)
        self._set_operand(cond_jump, self._current_addr())

    def _op(self, op_expr, args_expr):
        for arg in args_expr: self._expression(arg)
        self._expression(op_expr)
        self._emit("call", len(args_expr))

    def _set_operand(self, ip, operand):
        inst = self._code[ip]
        self._code[ip] = (inst[0], operand)

    def _emit(self, *inst):
        self._code.append(inst)

    def _current_addr(self):
        return len(self._code)


class VM:
    def __init__(self, code: list[Instruction], env: Environment) -> None:
        self._code = code
        self._env = env
        self._ip = 0
        self._stack: list[Value] = []
        self._ctrl_stack: list[tuple] = [("call", [("halt",)], 0, env)]

    def execute(self) -> Value:
        while (inst := self._code[self._ip]) != ("halt",):
            self._ip += 1
            match inst:
                case ("const", val): self._stack.append(val)
                case ("pop",): self._stack.pop()
                case ("enter_scope",):
                    self._ctrl_stack.append(("scope", self._env))
                    self._env = Environment(self._env)
                case ("leave_scope",):
                    _, self._env = self._ctrl_stack.pop()
                case ("def", ident): self._env.define(ident, self._stack[-1])
                case ("set", ident): self._env.assign(ident, self._stack[-1])
                case ("get", ident): self._stack.append(self._env.val(ident))
                case ("jump", addr): self._ip = addr
                case ("jump_if_false", addr):
                    if not self._stack.pop(): self._ip = addr
                case ("make_closure", params, body_code):
                    self._stack.append((Ident("closure"),
                            [params, body_code, self._env]))
                case ("call", nargs): self._call(nargs)
                case ("ret",): self._ret()
                case _:
                    assert False, f"Invalid instruction @ execute(): {inst}"
        assert len(self._ctrl_stack) == 0, \
            f"Invalid control stack state @ execute(): {self._ctrl_stack}"
        assert len(self._stack) == 1, \
            f"Invalid stack state @ execute(): {self._stack}"
        return self._stack.pop()

    def _call(self, nargs):
        op = self._stack.pop()
        args = list(reversed([self._stack.pop() for _ in range(nargs)]))
        match op:
            case f if callable(f): self._stack.append(f(args))
            case (Ident("closure"), [params, body_code, closure_env]):
                self._ctrl_stack.append(("call", self._code, self._ip, self._env))
                self._env = Environment(closure_env)
                self._env.bind(params, args)
                self._code = body_code
                self._ip = 0
            case _:
                assert False, f"Invalid operator @ _call(): {op}"

    def _ret(self):
        _, self._code, self._ip, self._env = self._ctrl_stack.pop()

class Interpreter:
    def __init__(self) -> None:
        self._env = Environment()
        self._builtins()

    def _builtins(self):
        self._env.define(Ident("add"), lambda args: args[0] + args[1])
        self._env.define(Ident("sub"), lambda args: args[0] - args[1])
        self._env.define(Ident("mul"), lambda args: args[0] * args[1])
        self._env.define(Ident("div"), lambda args: args[0] // args[1])
        self._env.define(Ident("mod"), lambda args: args[0] % args[1])
        self._env.define(Ident("neg"), lambda args: -args[0])

        self._env.define(Ident("equal"), lambda args: args[0] == args[1])
        self._env.define(Ident("not_equal"), lambda args: args[0] != args[1])
        self._env.define(Ident("less"), lambda args: args[0] < args[1])
        self._env.define(Ident("greater"), lambda args: args[0] > args[1])
        self._env.define(Ident("less_equal"), lambda args: args[0] <= args[1])
        self._env.define(Ident("greater_equal"), lambda args: args[0] >= args[1])

        self._env.define(Ident("not"), lambda args: not args[0])

        self._env.define(Ident("print"), lambda args: print(*args))

        self._env = Environment(self._env)

    def scan(self, src: str) -> list[Token]:
        return Scanner(src).tokenize()

    def parse(self, tokens: list[Token]) -> Expr:
        return Parser(tokens).parse()

    def ast(self, src: str) -> Expr:
        return self.parse(self.scan(src))

    def eval(self, expr: Expr) -> Value:
        try:
            return Evaluator().eval(expr, self._env)
        except ReturnException as e: return e.val
        except ContinueException: assert False, "Continue at top level @ eval()"
        except BreakException: assert False, "Break at top level @ eval()"

    def walk(self, src: str) -> Value:
        return self.eval(self.ast(src))

    def compile(self, ast: Expr) -> list[Instruction]:
        return Compiler(ast).compile()

    def code(self, src: str) -> list[Instruction]:
        return self.compile(self.ast(src))

    def execute(self, code: list[Instruction]) -> Value:
        return VM(code, self._env).execute()

    def run(self, src: str) -> Value:
        return self.execute(self.code(src))


if __name__ == "__main__":
    import sys

    toil = Interpreter()

    def print_code(code):
        for addr, inst in enumerate(code): print(f"{addr:3}: {inst}")

    def repl(walk_or_run):
        while True:
            print("\nInput source and enter Ctrl+D (Linux/Mac) or Ctrl+Z (Windows):")
            if (src := sys.stdin.read()) == "":
                exit(0)
            try:
                expr = toil.ast(src)
                print("AST:", expr, sep="\n")
                if walk_or_run == "walk":
                    print("Output:")
                    result = toil.eval(expr)
                else:
                    code = toil.code(src)
                    print("Code:")
                    print_code(code)
                    print("Output:")
                    result = toil.execute(code)
                print("Result:", result, sep="\n")
            except AssertionError as e:
                print("Error:", e, sep="\n")

    def from_file(walk_or_run, filename):
        with open(filename, "r") as f:
            if walk_or_run == "walk":
                result = toil.walk(f.read())
            else:
                result = toil.run(f.read())
        exit(result if isinstance(result, int) else 255)

    match sys.argv:
        case [_]: pass
        case [_, "--repl"]: repl("walk")
        case [_, "--rcepl"]: repl("run")
        case [_, "--walk", filename]: from_file("walk", filename)
        case [_, "--run", filename]: from_file("run", filename)
        case _: assert False, f"Invalid command line: {sys.argv}"

    # Example

    print("Break and continue:")

    print(toil.ast(r""" break """)) # -> break
    print(toil.ast(r""" continue """)) # -> continue

    print(toil.walk(r""" while True do break end """)) # -> None

    print(toil.walk(r"""
        i := 0; while i < 4 do
            print(i);
            i = i + 1
        end
    """)) # -> 0\n1\n2\n3\n4

    print(toil.walk(r"""
        i := 0; while i < 4 do
            if i == 1 then i = 2; continue end;
            print(i);
            if i == 3 then break end;
            i = i + 1
        end
    """)) # -> 0\n2\n3\nNone

    print(toil.walk(r"""
        i := 0; while i < 2 do
            j := 0; while j < 3 do
                print(i, j);
                j = j + 1
            end;
            i = i + 1
        end
    """)) # -> 0 0\n0 1\n0 2\n1 0\n1 1\n1 2\n2

    print(toil.walk(r"""
        i := 0; while i < 2 do
            j := 0; while j < 3 do
                print(i, j);
                if i == 0 and j == 1 then break end;
                j = j + 1
            end;
            i = i + 1
        end
    """)) # -> 0 0\n0 1\n1 0\n1 1\n1 2\n2

    print(toil.walk(r"""
        def check_and_quit(i) do
            if i == 2 then break end
        end;
        i := 0; while True do
            check_and_quit(i);
            print(i);
            i := i + 1
        end
    """)) # -> 0\n1\nNone

    # print(toil.walk(r""" break """)) # -> Break at top level
    # print(toil.walk(r""" continue """)) # -> Continue at top level
