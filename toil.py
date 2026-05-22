#! /usr/bin/env python3

from typing import Any

class Ident:
    __match_args__ = ("name",)

    def __init__(self, name: str) -> None: self.name = name
    def __hash__(self): return hash(self.name)
    def __repr__(self): return self.name
    def __str__(self): return self.name
    def __eq__(self, other):
        return isinstance(other, Ident) and self.name == other.name

type SyntaxElement = Ident | tuple[Ident, list[SyntaxElement]]
type SyntaxForm = list[SyntaxElement]
type SyntaxRule = tuple[Ident, SyntaxForm]
type SyntaxRules = dict[Ident, SyntaxRule]
type Source = str
type Token = Ident | int | str | bool | None
type Expr = Any
type Inst = tuple
type Code = list[Inst]
type Value = Any
type SymbolTable = dict[str, Value]


def is_ident_first(c): return c.isalpha() or c == "_"
def is_ident_rest(c): return c.isalnum() or c == "_"
def is_ident(s): return is_ident_first(s[0])
def toil_type(expr): return type(expr).__name__


class Scanner:
    def __init__(self, src: Source) -> None:
        self._src = src
        self._pos = 0
        self._tokens: list[Token] = []

    def tokenize(self) -> list[Token]:
        while True:
            while self._current_char().isspace(): self._advance()

            if self._current_char() == "#":
                while self._current_char() not in ("\n", "$EOF"):
                    self._advance()
                continue

            match self._current_char():
                case "$EOF":
                    self._tokens.append(Ident("$EOF"))
                    break
                case c if c.isnumeric(): self._number()
                case "'": self._raw_string()
                case "\"": self._string()
                case c if is_ident_first(c): self._ident()
                case "-": self._two_char_operator(">")
                case "!": self._two_char_operator("!=")
                case c if c in "=<>:": self._two_char_operator("=")
                case c if c in "+*/%()[]{}|.,;":
                    self._tokens.append(Ident(c))
                    self._advance()
                case invalid:
                    assert False, f"Invalid character @ tokenize(): {invalid}"

        return self._tokens

    def _number(self):
        start = self._pos
        while self._current_char().isnumeric(): self._advance()
        self._tokens.append(int(self._src[start:self._pos]))

    def _raw_string(self):
        self._advance()
        start = self._pos
        while (c := self._current_char()) != "'":
            assert c != "$EOF", f"Unterminated string @ _raw_string()"
            self._advance()
        self._tokens.append(self._src[start:self._pos])
        self._advance()

    def _string(self):
        self._advance()
        s = []
        while (c := self._current_char()) != '"':
            assert c != "$EOF", f"Unterminated string @ _string()"
            if c == "\\":
                self._advance()
                c = self._current_char()
                assert c != "$EOF", f"Unterminated string @ _string()"
                match c:
                    case "n": s.append("\n")
                    case _: s.append(c)
            else:
                s.append(c)
            self._advance()
        self._advance()
        self._tokens.append("".join(s))

    def _ident(self):
        start = self._pos
        self._advance()
        while is_ident_rest(self._current_char()): self._advance()
        token = self._src[start:self._pos]
        match token:
            case "None": self._tokens.append(None)
            case "True": self._tokens.append(True)
            case "False": self._tokens.append(False)
            case _: self._tokens.append(Ident(token))

    def _two_char_operator(self, successors):
        start = self._pos
        self._advance()
        if self._current_char() in successors: self._advance()
        self._tokens.append(Ident(self._src[start:self._pos]))

    def _advance(self): self._pos += 1

    def _current_char(self):
        if self._pos < len(self._src):
            return self._src[self._pos]
        else:
            return "$EOF"


