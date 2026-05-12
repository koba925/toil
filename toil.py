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

Source = str
Token = Ident | int | str | bool | None
Expr = Any
Value = Any
SymbolTable = dict[str, Value]


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
                case c if c in "=!<>:": self._two_char_operator("=")
                case c if c in "+*/%()[]{}.,;":
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
            Ident("<="): Ident("less_equal"), Ident(">="): Ident("greater_equal")
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
            Ident("-"): Ident("neg"), Ident("+"): Ident("+"), Ident("*"): Ident("*")
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
            case Ident("func"): return self._func()
            case Ident("def"): return self._def()
            case Ident("macro"): return self._macro()
            case Ident("scope"): return self._scope()
            case Ident("if"): return self._if()
            case Ident("match"): return self._match()
            case Ident("while"): return self._while()
            case Ident("for"): return self._for()
            case Ident("try"): return self._try()
            case Ident("assert"): return self._assert()
            case Ident("defclass"): return self._defclass()
            case Ident("defmethod"): return self._defmethod()
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

    def _func(self):
        self._current_and_advance()
        params = self._comma_separated_exprs(Ident("do"))
        self._consume(Ident("do"))
        body_expr = self._expression()
        self._consume(Ident("end"))
        return (Ident("func"), [params, body_expr])

    def _macro(self):
        self._current_and_advance()
        params = self._comma_separated_exprs(Ident("do"))
        self._consume(Ident("do"))
        body_expr = self._expression()
        self._consume(Ident("end"))
        return (Ident("macro"), [params, body_expr])

    def _def(self):
        self._current_and_advance()
        call_expr = self._expression()
        self._consume(Ident("do"))
        body_expr = self._expression()
        self._consume(Ident("end"))
        match call_expr:
            case (name, params) if isinstance(call_expr, tuple):
                return (Ident("define"), [name, (Ident("func"), [params, body_expr])])
            case Ident(name):
                return (Ident("define"), [call_expr, (Ident("func"), [[], body_expr])])
            case _:
                assert False, "Invalid def syntax @ _def(): " + str(call_expr)

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

    def _match(self):
        self._current_and_advance()
        val_expr = self._expression()
        cases = []
        while self._current_token() == Ident("case"):
            self._current_and_advance()
            pattern = self._expression()
            self._consume(Ident("then"))
            body_expr = self._expression()
            cases.append((pattern, body_expr))
        self._consume(Ident("end"))
        return (Ident("match"), [val_expr, cases])

    def _while(self):
        self._current_and_advance()
        cond_expr = self._expression()
        self._consume(Ident("do"))
        body_expr = self._expression()
        if self._current_token() == Ident("then"):
            self._current_and_advance()
            then_expr = [self._expression()]
        else:
            then_expr = []
        if self._current_token() == Ident("else"):
            self._current_and_advance()
            else_expr = [self._expression()]
        else:
            else_expr = []
        self._consume(Ident("end"))
        return (Ident("while"), [cond_expr, body_expr, then_expr, else_expr])

    def _for(self):
        self._current_and_advance()
        var_pat = self._expression()
        self._consume(Ident("in"))
        coll_expr = self._expression()
        self._consume(Ident("do"))
        body_expr = self._expression();
        if self._current_token() == Ident("then"):
            self._current_and_advance()
            then_expr = [self._expression()]
        else:
            then_expr = []
        if self._current_token() == Ident("else"):
            self._current_and_advance()
            else_expr = [self._expression()]
        else:
            else_expr = []
        self._consume(Ident("end"));
        return (Ident("for"), [var_pat, coll_expr, body_expr, then_expr, else_expr])

    def _try(self):
        self._current_and_advance()
        body_expr = self._expression()
        clauses = []
        while self._current_token() == Ident("except"):
            self._current_and_advance()
            exc_pat = self._expression()
            self._consume(Ident("then"))
            exc_expr = self._expression()
            clauses.append((exc_pat, exc_expr))
        self._consume(Ident("end"))
        return (Ident("try"), [body_expr, clauses])

    def _assert(self):
        self._current_and_advance()
        cond_expr = self._expression()
        self._consume(Ident("else"))
        exc_expr = self._expression()
        self._consume(Ident("end"))
        return (Ident("if"), [
            (Ident("not"), [cond_expr]),
            (Ident("raise"), [exc_expr]),
            None
        ])

    def _defclass(self):
        self._current_and_advance()
        call_expr = self._expression()
        self._consume(Ident("do"))
        body_expr = self._expression()
        self._consume(Ident("end"))

        match call_expr:
            case (name, args):
                return (Ident("define"), [name,
                    (Ident("func"), [args,
                        (Ident("seq"), [
                            (Ident("define"), [Ident("self"), {}]),
                            body_expr,
                            Ident("self")
                        ])
                    ])
                ])
            case Ident(name):
                return (Ident("define"), [call_expr,
                    (Ident("func"), [[],
                        (Ident("seq"), [
                            (Ident("define"), [Ident("self"), {}]),
                            body_expr,
                            Ident("self")
                        ])
                    ])
                ])
            case _:
                assert False, f"Invalid defclass syntax @ _defclass(): {call_expr}"

    def _defmethod(self):
        self._current_and_advance()
        call_expr = self._expression()
        self._consume(Ident("do"))
        body_expr = self._expression()
        self._consume(Ident("end"))

        match call_expr:
            case(name, args):
                return (Ident('assign'), [
                    (Ident('dot'), [Ident('self'), str(name)]),
                    (Ident('func'), [[Ident('self')] + args, body_expr])
                ])
            case Ident(name):
                return (Ident('assign'), [
                    (Ident('dot'), [Ident('self'), str(name)]),
                    (Ident('func'), [[Ident('self')], body_expr])
                ])
            case _:
                assert False, f"Invalid defmethod syntax @ _defmethod(): {call_expr}"

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
            case (Ident("or"), [left_pat, right_pat]):
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
            case (Ident("func"), [params, body_expr]):
                return (Ident("func"), [params, self.expand(body_expr, Environment(env))])
            case (Ident("macro"), [params, body_expr]):
                return (Ident("macro"), [params, self.expand(body_expr, env)])
            case (Ident("define"), [pat, expr]):
                expanded = self.expand(expr, env)
                match expanded:
                    case (Ident("macro"), [params, body_expr]):
                        env.define(str(pat), (Ident("macro"), [params, body_expr]))
                        return None
                    case _:
                        return (Ident("define"), [pat, expanded])
            case (Ident("assign"), [pat, expr]):
                return (Ident("assign"), [pat, self.expand(expr, env)])
            case (Ident("scope"), [body_expr]):
                return (Ident("scope"), [self.expand(body_expr, Environment(env))])
            case (Ident("match"), [val_expr, cases]):
                return (Ident("match"), [
                    self.expand(val_expr, env),
                    [(pat, self.expand(body_expr, env)) for pat, body_expr in cases]
                ])
            case (Ident("for"), [var_pat, coll_expr, body_expr, then_expr, else_expr]):
                return (Ident("for"), [
                    var_pat,
                    self.expand(coll_expr, env),
                    self.expand(body_expr, env),
                    self.expand(then_expr, env),
                    self.expand(else_expr, env)
                ])
            case (Ident("try"), [body_expr, clauses]):
                return (Ident("try"), [
                    self.expand(body_expr, env),
                    [(pat, self.expand(expr, env)) for pat, expr in clauses]
                ])
            case (Ident("dot"), [target_expr, attr_name]):
                return (Ident("dot"), [self.expand(target_expr, env), attr_name])
            case (op_expr, args_expr):
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
            case unexpected:
                assert False, f"Unexpected expression @ expand(): {unexpected}"


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
            case (Ident("and"), [left_expr, right_expr]):
                return self.eval(left_expr, env) and self.eval(right_expr, env)
            case (Ident("or"), [left_expr, right_expr]):
                return self.eval(left_expr, env) or self.eval(right_expr, env)
            case (Ident("while"), [cond_expr, body_expr, then_expr, else_expr]):
                return self._while(cond_expr, body_expr, then_expr, else_expr, env)
            case (Ident("for"), [var_pat, coll_expr, body_expr, then_expr, else_expr]):
                return self._for(var_pat, coll_expr, body_expr, then_expr, else_expr, env)
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

    def _for(self, var_pat, coll_expr, body_expr, then_expr, else_expr, env):
        coll_val = self.eval(coll_expr, env)
        for val in coll_val:
            assert env.bind(var_pat, val), \
                "Pattern mismatch @ _for(): " + str(var_pat) + ", " + str(val)
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