class Parser:
    def __init__(self, tokens: list[Token], syntax_rules: SyntaxRules) -> None:
        self._tokens = tokens
        self._syntax_rules = syntax_rules
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
        }, self._arrow)

    def _arrow(self):
        left = self._and_or()
        if self._current_token() == Ident("->"):
            self._current_and_advance()
            body_expr = self._arrow()
            params = left if isinstance(left, list) else [left]
            return (Ident("func"), [params, body_expr])
        return left

    def _and_or(self):
        return self._binary_left({
            Ident("and"): Ident("and"), Ident("or"): Ident("or"),
        }, self._not)

    def _not(self):
        return self._unary({ Ident("not"): Ident("not") }, self._comparison)

    def _comparison(self):
        return self._binary_left({
            Ident("=="): Ident("equal"), Ident("!="): Ident("not_equal"),
            Ident("<"): Ident("less"), Ident(">"): Ident("greater"),
            Ident("<="): Ident("less_equal"), Ident(">="): Ident("greater_equal"),
            Ident("|"): Ident("|")
        }, self._add_sub)

    def _add_sub(self):
        return self._binary_left({
            Ident("+"): Ident("add"), Ident("-"): Ident("sub")
        }, self._mul_div_mod)

    def _mul_div_mod(self):
        return self._binary_left({
            Ident("*"): Ident("mul"), Ident("/"): Ident("div"), Ident("%"): Ident("mod")
        }, self._unaries)

    def _unaries(self):
        return self._unary({
            Ident("-"): Ident("neg"), Ident("+"): Ident("+"), Ident("*"): Ident("*"),
            Ident("!"): Ident("!"), Ident("!!"): Ident("!!")
        }, self._call_index_dot)

    def _call_index_dot(self):
        target = self._primary()
        while (op := self._current_token()) in (Ident("("), Ident("["), Ident(".")):
            self._current_and_advance()
            match op:
                case Ident("("):
                    target = (target, self._comma_separated_exprs(Ident(")")))
                    self._consume(Ident(")"))
                case Ident("["):
                    index = self._expression()
                    self._consume(Ident("]"))
                    target = (Ident("index"), [target, index])
                case Ident("."):
                    attr_name = self._current_and_advance()
                    assert type(attr_name) is Ident, \
                        f"Invalid attribute @ _call_index_dot(): {self._current_token()}"
                    target = (Ident("dot"), [target, str(attr_name)])
        return target

    def _primary(self):
        match self._current_token():
            case None | bool() | int() | str(): return self._current_and_advance()
            case Ident("("): return self._group()
            case Ident("["): return self._list()
            case Ident("{"): return self._dict()
            case Ident("syntax"): return self._syntax()
            case Ident() as keyword  if keyword in self._syntax_rules:
                return self._apply_syntax(self._syntax_rules[keyword])
            case Ident(name) if is_ident(name): return self._current_and_advance()
            case unexpected:
                assert False, f"Unexpected token @ _primary(): {unexpected}"

    def _group(self):
        self._current_and_advance()
        expr = self._expression()
        self._consume(Ident(")"))
        return expr

    def _list(self):
        self._current_and_advance()
        exprs = self._comma_separated_exprs(Ident("]"))
        self._consume(Ident("]"))
        return exprs

    def _dict(self):
        def _parse_key_value(dic):
            match self._current_token():
                case Ident("*"):
                    self._current_and_advance()
                    dic["*"] = self._current_and_advance()
                case Ident(key):
                    self._current_and_advance()
                    if self._current_token() == Ident(":"):
                        self._current_and_advance()
                        dic[key] = self._expression()
                    else:
                        dic[key] = Ident(key)
                case str():
                    key = self._current_and_advance()
                    self._consume(Ident(":"))
                    dic[key] = self._expression()
                case invalid:
                    assert False, f"Invalid key @ _dict(): {invalid}"

        self._current_and_advance()
        dic = {}
        if self._current_token() != Ident("}"):
            _parse_key_value(dic)
            while self._current_token() != Ident("}"):
                self._consume(Ident(","))
                _parse_key_value(dic)
        self._current_and_advance()
        return dic

    def _syntax(self):
        self._current_and_advance()
        syntax = self._comma_separated_exprs(Ident("call"))
        keyword, *form = syntax
        assert isinstance(keyword, Ident), f"Invalid keyword @ _syntax(): {keyword}"
        self._consume(Ident("call"))
        op = self._expression()
        assert isinstance(op, Ident), f"Invalid operator @ _syntax(): {op}"
        self._consume(Ident("end"))
        self._syntax_rules[keyword] = (op, form)
        return None

    def _apply_syntax(self, rule):
        def match_args(form):
            args = []
            for current, next in zip(form, form[1:] + [None]):
                match current:
                    case Ident("EXPR"):
                        args.append(self._expression())
                    case Ident("EXPRS"):
                        args.append(self._comma_separated_exprs(next))
                    case (Ident("*"), [subform]):
                        subargs = []
                        while self._current_token() == subform[0]:
                            subargs.append(match_args(subform))
                        args.append(subargs)
                    case (Ident("+"), [subform]):
                        if self._current_token() == subform[0]:
                            args.append(match_args(subform))
                        else:
                            args.append([])
                    case delimiter:
                        self._consume(delimiter)
            return args

        self._current_and_advance()
        operator, form = rule
        return (operator, match_args(form))

    def _binary_left(self, ops, sub_elem):
        left = sub_elem()
        while type(op := self._current_token()) is Ident and op in ops:
            self._current_and_advance()
            right = sub_elem()
            left = (ops[op], [left, right])
        return left

    def _binary_right(self, ops, sub_elem):
        left = sub_elem()
        if type(self._current_token()) is Ident and \
                (op := self._current_token()) in ops:
            self._current_and_advance()
            right = self._binary_right(ops, sub_elem)
            return (ops[op], [left, right])
        return left

    def _unary(self, ops, sub_elem):
        if type(self._current_token()) is Ident and \
                (op := self._current_token()) in ops:
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
    def __init__(self, parent: 'Environment | None' = None) -> None:
        self._parent = parent
        self._vars = {}

    def __repr__(self):
        content = "__builtins" if "__builtins" in self._vars else \
                  "__stdlib" if "__stdlib" in self._vars else \
                  ", ".join(self._vars)
        return f"[{content}]" + (f" < {self._parent}" if self._parent else "")

    def define(self, name: str, val: Value) -> Value:
        self._vars[name] = val
        return val

    def lookup(self, name: str) -> SymbolTable | None:
        if name in self._vars: return self._vars
        elif self._parent is not None: return self._parent.lookup(name)
        else: return None

    def val(self, name: str) -> Value:
        vars = self.lookup(name)
        assert vars is not None, f"Undefined variable @ val(): {name}"
        return vars[name]

    def assign(self, name: str, val: Value) -> Value:
        vars = self.lookup(name)
        assert vars is not None, f"Undefined variable @ assign(): {name}"
        vars[name] = val
        return val

    def bind(self, pattern, value):
        match pattern:
            case Ident(name):
                self.define(name, value)
                return True
            case list():
                return toil_type(value) == "list" and self._bind_list(pattern, value)
            case dict():
                return toil_type(value) == "dict" and self._bind_dict(pattern, value)
            case (Ident("|"), [left_pat, right_pat]):
                return self.bind(left_pat, value) or \
                       self.bind(right_pat, value)
            case (Ident("Ident"), [name_pat]):
                return toil_type(value) == "Ident" and \
                    self.bind(name_pat, value.name)
            case (Ident("tuple"), expr_pats):
                return (
                    toil_type(value) == "tuple" and len(expr_pats) == len(value) and
                    all(self.bind(p, v) for p, v in zip(expr_pats, value))
                )
            case (Ident(typ), [val_pat]):
                return toil_type(value) == typ and \
                    self.bind(val_pat, value)
            case _:
                return type(pattern) is type(value) and pattern == value

    def _bind_list(self, pattern, value):
        i = 0; lpat = len(pattern); lval = len(value)

        # Before "*"
        while i < lpat:
            sub_pat = pattern[i]
            match sub_pat:
                case (Ident("*"), [Ident(rest_name)]): break
            if i >= lval: return False
            sub_val = value[i]
            if not self.bind(sub_pat, sub_val):
                return False
            i += 1
        else:
            # No "*"
            return i == lval

        # At "*"
        lrest = lval - lpat + 1
        if lrest < 0: return False
        self.define(rest_name, value[i:i + lrest])
        i += 1

        # After "*"
        while i < lpat:
            sub_pat = pattern[i]
            match sub_pat:
                case (Ident("*"), [Ident(rest_name)]): return False
            sub_val = value[i + lrest - 1]
            if not self.bind(sub_pat, sub_val):
                return False
            i += 1

        return True

    def _bind_dict(self, pattern, value):
        tmp_pat, tmp_val = pattern.copy(), value.copy()

        rest_name = tmp_pat.get("*")
        if rest_name is not None: tmp_pat.pop("*")

        for key, sub_pattern in tmp_pat.items():
            if key not in tmp_val: return False
            if not self.bind(sub_pattern, tmp_val[key]):
                return False
            tmp_val.pop(key)

        if rest_name is not None: self.define(rest_name.name, tmp_val)
        return True


class Expander:
    def expand(self, expr: Expr, env: Environment) -> Expr:
        # print(expr)
        match expr:
            case None | bool() | int() | str() | Ident(): return expr
            case list() as exprs:
                return [self.expand(expr, env) for expr in exprs]
            case dict() as exprs:
                return {key: self.expand(val, env) for key, val in exprs.items()}
            case (Ident("quote"), [expr]):
                return self._quote(expr, env)
            case (Ident("macro"), [params, body_expr]):
                return (Ident("macro"), [params, self.expand(body_expr, env)])
            case (Ident("func"), [params, body_expr]):
                return (Ident("func"), [params, self.expand(body_expr, Environment(env))])
            case (Ident("define"), [pat, expr]):
                return self._define(pat, expr, env)
            case (Ident("assign"), [pat, expr]):
                return (Ident("assign"), [pat, self.expand(expr, env)])
            case (Ident("scope"), [body_expr]):
                return (Ident("scope"), [self.expand(body_expr, Environment(env))])
            case (Ident("match"), [val_expr, cases]):
                return self._match(val_expr, cases, env)
            case (Ident("try"), [body_expr, clauses]):
                return self._try(body_expr, clauses, env)
            case (Ident("dot"), [target_expr, attr_name]):
                return (Ident("dot"), [self.expand(target_expr, env), attr_name])
            case (op_expr, args_expr):
                return self._op(op_expr, args_expr, env)
            case unexpected:
                assert False, f"Unexpected expression @ expand(): {unexpected}"

    def _quote(self, expr, env):
        match expr:
            case list() as exprs:
                res = []
                for e in exprs:
                    match e:
                        case (Ident("!!"), [unq]) if isinstance(e, tuple):
                            res = (Ident("add"), [res, self.expand(unq, env)])
                        case _:
                            res = (Ident("add"), [res, [self._quote(e, env)]])
                return res
            case dict() as exprs:
                return {key: self._quote(val, env) for key, val in exprs.items()}
            case Ident(name):
                return (Ident("Ident"), [name])
            case (Ident("!"), [unquote_expr]):
                return self.expand(unquote_expr, env)
            case (op, args):
                return (Ident("tuple"), [self._quote(op, env), self._quote(args, env)])
            case _:
                return expr

    def _define(self, pat, expr, env):
        expanded = self.expand(expr, env)
        match expanded:
            case (Ident("macro"), [params, body_expr]):
                env.define(str(pat), (Ident("macro"), [params, body_expr]))
                return None
            case _:
                return (Ident("define"), [pat, expanded])

    def _match(self, val_expr, cases, env):
        return (Ident("match"), [
            self.expand(val_expr, env),
            [(pat, self.expand(body_expr, env)) for pat, body_expr in cases]
        ])

    def _try(self, body_expr, clauses, env):
        return (Ident("try"), [
            self.expand(body_expr, env),
            [(pat, self.expand(expr, env)) for pat, expr in clauses]
        ])

    def _op(self, op_expr, args_expr, env):
        op_expanded = self.expand(op_expr, env)

        target_node = op_expanded
        match op_expanded:
            case Ident(name):
                if (vars := env.lookup(name)) is not None:
                    target_node = vars[name]

        match target_node:
            case (Ident("macro"), [params, body_expr]):
                new_env = Environment(env)
                if new_env.bind(params, args_expr):
                    expanded_ast = Evaluator().eval(body_expr, new_env)
                    return self.expand(expanded_ast, env)
                else:
                    assert False, f"Pattern mismatch @ apply(): {params}, {args_expr}"
            case _:
                args_expanded = [self.expand(expr, env) for expr in args_expr]
                return (op_expanded, args_expanded)

class ToilException(Exception):
    def __init__(self, e: Value = None) -> None: self.e = e

class ReturnException(Exception):
    def __init__(self, val: Value = None) -> None: self.val = val

class ContinueException(Exception): pass
class BreakException(Exception): pass