class Interpreter:
    def __init__(self) -> None:
        self._env = Environment()

    def init_env(self) -> 'Interpreter':
        self._env = Environment()
        self._builtins()
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
        self._env.define("bool", lambda args: bool(args[0]))
        self._env.define("int", lambda args: int(args[0]))
        self._env.define("str", lambda args: str(args[0]))
        self._env.define("list", lambda args: list(args[0]))
        self._env.define("dict", lambda args: dict(args[0]))
        self._env.define("Ident", lambda args: Ident(args[0]))
        self._env.define("tuple", lambda args: tuple(args))

        self._env.define("print", lambda args: print(*args))

        self._env.define("read", lambda args: open(args[0], "r").read())
        self._env.define("load", lambda args: self._load(args[0]))

        self._env.define("eval", lambda args: Evaluator().eval(self.ast(args[0]), self._env))
        self._env.define("eval_expr", lambda args: Evaluator().eval(args[0], self._env))
        self._env.define("apply", lambda args: Evaluator().apply(args[0], args[1]))

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

    def _load(self, path):
        with open(path, "r") as f: src = f.read()
        return Evaluator().eval(self.ast(src), Environment(self._env))

    def scan(self, src: Source) -> list[Token]:
        return Scanner(src).tokenize()

    def parse(self, tokens: list[Token]) -> Expr:
        return Parser(tokens).parse()

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