class Evaluator:
    def eval(self, expr: Expr, env: Environment) -> Value:
        # print(expr)
        match expr:
            case None | bool() | int() | str():
                return expr
            case list() as exprs:
                return [self.eval(expr, env) for expr in exprs]
            case dict() as exprs:
                return {key: self.eval(val, env) for key, val in exprs.items()}
            case Ident("continue"): raise ContinueException()
            case Ident("break"): raise BreakException()
            case Ident(name): return env.val(name)
            case (Ident("quote"), [expr]): return expr
            case (Ident("func"), [params, body_expr]):
                return (Ident("closure"), [params, body_expr, env])
            case (Ident("return"), args):
                raise ReturnException(self.eval(args[0], env) if args else None)
            case (Ident("define"), [pat, expr]):
                return self._define(pat, expr, env)
            case (Ident("assign"), [pat, expr]):
                return self._assign(pat, expr, env)
            case (Ident("scope"), [body_expr]):
                return self.eval(body_expr, Environment(env))
            case (Ident("seq"), exprs):
                return self._seq(exprs, env)
            case (Ident("if"), [cond_expr, then_expr, else_expr]):
                return self._if(cond_expr, then_expr, else_expr, env)
            case (Ident("match"), [val_expr, cases]):
                return self._match(val_expr, cases, env)
            case (Ident("while"), [cond_expr, body_expr, then_expr, else_expr]):
                return self._while(cond_expr, body_expr, then_expr, else_expr, env)
            case (Ident("try"), [body_expr, clauses]):
                return self._try(body_expr, clauses, env)
            case (Ident("raise"), args):
                raise ToilException(self.eval(args[0], env) if args else None)
            case (Ident("dot"), [target_expr, attr_name]):
                return self._dot(target_expr, attr_name, env)
            case (op_expr, args_expr) if isinstance(expr, tuple):
                return self._op(op_expr, args_expr, env)
            case unexpected:
                assert False, f"Unexpected expression @ evaluate(): {unexpected}"

    def _define(self, pat, expr, env):
        val = self.eval(expr, env)
        if env.bind(pat, val):
            return val
        assert False, f"Pattern mismatch @ _define(): {pat}, {val}"

    def _assign(self, left_expr, right_expr, env):
        val = self.eval(right_expr, env)
        match left_expr:
            case Ident(name):
                return env.assign(name, val)
            case (Ident("index"), [coll_expr, index_expr]) | \
                 (Ident("dot"), [coll_expr, index_expr]):
                coll_val = self.eval(coll_expr, env)
                index_val = self.eval(index_expr, env)
                coll_val[index_val] = val
                return val
            case unexpected:
                assert False, f"Invalid assign target @ _assign(): {unexpected}"

    def _seq(self, exprs, env):
        val = None
        for expr in exprs:
            val = self.eval(expr, env)
        return val

    def _if(self, cond_expr, then_expr, else_expr, env):
        if self.eval(cond_expr, env):
            return self.eval(then_expr, env)
        else:
            return self.eval(else_expr, env)

    def _match(self, val_expr, cases, env):
        val = self.eval(val_expr, env)
        for pattern, body_expr in cases:
            if env.bind(pattern, val):
                return self.eval(body_expr, env)
        return None

    def _while(self, cond_expr, body_expr, then_expr, else_expr, env):
        while self.eval(cond_expr, env):
            try:
                self.eval(body_expr, env)
            except ContinueException: continue
            except BreakException:
                return self._eval_optional_arg(else_expr, env)
        return self._eval_optional_arg(then_expr, env)

    def _eval_optional_arg(self, args, env):
        return None if len(args) == 0 else self.eval(args[0], env)

    def _try(self, body_expr, clauses, env):
        try:
            return self.eval(body_expr, env)
        except ToilException as e:
            for exc_pat, exc_expr in clauses:
                if env.bind(exc_pat, e.e):
                    return self.eval(exc_expr, env)
            raise e

    def _dot(self, target_expr, attr_name, env):
        target_val = self.eval(target_expr, env)
        match target_val:
            case dict() if attr_name in target_val:
                func_val = target_val[attr_name]
                match func_val:
                    case (Ident("closure"), [[Ident("self"), *_], _, _]):
                        return lambda args: self.apply(func_val, [target_val] + args)
                return func_val

        func_val = env.val(attr_name)
        return lambda args: self.apply(func_val, [target_val] + args)

    def _op(self, op_expr, args_expr, env):
        op_val = self.eval(op_expr, env)
        args_val = [self.eval(arg, env) for arg in args_expr]
        return self.apply(op_val, args_val)

    def apply(self, op_val: Value, args_val: list[Value]) -> Value:
        match op_val:
            case c if callable(c):
                return c(args_val)
            case (Ident("closure"), [params, body_expr, closure_env]):
                new_env = Environment(closure_env)
                if new_env.bind(params, args_val):
                    try:
                        return self.eval(body_expr, new_env)
                    except ReturnException as e: return e.val
                assert False, f"Pattern mismatch @ apply(): {params}, {args_val}"
            case _:
                assert False, f"Invalid operator @ apply(): {op_val}"


class Compiler:
    def __init__(self):
        self._code = []
        self._control_stack = []

    def compile(self,expr: Expr) -> Code:
        self._code = []
        self._expression(expr)
        self._code.append(("halt",))
        assert self._control_stack == [], \
            f"Invalid control stack state @ compile(): {self._control_stack}"
        return self._code

    def _expression(self, expr):
        match expr:
            case None | bool() | int() | str():
                self._code.append(("const", expr))
            case list() as lst:
                self._list(lst)
            case dict() as dic:
                self._dict(dic)
            case Ident("continue"): self._continue()
            case Ident("break"): self._break()
            case Ident(name): self._code.append(("get", name))
            case (Ident("define"), [pat, expr]):
                self._expression(expr)
                self._code.append(("def", pat))
            case (Ident("assign"), [left_expr, right_expr]):
                self._assign(left_expr, right_expr)
            case (Ident("scope"), [body_expr]):
                self._scope(body_expr)
            case (Ident('seq'), exprs): self._seq(exprs)
            case (Ident('if'), [cond_expr, then_expr, else_expr]):
                self._if(cond_expr, then_expr, else_expr)
            case (Ident("while"), [cond_expr, body_expr, then_expr, else_expr]):
                self._while(cond_expr, body_expr, then_expr, else_expr)
            case (Ident("dot"), [target_expr, attr_name]):
                self._dot(target_expr, attr_name)
            case (Ident(op), [*args]):
                self._op(Ident(op), args)
            case _:
                assert False, f"Unsupported expression @ compile(): {expr}"

    def _list(self, lst):
        for elem in lst: self._expression(elem)
        self._code.append(("get", "list"))
        self._code.append(("call", len(lst)))

    def _dict(self, dic):
        for key, val in dic.items(): self._list([key, val])
        self._code.append(("get", "dict"))
        self._code.append(("call", len(dic)))

    def _assign(self, left_expr, right_expr):
        match left_expr:
            case Ident(name):
                self._expression(right_expr)
                self._code.append(("set", name))
            case (Ident("index"), [coll_expr, index_expr]):
                self._expression(coll_expr)
                self._expression(index_expr)
                self._expression(right_expr)
                self._code.append(("set_index",))
            case (Ident("dot"), [coll_expr, attr_name]):
                self._expression(coll_expr)
                self._code.append(("const", attr_name))
                self._expression(right_expr)
                self._code.append(("set_index",))
            case unexpected:
                assert False, f"Invalid assign target @ compile(): {unexpected}"

    def _scope(self, body_expr):
        self._control_stack.append(("scope",))
        self._code.append(("push_env",))
        self._expression(body_expr)
        self._code.append(("pop_env",))
        self._control_stack.pop()

    def _seq(self, exprs):
        assert len(exprs) > 0, f"Empty sequence @ compile(): {exprs}"
        for expr in exprs[:-1]:
            self._expression(expr)
            self._code.append(("pop",))
        self._expression(exprs[-1])

    def _if(self, cond_expr, then_expr, else_expr):
        self._expression(cond_expr)
        else_jump = self._current_addr()
        self._code.append(("jump_if_false", None))
        self._expression(then_expr)
        end_jump = self._current_addr()
        self._code.append(("jump", None))
        self._set_operand(else_jump, self._current_addr())
        self._expression(else_expr)
        self._set_operand(end_jump, self._current_addr())

    def _while(self, cond_expr, body_expr, then_expr, else_expr):
        loop_jump = self._current_addr()
        break_addrs = []
        self._control_stack.append(("while", loop_jump, break_addrs))
        self._expression(cond_expr)
        cond_jump = self._current_addr()
        self._code.append(("jump_if_false", None))
        self._expression(body_expr)
        self._code.append(("pop",))
        self._code.append(("jump", loop_jump))
        self._set_operand(cond_jump, self._current_addr())

        self._control_stack.pop()
        self._expression(then_expr[0] if then_expr else None)
        then_jump = self._current_addr()
        self._code.append(("jump", None))
        for break_addr in break_addrs:
            self._set_operand(break_addr, self._current_addr())
        self._expression(else_expr[0] if else_expr else None)
        self._set_operand(then_jump, self._current_addr())

    def _continue(self):
        for ctrl in reversed(self._control_stack):
            match ctrl:
                case ("scope",):
                    self._code.append(("pop_env",))
                case ("while", loop_jump, _):
                    self._code.append(("jump", loop_jump))
                    return
        assert False, "Continue outside of loop @ _continue()"

    def _break(self):
        for ctrl in reversed(self._control_stack):
            match ctrl:
                case ("scope",):
                    self._code.append(("pop_env",))
                case ("while", _, break_addrs):
                    break_addrs.append(self._current_addr())
                    self._code.append(("jump", None))
                    return
        assert False, "Break outside of loop @ _break()"

    def _dot(self, target_expr, attr_name):
        self._expression(target_expr)
        self._code.append(("dot", attr_name))

    def _op(self, op, args):
        for arg in args: self._expression(arg)
        self._expression(op)
        self._code.append(("call", len(args)))

    def _set_operand(self, ip, operand):
        inst = self._code[ip]
        self._code[ip] = (inst[0], operand)

    def _current_addr(self):
        return len(self._code)

class VM:
    def __init__(self, env: Environment):
        self._code = []
        self._ip = 0
        self._stack = []
        self._ctrl_stack = []
        self._env = env

    def load(self, code: Code) -> None:
        self._code = code
        self._ip = 0

    def execute(self) -> Value:
        while True:
            inst = self._code[self._ip]; self._ip += 1
            match inst:
                case ("halt",): break
                case ("const", val): self._stack.append(val)
                case ("pop",): self._stack.pop()
                case ("def", pat): self._def(pat)
                case ("set", name): self._set(name)
                case ("set_index",): self._set_index()
                case ("get", name): self._stack.append(self._env.val(name))
                case ("push_env",):
                    self._ctrl_stack.append(self._env)
                    self._env = Environment(self._env)
                case ("pop_env",): self._env = self._ctrl_stack.pop()
                case ("jump", addr): self._ip = addr
                case ("jump_if_false", addr):
                    if not self._stack.pop(): self._ip = addr
                case ("dot", attr_name): self._dot(attr_name)
                case ("call", nargs): self._call(nargs)
                case _:
                    assert False, f"Invalid instruction @ execute(): {inst}"
        assert len(self._ctrl_stack) == 0, f"Invalid control stack state @ execute(): {self._ctrl_stack}"
        assert len(self._stack) == 1, f"Invalid stack state @ execute(): {self._stack}"
        return self._stack.pop()

    def _def(self, pat):
        val = self._stack[-1]
        assert self._env.bind(pat, val), f"Pattern mismatch @ _def(): {pat}, {val}"

    def _set(self, name):
        val = self._stack[-1]
        self._env.assign(name, val)

    def _set_index(self):
        val = self._stack.pop()
        index_val = self._stack.pop()
        coll_val = self._stack.pop()
        coll_val[index_val] = val
        self._stack.append(val)

    def _dot(self, attr_name):
        target_val = self._stack.pop()
        self._stack.append(target_val[attr_name])

    def _call(self, nargs):
        op = self._stack.pop()
        args = list(reversed([self._stack.pop() for _ in range(nargs)]))
        match op:
            case f if callable(f): self._stack.append(f(args))
            case unexpected:
                assert False, f"Invalid call @ _call(): {unexpected}"