if __name__ == "__main__":
    import sys

    toil = Interpreter().init_env().stdlib()

    def repl():
        while True:
            print("\nInput source and enter Ctrl+D:")
            if (src := sys.stdin.read()) == "": exit(0)
            try:
                expr = toil.ast(src)
                print("AST:", expr, sep="\n")
                print("Output:")
                result = toil.eval(expr)
                print("Result:", result, sep="\n")
            except AssertionError as e:
                print("Error:", e, sep="\n")

    def walk_file(filename):
        with open(filename, "r") as f: result = toil.walk(f.read())
        exit(result if isinstance(result, int) else 0)

    if len(sys.argv) > 1:
        if sys.argv[1] == "--repl":
            repl()
        else:
            walk_file(sys.argv[1])

    # Example

    print(toil.ast(r""" macro do 2 + 3 end """)) # -> (macro, [[], (add, [2, 3])])
    print(toil.ast(r""" macro do 2 + 3 end () """)) # -> 5

    print(toil.ast(r""" macro cond, body do tuple(Ident('if'), [cond, body, None]) end """)) # -> (macro, [[cond, body], (tuple, [(Ident, ['if']), [cond, body, None]])])
    print(toil.ast(r""" macro cond, body do tuple(Ident('if'), [cond, body, None]) end (2 == 3, 1/0)""")) # -> (if, [(equal, [2, 3]), (div, [1, 0]), None])

    print(toil.ast(r""" when := macro cond, body do tuple(Ident('if'), [cond, body, None]) end """)) # -> None
    toil.walk(r""" when := macro cond, body do tuple(Ident('if'), [cond, body, None]) end """)
    toil.walk(r""" a := 2; b := 3 """)
    print(toil.ast(r""" when(a == b, 1 / 0) """)) # -> (if, [(equal, [a, b]), (div, [1, 0]), None])
    print(toil.walk(r""" when(a == b, 1 / 0) """)) # -> None

    toil.walk(r"""
        def test_macro_scope() do
            local_when := macro cond, body do tuple(Ident('if'), [cond, body, None]) end;
            local_when(2 == 2, 3)
        end
    """)
    print(toil.walk(" test_macro_scope() ")) # -> inside func
    # toil.walk(" local_when(2 == 2, 3) ") # -> Undefined variable

    # toil.walk(r""" def when_func(cond, body) do if cond then body end end """)
    # toil.walk(r""" when_func(a == b, 1 / 0) """) # -> ZeroDivisionError

    toil.walk(r""" unless := macro cond, body do tuple(Ident('when'), [tuple(Ident('not'), [cond]), body]) end """)
    print(toil.ast(r""" unless(a == b, 2 + 3) """)) # -> (if, [(not, [(equal, [a, b])]), (add, [2, 3]), None])
    print(toil.walk(r""" unless(a == b, 2 + 3) """)) # -> 5

    toil.walk(r""" obj := { when: func self, cond, body do "method called" end } """)
    print(toil.walk(r""" obj.when(True, "foo") """)) # -> method called

    toil.walk(r"""
        multi_and := macro a, *rest do
            if len(rest) == 0 then
                a
            else
                tuple(Ident('if'), [a, tuple(Ident('multi_and'), rest), False])
            end
        end
    """)
    print(toil.ast(r""" multi_and(1 == 1) """)) # -> (equal, [1, 1])
    print(toil.ast(r""" multi_and(1 == 1, 2 == 2, 3 == 3) """)) # -> (if, [(equal, [1, 1]), (if, [(equal, [2, 2]), (equal, [3, 3]), False]), False])
    print(toil.walk(r""" multi_and(1 == 1, 2 == 2, 3 == 3) """)) # -> True
    print(toil.walk(r""" multi_and(False, 1 / 0) """)) # -> False

    # toil.walk(r""" when(True) """) # -> Pattern mismatch