class Interpreter:
    def __init__(self) -> None:
        self._syntax_rules = {}
        self._env = Environment()

    def init_env(self) -> 'Interpreter':
        self._gensym_counter = 0
        self._env = Environment()
        self._builtins()
        self._corelib()
        return self

    def _builtins(self):
        self._env.define("__builtins", None)

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

        self._env.define("list", lambda args: args)
        self._env.define("tuple", lambda args: tuple(args))
        self._env.define("dict", lambda args: dict(args))
        self._env.define("Ident", lambda args: Ident(args[0]))

        self._env.define("len", lambda args: len(args[0]))
        self._env.define("index", lambda args: args[0][args[1]])
        self._env.define("slice", lambda args: args[0][args[1]:args[2]])
        self._env.define("push", lambda args: args[0].append(args[1]))
        self._env.define("pop", lambda args: args[0].pop() if len(args) == 1 else args[0].pop(args[1]))
        self._env.define("in", lambda args: args[0] in args[1])
        self._env.define("copy", lambda args: args[0].copy())

        self._env.define("join", lambda args: str(args[1]).join(map(str, args[0])))
        self._env.define("format", lambda args: args[0].format(*args[1:]))

        self._env.define("keys", lambda args: list(args[0].keys()))
        self._env.define("items", lambda args: [list(e) for e in args[0].items()])

        self._env.define("type", lambda args: toil_type(args[0]))
        self._env.define("to_bool", lambda args: bool(args[0]))
        self._env.define("to_int", lambda args: int(args[0]))
        self._env.define("to_str", lambda args: str(args[0]))
        self._env.define("to_list", lambda args: list(args[0]))
        self._env.define("to_dict", lambda args: dict(args[0]))
        self._env.define("to_tuple", lambda args: tuple(args[0]))

        self._env.define("print", lambda args: print(*args))

        self._env.define("read", lambda args: open(args[0], "r").read())
        self._env.define("load", lambda args: self._load(args[0]))

        self._env.define("eval", lambda args: Evaluator().eval(self.ast(args[0]), self._env))
        self._env.define("eval_expr", lambda args: Evaluator().eval(args[0], self._env))
        self._env.define("apply", lambda args: Evaluator().apply(args[0], args[1]))

        self._env.define("gensym", lambda args: self._gensym(args))

        self._env = Environment(self._env)

    def _corelib(self):
        self.walk(r""" __corelib := None """)

        self.walk(r"""
            syntax quote, EXPR, end call quote end;
            syntax func, EXPRS, do, EXPR, end call func end;
            syntax macro, EXPRS, do, EXPR, end call macro end;
            syntax scope, EXPR, end call scope end;
            syntax match, EXPR, *[case, EXPR, then, EXPR], end call match end;
            syntax while, EXPR, do, EXPR, +[then, EXPR], +[else, EXPR], end call while end;
            syntax try, EXPR, *[except, EXPR, then, EXPR], end call try end
        """)

        self.walk(r"""
            defmacro_ := macro call_expr, body do
                match call_expr
                    case tuple(name, args) then
                        quote !name := macro !!args do !body end end
                    case Ident(name) then
                        quote !call_expr := macro do !body end end
                    case _ then
                        raise('Invalid defmacro syntax @ defmacro() : {}'.format(call_expr))
                end
            end;

            syntax defmacro, EXPR, do, EXPR, end call defmacro_ end
        """)

        self.walk(r"""
            defmacro def_(call_expr, body) do
                match call_expr
                    case tuple(name, args) then
                        quote !name := func !!args do !body end end
                    case Ident(name) then
                        quote !call_expr := func do !body end end
                    case _ then
                        raise('Invalid def syntax @ def() : {}'.format(call_expr))
                end
            end;

            syntax def, EXPR, do, EXPR, end call def_ end
        """)

        self.walk(r"""
            defmacro if_(cnd, thn, elifs, els) do
                expr := if(els == [], None, els[0]);
                i := len(elifs) - 1;
                while i >= 0 do
                    [elif_cnd, elif_thn] := elifs[i];
                    expr = quote if(!elif_cnd, !elif_thn, !expr) end;
                    i = i - 1
                end;
                quote if(!cnd, !thn, !expr) end
            end;

            syntax if, EXPR, then, EXPR, *[elif, EXPR, then, EXPR], +[else, EXPR], end call if_ end
        """)

        self.walk(r"""
            defmacro and(a, b) do
                g := gensym("it"); quote if !g := !a then !b else !g end end
            end;
            defmacro or(a, b) do
                g := gensym("it"); quote if !g := !a then !g else !b end end
            end
        """)

        self.walk(r"""
            defmacro for_(var, coll, body, thn, els) do
                thn = if thn == [] then None else thn[0] end;
                els = if els == [] then None else els[0] end;
                _coll := gensym("coll");
                _index := gensym("index");
                quote
                    !_coll := !coll; !_index := -1;
                    while !_index + 1 < len(!_coll) do
                        !_index = !_index + 1;
                        !var := (!_coll)[!_index];
                        !body
                    then !thn else !els end
                end
            end;

            syntax for, EXPR, in, EXPR, do, EXPR, +[then, EXPR], +[else, EXPR], end call for_ end
        """)

        self.walk(r"""
            defmacro assert_(cond_expr, exc_expr) do
                quote if not !cond_expr then raise(!exc_expr) end end
            end;

            syntax assert, EXPR, else, EXPR, end call assert_ end
        """)

        self.walk(r"""
            defmacro defclass_(call_expr, super, body) do
                init := if super == [] then {} else super[0] end;
                match call_expr
                    case tuple(name, args) then
                        quote def (!name)(!!args) do self := !init; !body; self end end
                    case Ident(name) then
                        quote def (!call_expr)() do self := !init; !body; self end end
                    case _ then
                        raise("Invalid defclass syntax @ defclass() : {}".format(call_expr))
                end
            end;

            syntax defclass, EXPR, +[inherits, EXPR], do, EXPR, end call defclass_ end;

            defmacro defmethod_(call_expr, body) do
                match call_expr
                    case tuple(name, args) then
                        quote self[!to_str(name)] = func self, !!args do !body end end
                    case Ident(name) then
                        quote self[!to_str(name)] = func self do !body end end
                    case _ then
                        raise("Invalid defmethod syntax @ defmethod(): {}".format(call_expr))
                end
            end;

            syntax defmethod, EXPR, do, EXPR, end call defmethod_ end
        """)

        self._env = Environment(self._env)

    def stdlib(self) -> 'Interpreter':
        self.walk("""
            __stdlib := None;

            def first(a) do a[0] end;
            def rest(a) do slice(a, 1, None) end;
            def last(a) do a[-1] end;

            def range(start, stop, step) do
                b := [];
                i := start; while i < stop do push(b, i); i = i + step then b end
            end;

            def map(a, f) do
                b := [];
                for x in a do push(b, f(x)) then b end
            end;

            def filter(a, f) do
                b := [];
                for x in a do if f(x) then push(b, x) end then b end
            end;

            def zip(a, b) do
                z := []; la := len(a); lb := len(b);
                i := 0; while i < la and i < lb do
                    push(z, [a[i], b[i]]); i = i + 1
                then z end
            end;

            def reverse(a) do
                b := []; l := len(a);
                for i in range(1, l + 1, 1) do push(b, a[l - i]) then b end
            end;

            def enumerate(a) do
                zip(range(0, len(a), 1), a)
            end;

            def all(a, f) do
                for x in a do if not f(x) then return(False) end then True end
            end;

            def any(a, f) do
                for x in a do if f(x) then return(True) end then False end
            end
        """)

        self._env = Environment(self._env)
        return self

    def _gensym(self, args):
        self._gensym_counter += 1
        name = args[0] if args else "gensym"
        return Ident(f"__{name}_{self._gensym_counter}")

    def _load(self, path):
        with open(path, "r") as f: src = f.read()
        return Evaluator().eval(self.ast(src), Environment(self._env))

    def scan(self, src: Source) -> list[Token]:
        return Scanner(src).tokenize()

    def parse(self, tokens: list[Token]) -> Expr:
        return Parser(tokens, self._syntax_rules).parse()

    def expand(self, ast: Expr) -> Expr:
        return Expander().expand(ast, self._env)

    def ast(self, src: Source) -> Expr:
        return self.expand(self.parse(self.scan(src)))

    def eval(self, ast: Expr) -> Value:
        try:
            return Evaluator().eval(ast, self._env)
        except ToilException as e: assert False, f"ToilException @ evaluate(): {e.e}"
        except ReturnException as e:
            assert False, f"Return from top level @ evaluate(): {e.val}"
        except ContinueException: assert False, "Continue at top level @ evaluate()"
        except BreakException: assert False, f"Break at top level @ evaluate()"

    def walk(self, src: Source) -> Value:
        return self.eval(self.ast(src))

    def compile(self, ast: Expr) -> Code:
        return Compiler().compile(ast)

    def code(self, src: Source) -> Code:
        return self.compile(self.ast(src))

    def execute(self, code: Code) -> Value:
        vm = VM(self._env)
        vm.load(code)
        return vm.execute()

    def run(self, src: Source) -> Value:
        return self.execute(self.code(src))

if __name__ == "__main__":
    import sys

    toil = Interpreter().init_env().stdlib()

    def repl(walk_or_run):
        while True:
            print("\nInput source and enter Ctrl+D:")
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
                    print("Code:", code, "Output:", sep="\n")
                    result = toil.execute(code)
                print("Result:", result, sep="\n")
            except AssertionError as e:
                print("Error:", e, sep="\n")

    def go_file(walk_or_run, filename):
        with open(filename, "r") as f:
            if walk_or_run == "walk":
                result = toil.walk(f.read())
            else:
                result = toil.run(f.read())
        exit(result if isinstance(result, int) else 0)

    if len(sys.argv) > 1:
        match sys.argv[1]:
            case "--repl": repl("walk")
            case "--rcepl": repl("run")
            case "--walk": go_file("walk", sys.argv[2])
            case "--run": go_file("run", sys.argv[2])

    def print_code(code):
        print()
        for addr, inst in enumerate(code):
            print(f"{addr:3}: {list(inst)}")

    # Example

    # If
    print_code(toil.code(r""" if 2 == 2 then 4 + 5 else 6 + 7  end """))
    print(toil.run(r""" if 2 == 2 then 4 + 5 else 6 + 7  end """)) # -> 9
    print(toil.run(r""" if 2 == 3 then 4 + 5 else 6 + 7  end """)) # -> 13
    print(toil.run(r""" if False then 2 elif False then 3 else 4 end """)) # -> 4

    # Variable
    print_code(toil.code(r""" a := 2 + 3 """))
    print_code(toil.code(r""" a = 2 + 3 """))
    print(toil.run(r""" a := 2 + 3 """)) # -> 5
    print(toil.run(r""" a """)) # -> 5
    print(toil.run(r""" a = 4 + 5 """)) # -> 9
    print(toil.run(r""" a """)) # -> 9
    # print(toil.run(r""" b """)) # -> Undefined variable

    # Destructuring
    print_code(toil.code(r""" [a, b] := [2, 3] """))
    print(toil.run(r""" [a, b] := [2, 3]; [a, b] """))

    print(toil.run(r""" [a, *b] := [2, 3, 4]; [a, b] """))
    print(toil.run(r""" {a, b} := {a: 2, b: {c: 3, d: 4}}; [a, b] """))

    # Scope
    print_code(toil.code(r""" a := 2; scope a end """))
    print(toil.run(r""" a := 2; scope a end """)) # ->  2
    print(toil.run(r""" a := 2; scope scope a end end """)) # -> 2

    print(toil.run(r""" a := 2; scope a := 3 end """)) # -> 3
    print(toil.run(r""" a """)) # -> 2

    print(toil.run(r""" a := 2; scope a = 3 end """)) # -> 3
    print(toil.run(r""" a """)) # -> 3

    print(toil.run(r""" a := 2; scope d := 3 end """)) # -> 3
    # toil.run(r""" d """) # -> Undefined variable

    # While
    print_code(toil.code(r""" while i < 3 do i = i + 1 then i + 1 end """))
    print(toil.run(r""" i := 0; while i < 3 do i = i + 1 then i + 1 end """)) # -> 4
    print_code(toil.code(r""" while i < 3 do print(i); i = i + 1 end """))
    print(toil.run(r""" i := 0; while i < 3 do print(i); i = i + 1 end """)) # -> 0\n1\n2\nNone

    # Continue
    print_code(toil.code(r""" while i < 3 do i = i + 1; if i == 2 then continue end end """))
    toil.run(r""" i := 0; while i < 3 do i = i + 1; if i == 2 then continue end; print(i) end """) # -> 1\n3\n

    toil.run(r"""
        i := 0; while i < 2 do
            j := 0; while j < 3 do
                j = j + 1; if j == 2 then continue end;
                print(i, j)
            end;
            i = i + 1
        end
    """) # -> 0 1\n0 3\n1 1\n1 3

    toil.run(r"""
        i := 0; while i < 3 do
            i = i + 1;
            scope
                if i == 2 then continue end;
                print(i)
            end
        end
    """) # -> 1\n3

    # toil.run(r""" continue """) # -> Continue outside of loop

    # Break
    print_code(toil.code(r""" while i < 3 do if i == 1 then break end; i = i + 1 end """))
    print(toil.run(r""" i := 0; while i < 3 do if i == 1 then break end; print(i); i = i + 1 end """)) # -> 0\nNone

    print_code(toil.code(r""" while i < 3 do if i == 1 then break end; i = i + 1 then i * 2 else i * 3 end """))
    print(toil.run(r""" i := 0; while i < 3 do if i == 1 then break end; print(i); i = i + 1 then i * 2 else i * 3 end """)) # -> 0\n3

    toil.run(r"""
        i := 0; while i < 2 do
            j := 0; while j < 3 do
                if i == 0 and j == 1 then break end;
                print(i, j);
                j = j + 1
            end;
            i = i + 1
        end
    """) # ->  0 0\n1 0\n1 1\n1 2

    toil.run(r"""
        i := 0; while i < 2 do
            j := 0; while j < 3 do
                if i == 1 and j == 1 then break end;
                print(i, j);
                j = j + 1
            else break end;
            i = i + 1
        end
    """) # -> 0 0\n0 1\n0 2\n1 0

    toil.run(r"""
        i := 0; while i < 3 do
            scope
                if i == 1 then break end;
                print(i)
            end;
            i = i + 1
        end
    """) # -> 0

    # toil.run(r""" break """) # -> Break outside of loop

    # Built-in functions
    print_code(toil.code(r""" add(mul(2, 3), 4) """))
    print(toil.run(r""" add(mul(2, 3), 4) """)) # -> 10

    print(toil.run(r""" tuple() """)) # -> ()
    print(toil.run(r""" tuple(2, 3, 4) """)) # -> (2, 3, 4)

    toil.run(r""" print() """) # -> (newline)
    toil.run(r""" print(2, 3, 4) """) # -> 2 3 4

    print(toil.run(r""" myadd := add; myadd(2, 3) """)) # -> 5

    # List
    print_code(toil.code(r""" [] """))
    print(toil.run(r""" [] """)) # -> []

    print_code(toil.code(r""" [2, [3, 4]] """))
    print(toil.run(r""" [2, [3, 4]] """)) # -> [2, [3, 4]]

    print_code(toil.code(r""" [2, [3, 4]][1] """))
    print(toil.run(r""" [2, [3, 4]][1] """)) # -> [3, 4]
    print(toil.run(r""" [2, [3, 4]][1][0] """)) # -> 3

    # Assign list element
    toil.run(r""" a := [2, [3, 4]] """)
    print_code(toil.code(r""" a[0] = 5 """))
    print(toil.run(r""" a[0] = 5; a """)) # -> [5, [3, 4]]
    print(toil.run(r""" a[1][0] = 6; a """)) # -> [5, [6, 4]]
    print(toil.run(r""" a[-1][1] = 7; a """)) # -> [5, [6, 7]]
    print(toil.run(r""" l1 := [2, 3]; l2 := [4, 5]; l1[0] = l2[1] = 6; [l1, l2] """)) # -> [[6, 3], [4, 6]]

    # Dict
    print_code(toil.code(r""" {} """))
    print(toil.run(r""" {} """)) # -> {}

    print_code(toil.code(r""" {a: 2, b: {c: 3, d: 4}} """))
    print(toil.run(r""" {a: 2, b: {c: 3, d: 4}} """)) # -> {'a': 2, 'b': {'c': 3, 'd': 4}}

    print_code(toil.code(r""" {a: 2, b: {c: 3, d: 4}}["b"] """))
    print(toil.run(r""" {a: 2, b: {c: 3, d: 4}}["b"] """)) # -> {'c': 3, 'd': 4}
    print(toil.run(r""" {a: 2, b: {c: 3, d: 4}}["b"]["c"] """)) # -> 3

    print_code(toil.code(r""" {a: 2, b: {c: 3, d: 4}}.b """))
    print(toil.run(r""" {a: 2, b: {c: 3, d: 4}}.b """)) # -> {'c': 3, 'd': 4}
    print(toil.run(r""" {a: 2, b: {c: 3, d: 4}}.b.c """)) # -> 3

    # Assign dict element
    toil.run(r""" d := {a: 2, b: {c: 3, d: 4}} """)
    print_code(toil.code(r""" d["a"] = 5 """))
    print(toil.run(r""" d["a"] = 5; d """)) # -> {'a': 5, 'b': {'c': 3, 'd': 4}}
    print(toil.run(r""" d["b"]["c"] = 6; d """)) # -> {'a': 5, 'b': {'c': 6, 'd': 4}}

    print(toil.run(r""" d.b.c = 7; d """)) # -> {'a': 5, 'b': {'c': 7, 'd': 4}}
    print(toil.run(r""" d1 := {a: 2}; d2 := {b: 3}; d1.a = d2["b"] = 4; [d1, d2] """)) # -> [{'a': 4}, {'b': 4}]
