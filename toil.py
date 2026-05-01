#! /usr/bin/env python3

from typing import Any


class Ident:
    __match_args__ = ("name",)

    def __init__(self, name: str): self.name = name
    def __hash__(self): return hash(self.name)
    def __repr__(self): return self.name
    def __str__(self): return self.name
    def __eq__(self, other):
        return isinstance(other, Ident) and self.name == other.name

RuleElement = Ident | tuple[Ident, list[Any]]
CustomRules = dict[str, list[RuleElement]]
Token = Ident | int | str | bool | None
Expr = Any
Value = Any
SymbolTable = dict[str, Value]


def is_ident_first(c): return c.isalpha() or c == "_"
def is_ident_rest(c): return c.isalnum() or c == "_"
def is_ident(s): return is_ident_first(s[0])
def toil_type(expr): return "Expr" if type(expr) is tuple else type(expr).__name__


class RuleCollector:
    def __init__(self, src):
        self._src = src

    def collect(self) -> CustomRules:
        custom_rules: CustomRules = {}
        for line in self._src.splitlines():
            line = line.strip()
            if line.startswith("#rule "):
                rule_src = line[6:]
                new_rule = Parser(Scanner(rule_src).tokenize(), {}).parse()
                assert type(new_rule) is dict, f"Invalid rule @ collect(): {new_rule}"
                custom_rules = {**custom_rules, **new_rule}
        return custom_rules


class Scanner:
    def __init__(self, src):
        self._src = src
        self._pos = 0
        self._tokens: list[Token] = []

    def tokenize(self) -> list[Token]:
        while True:
            while self._current_char().isspace():
                self._advance()

            if self._current_char() == "#":
                while self._current_char() not in ("\n", "$EOF"):
                    self._advance()
                continue

            match self._current_char():
                case "$EOF":
                    self._tokens.append(Ident("$EOF"))
                    break
                case ch if ch.isnumeric():
                    self._number()
                case "'":
                    self._raw_string()
                case "\"":
                    self._string()
                case c if is_ident_first(c):
                    self._ident()
                case "!":
                    self._two_char_operator("=!")
                case ch if ch in "=!<>:":
                    self._two_char_operator("=")
                case "-":
                    self._two_char_operator(">")
                case ch if ch in "+*/%()[]{}.;,":
                    self._tokens.append(Ident(ch))
                    self._advance()
                case invalid:
                    assert False, f"Invalid character @ tokenize(): {invalid}"

        return self._tokens

    def _number(self):
        start = self._pos
        while self._current_char().isnumeric():
            self._advance()
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
        while (c := self._current_char()) != "\"":
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
        while is_ident_rest(self._current_char()):
            self._advance()
        token = self._src[start:self._pos]
        match token:
            case "None": self._tokens.append(None)
            case "True": self._tokens.append(True)
            case "False": self._tokens.append(False)
            case _: self._tokens.append(Ident(token))

    def _two_char_operator(self, successors):
        start = self._pos
        self._advance()
        if self._current_char() in successors:
            self._advance()
        self._tokens.append(Ident(self._src[start:self._pos]))

    def _advance(self):
        self._pos += 1

    def _current_char(self):
        if self._pos < len(self._src):
            return self._src[self._pos]
        else:
            return "$EOF"


class Parser:
    def __init__(self, tokens: list[Token], custom_rules: CustomRules):
        self._tokens = tokens
        self._pos = 0
        self._custom_rules = custom_rules

    def parse(self) -> Expr:
        expr = self._expression()
        assert self._current_token() == Ident("$EOF"), \
            f"Extra token @ parse(): {self._current_token()}"
        return expr

    def _expression(self):
        return self._sequence()

    def _sequence(self):
        exprs = [self._define_assign()]
        while self._current_token() == Ident(";"):
            self._advance()
            exprs.append(self._define_assign())
        return exprs[0] if len(exprs) == 1 else (Ident("seq"), exprs)

    def _define_assign(self):
        return self._binary_right({
            Ident(":="): Ident("define"), Ident("="): Ident("assign")
        }, self._arrow)

    def _arrow(self):
        left = self._and_or()
        if self._current_token() == Ident("->"):
            self._advance()
            right = self._arrow()
            params = left if isinstance(left, list) else [left]
            return (Ident("__core_func"), [params, right])
        return left

    def _and_or(self):
        return self._binary_left({
            Ident("and"): Ident("and"), Ident("or"): Ident("or"),
        }, self._not)

    def _not(self):
        return self._unary({
            Ident("not"): Ident("not")
        }, self._comparison)

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
            Ident("-"): Ident("neg"), Ident("+"): Ident("+"), Ident("*"): Ident("*"),
            Ident("!"): Ident("!"), Ident("!!"): Ident("!!")
        }, self._call_index_dot)

    def _call_index_dot(self):
        target = self._primary()
        while self._current_token() in (Ident("("), Ident("["), Ident(".")):
            match self._current_token():
                case Ident("("):
                    self._advance()
                    target = (target, self._comma_separated_exprs(Ident(")")))
                    self._consume(Ident(")"))
                case Ident("["):
                    self._advance()
                    index = self._expression()
                    self._consume(Ident("]"))
                    target = (Ident("index"), [target, index])
                case Ident("."):
                    self._advance()
                    assert type(self._current_token()) is Ident, \
                        f"Invalid attribute @ _call_index_dot(): {self._current_token()}"
                    attr = self._advance()
                    target = (Ident("dot"), [target, str(attr)])
        return target

    def _primary(self):
        match self._current_token():
            case Ident("("): return self._group()
            case Ident("["): return self._list()
            case Ident("{"): return self._dict()
            case None | bool() | int() | str(): return self._advance()
            case Ident(name) if name in self._custom_rules:
                return self._custom(self._custom_rules[name])
            case Ident(name) if is_ident(name): return self._advance()
            case unexpected:
                assert False, f"Unexpected token @ _primary(): {unexpected}"

    def _group(self):
        self._advance()
        expr = self._expression()
        self._consume(Ident(")"))
        return expr

    def _list(self):
        self._advance()
        exprs = self._comma_separated_exprs(Ident("]"))
        self._consume(Ident("]"))
        return exprs

    def _dict(self):
        def _parse_key_value(dic):
            match self._current_token():
                case Ident("*"):
                    self._advance()
                    rest_name = self._advance()
                    assert isinstance(rest_name, Ident), \
                        f"Expected rest pattern name @ _dict(): {rest_name}"
                    dic["*"] = rest_name
                case Ident(key):
                    self._advance()
                    if self._current_token() == Ident(":"):
                        self._advance()
                        dic[key] = self._expression()
                    else:
                        dic[key] = Ident(key)
                case str():
                    key = self._advance()
                    self._consume(Ident(":"))
                    dic[key] = self._expression()
                case invalid:
                    assert False, f"Invalid key @ _dict(): {invalid}"

        self._advance()
        dic = {}
        if self._current_token() != Ident("}"):
            _parse_key_value(dic)
            while self._current_token() != Ident("}"):
                self._consume(Ident(","))
                _parse_key_value(dic)
        self._advance()
        return dic

    def _custom(self, rule):
        def match_args(rule):
            args = []
            for current, next in zip(rule, rule[1:] + [None]):
                match current:
                    case Ident("EXPR"):
                        args.append(self._expression())
                    case Ident("EXPRS"):
                        args.append(self._comma_separated_exprs(next))
                    case (Ident("*"), [subrule]):
                        subargs = []
                        while self._current_token() == subrule[0]:
                            subargs.append(match_args(subrule))
                        args.append(subargs)
                    case (Ident("+"), [subrule]):
                        if self._current_token() == subrule[0]:
                            args.append(match_args(subrule))
                        else:
                            args.append([])
                    case delimiter:
                        self._consume(delimiter)
            return args

        self._advance()
        return (rule[0], match_args(rule[1:]))

    def _binary_left(self, ops, sub_elem):
        left = sub_elem()
        while type(self._current_token()) is Ident and \
                (op := self._current_token()) in ops:
            self._advance()
            right = sub_elem()
            left = (ops[op], [left, right])
        return left

    def _binary_right(self, ops, sub_elem):
        left = sub_elem()
        if type(self._current_token()) is Ident and \
                (op := self._current_token()) in ops:
            self._advance()
            right = self._binary_right(ops, sub_elem)
            return (ops[op], [left, right])
        return left

    def _unary(self, ops, sub_elem):
        if type(self._current_token()) is Ident and \
                (op := self._current_token()) in ops:
            self._advance()
            return (ops[op], [self._unary(ops, sub_elem)])
        else:
            return sub_elem()

    def _comma_separated_exprs(self, terminator):
        cse = []
        if self._current_token() != terminator:
            cse.append(self._expression())
            while self._current_token() == Ident(","):
                self._advance()
                cse.append(self._expression())
        return cse

    def _consume(self, expected):
        assert self._current_token() == expected, \
            f"Expected {expected} @ consume: {self._current_token()}"
        return self._advance()

    def _current_token(self):
        return self._tokens[self._pos]

    def _advance(self):
        self._pos += 1
        return self._tokens[self._pos - 1]


class Environment(dict):
    def __init__(self, parent=None):
        self["parent"] = parent
        self["vars"] = {}
        self["define"] = lambda args: self.define(args[0], args[1])
        self["val"] = lambda args: self.val(args[0])
        self["assign"] = lambda args: self.assign(args[0], args[1])
        self["lookup"] = lambda args: self.lookup(args[0])

    def __repr__(self):
        content = "__builtins" if "__builtins" in self["vars"] else \
                  "__corelib" if "__corelib" in self["vars"] else \
                  "__stdlib" if "__stdlib" in self["vars"] else \
                  ", ".join(self["vars"])
        return f"[{content}]" + (f" < {self['parent']}" if self["parent"] else "")

    def define(self, name: str, val):
        self["vars"][name] = val
        return val

    def lookup(self, name: str):
        if name in self["vars"]:
            return self["vars"]
        elif self["parent"] is not None:
            return self["parent"].lookup(name)
        else:
            return None

    def val(self, name: str):
        vars = self.lookup(name)
        assert vars is not None, f"Undefined variable @ val(): {name}"
        return vars[name]

    def assign(self, name: str, val):
        vars = self.lookup(name)
        assert vars is not None, f"Undefined variable @ assign(): {name}"
        vars[name] = val
        return val


class ToilException(Exception):
    def __init__(self, e=None):
        self.e = e

class ReturnException(Exception):
    def __init__(self, val=None): self.val = val

class ContinueException(Exception): pass
class BreakException(Exception): pass

class Evaluator:
    def eval(self, expr: Expr, env: Environment) -> Value:
        match expr:
            case None | bool() | int() | str():
                return expr
            case exprs if type(exprs) is list:
                return [self.eval(expr, env) for expr in exprs]
            case exprs if type(exprs) is dict:
                return {key: self.eval(val, env) for key, val in exprs.items()}
            case Ident("__env"):
                return env
            case Ident(name):
                return env.val(name)
            case (Ident("__core_quote"), [expr]):
                return self._quote(expr, env)
            case (Ident("define"), [left_expr, right_expr]):
                return self._define(left_expr, right_expr, env)
            case (Ident("assign"), [left_expr, right_expr]):
                return self._assign(left_expr, right_expr, env)
            case (Ident("seq"), exprs):
                return self._seq(exprs, env)
            case (Ident("__core_if"), [cond_expr, then_expr, else_expr]):
                return self._if(cond_expr, then_expr, else_expr, env)
            case (Ident("__core_match"), [val_expr, cases_expr]):
                return self._match(val_expr, cases_expr, env)
            case (Ident("__core_while"), [cond_expr, body_expr, then_expr, else_expr]):
                return self._while(cond_expr, body_expr, then_expr, else_expr, env)
            case (Ident("continue"), []):
                raise ContinueException()
            case (Ident("break"), []):
                raise BreakException()
            case (Ident("__core_func"), [params, body]):
                return (Ident("closure"), [params, body, env, None])
            case (Ident("return"), args):
                assert len(args) <= 1, \
                    f"Return takes zero or one argument @ evaluate(): {args}"
                raise ReturnException(self.eval(args[0], env) if args else None)
            case (Ident("expand"), [(op_expr, args_expr)]):
                return self._expand(op_expr, args_expr, env)
            case (Ident("__core_macro"), [params, body]):
                return (Ident("mclosure"), params, body, env)
            case (Ident("__core_try"), [body_expr, clauses_expr]):
                return self._try(body_expr, clauses_expr, env)
            case (Ident("raise"), args):
                assert len(args) <= 1, \
                    f"Raise takes zero or one argument @ evaluate(): {args}"
                raise ToilException(self.eval(args[0], env) if args else None)
            case (Ident("__core_scope"), [expr]):
                return self.eval(expr, Environment(env))
            case (Ident("dot"), [target_expr, attr_expr]):
                return self._dot(target_expr, attr_expr, env)
            case (op_expr, args_expr) if isinstance(expr, tuple):
                return self._op(op_expr, args_expr, env)
            case unexpected:
                assert False, f"Unexpected expression @ evaluate(): {unexpected}"

    def _quote(self, expr, env):
        def items(exprs):
            quoted = []
            for expr in exprs:
                match expr:
                    case (Ident("!!"), [elem]):
                        quoted += self.eval(elem, env)
                    case _:
                        quoted.append(self._quote(expr, env))
            return quoted

        match expr:
            case [*exprs] if isinstance(expr, list):
                return items(exprs)
            case (Ident("!"), [elem]):
                return self.eval(elem, env)
            case (*exprs,):
                return tuple(items(exprs))
            case _:
                return expr

    def _define(self, left_expr, right_expr, env):
        right_val = self.eval(right_expr, env)
        match left_expr:
            case Ident(name):
                match right_val:
                    case (Ident("closure"), [params, body, closure_env, fallback]):
                        old_val_dict = env.lookup(name)
                        if old_val_dict is not None and name in old_val_dict:
                            old_val = old_val_dict[name]
                            match old_val:
                                case (Ident("closure"), _):
                                    right_val = (Ident("closure"), [params, body, closure_env, old_val])
        if self._match_pattern(left_expr, right_val, env):
            return right_val
        assert False, f"Pattern mismatch @ _define(): {left_expr}, {right_val}"

    def _assign(self, left_expr, right_expr, env):
        right_val = self.eval(right_expr, env)
        match left_expr:
            case Ident(name):
                return env.assign(name, right_val)
            case (Ident("index"), [coll_expr, index_expr]) | \
                 (Ident("dot"), [coll_expr, index_expr]):
                coll_val = self.eval(coll_expr, env)
                index_val = self.eval(index_expr, env)
                match coll_val, index_val:
                    case list(), int():
                        coll_val[index_val] = right_val
                    case dict(), str():
                        match right_val:
                            case (Ident("closure"), [params, body, closure_env, fallback]):
                                if index_val in coll_val:
                                    old_val = coll_val[index_val]
                                    match old_val:
                                        case (Ident("closure"), _):
                                            right_val = (Ident("closure"), [params, body, closure_env, old_val])
                        coll_val[index_val] = right_val
                    case _:
                        assert False, f"Invalid indexing @ _assign(): {coll_val}, {index_val}"
                return right_val
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

    def _match(self, val_expr, cases_expr, env):
        val = self.eval(val_expr, env)
        for pattern, body_expr in cases_expr:
            if self._match_pattern(pattern, val, env):
                return self.eval(body_expr, env)
        return None

    def _while(self, cond_expr, body_expr, then_expr, else_expr, env):
        while self.eval(cond_expr, env):
            try:
                self.eval(body_expr, env)
            except ContinueException: continue
            except BreakException:
                return None if else_expr == [] else self.eval(else_expr[0], env)
        return None if then_expr == [] else self.eval(then_expr[0], env)

    def _try(self, body_expr, clauses_expr, env):
        try:
            return self.eval(body_expr, env)
        except ToilException as toil_exception:
            for cond_expr, except_expr in clauses_expr:
                if self._match_pattern(cond_expr, toil_exception.e, env):
                    return self.eval(except_expr, env)
            raise toil_exception

    def _dot(self, target_expr, attr_expr, env):
        target_val = self.eval(target_expr, env)
        match target_val:
            case dict() if attr_expr in target_val:
                attr_val = target_val[attr_expr]
                match attr_val:
                    case (Ident("closure"), [[Ident("self"), *_], _, _, _]):
                        return lambda args: self.apply(attr_val, [target_val] + args)
                return attr_val

        attr_val = env.val(attr_expr)
        match attr_val:
            case c if callable(c):
                return lambda args: c([target_val] + args)
            case (Ident("closure"), [_, _, _, _]):
                return lambda args: self.apply(attr_val, [target_val] + args)

    def _op(self, op_expr, args_expr, env):
        op_val = self.eval(op_expr, env)
        match op_val:
            case (Ident("mclosure"), params, body_expr, mclosure_env):
                new_env = Environment(mclosure_env)
                expanded = self._expand_macro(params, args_expr, body_expr, new_env)
                # print(expanded)
                return self.eval(expanded, env)
            case _:
                args_val = [self.eval(arg, env) for arg in args_expr]
                return self.apply(op_val, args_val)

    def _expand(self, op_expr, args_expr, env):
        match self.eval(op_expr, env):
            case (Ident("mclosure"), params, body_expr, mclosure_env):
                new_env = Environment(mclosure_env)
                return self._expand_macro(params, args_expr, body_expr, new_env)
            case _:
                assert False, f"Cannot expand non-macro @ expand(): {op_expr}"

    def _expand_macro(self, params, args_expr, body_expr, env):
        if self._match_pattern(params, args_expr, env):
            try:
                return self.eval(body_expr, env)
            except ReturnException as e: return e.val
        assert False, f"Argument mismatch @ expand(): {params}, {args_expr}"

    def apply(self, op_val, args_val):
        match op_val:
            case c if callable(c):
                return c(args_val)
            case (Ident("closure"), [params, body, closure_env, fallback]):
                new_env = Environment(closure_env)
                if self._match_pattern(params, args_val, new_env):
                    try:
                        return self.eval(body, new_env)
                    except ReturnException as e: return e.val
                if fallback is not None:
                    return self.apply(fallback, args_val)
                assert False, f"Argument mismatch @ apply(): {params}, {args_val}"
            case _:
                assert False, f"Invalid operator @ apply(): {op_val}"

    def _match_pattern(self, pattern, value, env):
        def _match_list():
            i = 0; lpat = len(pattern); lval = len(value)

            # Before '*'
            while i < lpat:
                sub_pat = pattern[i]
                match sub_pat:
                    case (Ident("*"), [Ident(rest_name)]): break
                if i >= lval: return False
                sub_val = value[i]
                if not self._match_pattern(sub_pat, sub_val, env):
                    return False
                i += 1
            else:
                # No '*'
                return i == lval

            # At '*'
            lrest = lval - lpat + 1
            if lrest < 0: return False
            env.define(rest_name, value[i:i + lrest])
            i += 1

            # After '*'
            while i < lpat:
                sub_pat = pattern[i]
                match sub_pat:
                    case (Ident("*"), [Ident(rest_name)]): return False
                sub_val = value[i + lrest - 1]
                if not self._match_pattern(sub_pat, sub_val, env):
                    return False
                i += 1

            return True

        def _match_dict():
            rest_name = pattern.get("*")

            fixed_patterns = pattern.copy()
            remaining_values = value.copy()

            if rest_name is not None:
                fixed_patterns.pop("*")

            for key, sub_pattern in fixed_patterns.items():
                if key not in remaining_values:
                    return False
                if not self._match_pattern(sub_pattern, remaining_values[key], env):
                    return False
                remaining_values.pop(key)

            if rest_name is not None:
                env.define(rest_name.name, remaining_values)
            return True

        match pattern:
            case Ident(name):
                env.define(name, value)
                return True
            case list():
                return toil_type(value) == 'list' and _match_list()
            case dict():
                return toil_type(value) == 'dict' and _match_dict()
            case (Ident("or"), [left_pat, right_pat]):
                return self._match_pattern(left_pat, value, env) or \
                       self._match_pattern(right_pat, value, env)
            case (Ident('Ident'), [name_pat]):
                return toil_type(value) == 'Ident' and \
                    self._match_pattern(name_pat, value.name, env)
            case (Ident('Expr'), expr_pats):
                return (
                    toil_type(value) == 'Expr' and len(expr_pats) == len(value) and
                    all(self._match_pattern(p, v, env) for p, v in zip(expr_pats, value))
                )
            case (Ident(typ), [val_pat]):
                if toil_type(value) != typ: return False
                return self._match_pattern(val_pat, value, env)
            case _:
                return type(pattern) is type(value) and pattern == value

class Interpreter:
    def __init__(self):
        self._env = Environment()
        self._custom_rules = {}

    def _load(self, path):
        with open(path, "r") as f: src = f.read()
        module_env = Environment(self._env)
        expr = self.ast(src)
        return Evaluator().eval(expr, module_env)

    def init_env(self):
        self._env = Environment()
        self._builtins()
        self._corelib()

        return self

    def _builtins(self):
        self._env.define("__builtins", None)

        self._env.define("load", lambda args: self._load(args[0]))
        self._env.define("read", lambda args: open(args[0], "r").read())

        self._env.define("eval", lambda args: Evaluator().eval(
            self.ast(args[0]),
            args[1] if len(args) > 1 else self._env
        ))
        self._env.define("eval_expr", lambda args: Evaluator().eval(
            args[0],
            args[1] if len(args) > 1 else self._env
        ))
        self._env.define("apply",
            lambda args: Evaluator().apply(args[0], args[1])
        )

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

        self._env.define("chr", lambda args: chr(args[0]))
        self._env.define("ord", lambda args: ord(args[0]))
        self._env.define("join", lambda args: str(args[1]).join(map(str, args[0])))

        self._env.define("keys", lambda args: list(args[0].keys()))
        self._env.define("items", lambda args: [list(e) for e in args[0].items()])

        self._env.define("type", lambda args: toil_type(args[0]))
        self._env.define("bool", lambda args: bool(args[0]))
        self._env.define("int", lambda args: int(args[0]))
        self._env.define("str", lambda args: str(args[0]))
        self._env.define("list", lambda args: list(args[0]))
        self._env.define("dict", lambda args: dict(args[0]))
        self._env.define("Ident", lambda args: Ident(args[0]))
        self._env.define("Expr", lambda args: tuple(args))

        self._env.define("print", lambda args: print(*args))

        self._env = Environment(self._env)

    def _corelib(self):
        self.walk("""
            __corelib := None;

            #rule {func: [__core_func, EXPRS, do, EXPR, end]}
            #rule {macro: [__core_macro, EXPRS, do, EXPR, end]}

            #rule {scope: [__core_scope, EXPR, end]}

            #rule {quote: [__core_quote, EXPR, end]}

            __core_defmacro := macro call_expr, body do
                match call_expr
                    case Expr(name, args) then
                        quote !name := macro !!args do !body end end
                    case Ident(name) then
                        quote !call_expr := macro do !body end end
                    case _ then
                        raise("Invalid defmacro syntax")
                end
            end;
            #rule {defmacro: [__core_defmacro, EXPR, do, EXPR, end]}

            defmacro __core_quotes(expr) do quote quote scope !expr end end end end;
            #rule {quotes: [__core_quotes, EXPR, end]}

            defmacro __core_def(call_expr, body) do
                match call_expr
                    case Expr(name, args) then
                        quote !name := func !!args do !body end end
                    case Ident(name) then
                        quote !call_expr := func do !body end end
                    case _ then
                        raise("Invalid def syntax")
                end
            end;
            #rule {def: [__core_def, EXPR, do, EXPR, end]}

            #rule {pif: [__core_if, EXPR, then, EXPR, else, EXPR, end]}

            defmacro __core_if_macro(cnd, thn, elifs, els) do scope
                __core_if_expr := pif els == [] then None else els[0] end;
                __core_if_i := len(elifs) - 1;
                while __core_if_i >= 0 do
                    [__core_if_elif_cnd, __core_if_elif_thn] := elifs[__core_if_i];
                    __core_if_expr = quote
                        pif !__core_if_elif_cnd then
                            !__core_if_elif_thn
                        else
                            !__core_if_expr
                        end
                    end;
                    __core_if_i = __core_if_i - 1
                end;
                quote pif !cnd then !thn else !__core_if_expr end end
            end end;
            #rule {if: [__core_if_macro, EXPR, then, EXPR, *[elif, EXPR, then, EXPR], +[else, EXPR], end]}

            #rule {match: [__core_match, EXPR, *[case, EXPR, then, EXPR], end]}

            defmacro _aif(cnd, thn, els) do quote
                pif it := !cnd then !thn else !els end
            end end;
            #rule {aif: [_aif, EXPR, then, EXPR, else, EXPR, end]}

            defmacro and(a, b) do quote aif !a then !b else it end end end;
            defmacro or(a, b) do quote aif !a then it else !b end end end;

            #rule {while: [__core_while, EXPR, do, EXPR, +[then, EXPR], +[else, EXPR], end]}

            defmacro __core_for(var, coll, body, thn, els) do quote scope
                __core_for_coll := !coll;
                __core_for_index := -1;
                !Expr(Ident("__core_while"), [
                    quote __core_for_index + 1 < len(__core_for_coll) end,
                    quote
                        __core_for_index = __core_for_index + 1;
                        !var := __core_for_coll[__core_for_index];
                        !body
                    end,
                    thn,
                    els
                ])
            end end end;
            #rule {for: [__core_for, EXPR, in, EXPR, do, EXPR, +[then, EXPR], +[else, EXPR], end]}

            #rule {try: [__core_try, EXPR, *[except, EXPR, then, EXPR], end]}

            # Object oriented notations

            defmacro __core_defclass(name, params_, body) do
                quote
                    def (!name)(!!params_) do self := {}; !body; self end
                end
            end;
            #rule {defclass: [__core_defclass, EXPR, params, EXPRS, do, EXPR, end]}

            defmacro inherits(super) do
                quote self = !super end
            end;

            defmacro __core_defmethod(name, params_, body) do
                Expr(Ident("assign"), [
                        Expr(Ident("dot"), [Ident("self"), str(name) ]),
                        quote func self, !!params_ do !body end end
                ])
            end;
            #rule {defmethod: [__core_defmethod, EXPR, params, EXPRS, do, EXPR, end]}

            defmacro __core_defmodule(name_expr, export_expr, body_expr) do
                quote def !name_expr do !body_expr; !export_expr end end
            end;
            #rule {defmodule: [__core_defmodule, EXPR, export, EXPR, do, EXPR, end]}

            defmacro __core_import(mod_expr, name_expr) do
                quote !name_expr := (!mod_expr)() end
            end
            #rule {import: [__core_import, EXPR, as, EXPR, end]}
            #rule {from: [__core_import, EXPR, import, EXPR, end]}
        """)

        self._env = Environment(self._env)

    def stdlib(self):
        self.walk("""
            __stdlib := None;

            def first(a) do a[0] end;
            def rest(a) do slice(a, 1, None) end;
            def last(a) do a[-1] end;

            def map(a, f) do
                b := []; l := len(a);
                i := 0; while i < l do
                    push(b, f(a[i]));
                    i = i + 1
                end;
                b
            end;

            def filter(a, f) do
                b := []; l := len(a);
                i := 0; while i < l do
                    if f(a[i]) then push(b, a[i]) end;
                    i = i + 1
                end;
                b
            end;

            def zip(a, b) do
                z := []; la := len(a); lb := len(b);
                i := 0; while i < la and i < lb do
                    push(z, [a[i], b[i]]);
                    i = i + 1
                end;
                z
            end;

            def reduce(a, f, init) do
                acc := init; l := len(a);
                i := 0; while i < l do
                    acc = f(acc, a[i]);
                    i = i + 1
                end;
                acc
            end;

            def reverse(a) do
                b := []; i := len(a) - 1;
                while i >= 0 do
                    push(b, a[i]);
                    i = i - 1
                end;
                b
            end;

            def range(start, stop, step) do
                b := [];
                i := start; while i < stop do
                    push(b, i);
                    i = i + step
                end;
                b
            end;

            def enumerate(a) do
                zip(range(0, len(a), 1), a)
            end;

            def all(a, f) do
                for x in a do if not f(x) then return(False) end end; True
            end;

            def any(a, f) do
                for x in a do if f(x) then return(True) end end; False
            end
            """)

        self._env = Environment(self._env)
        return self

    def collect_rules(self, src: str):
        self._custom_rules = {**self._custom_rules, **RuleCollector(src).collect()}

    def scan(self, src: str) -> list[Token]:
        return Scanner(src).tokenize()

    def parse(self, tokens: list[Token]) -> Expr:
        return Parser(tokens, self._custom_rules).parse()

    def ast(self, src: str) -> Expr:
        self.collect_rules(src)
        return self.parse(self.scan(src))

    def eval(self, ast: Expr) -> Value:
        try:
            return Evaluator().eval(ast, self._env)
        except ToilException as e: assert False, f"ToilException @ evaluate(): {e.e}"
        except ReturnException as e: assert False, f"Return from top level @ evaluate(): {e.val}"
        except ContinueException: assert False, "Continue at top level @ evaluate()"
        except BreakException: assert False, f"Break at top level @ evaluate()"

    def walk(self, src: str) -> Value:
        return self.eval(self.ast(src))

if __name__ == "__main__":
    import sys

    i = Interpreter().init_env().stdlib()
    def scan(src): return i.scan(src)
    def ast(src): return i.ast(src)
    def eval(expr): return i.eval(expr)
    def walk(src): return i.walk(src)

    def repl():
        while True:
            print("\nInput source and enter Ctrl+D:")
            if (src := sys.stdin.read()) == "":
                exit(0)
            try:
                expr = ast(src)
                print("AST:", expr, sep="\n")
                print("Output:")
                result = eval(expr)
                print("Result:", result, sep="\n")
            except AssertionError as e:
                print("Error:", e, sep="\n")

    def run(filename):
        with open(filename, "r") as f:
            result = walk(f.read())
        exit(result if isinstance(result, int) else 0)

    if len(sys.argv) > 1:
        if sys.argv[1] == "--repl":
            repl()
        else:
            run(sys.argv[1])

    # Example

    # Def
    walk("""
        def say_hello do "hello" end
    """)
    print(walk(""" say_hello() """)) # -> hello

    walk("""
        def fact(n) do n * fact(n - 1) end;
        def fact(0) do 1 end
    """)
    print(walk(""" fact(0) """)) # -> 1
    print(walk(""" fact(3) """)) # -> 6

    # Defmacro
    print("\nDefmacro")
    walk("""
        defmacro mwhen(cond, body) do
            quote if !cond then !body else None end end
        end
    """)
    print(walk(""" expand(mwhen(2 == 2, 3)) """)) # -> (__core_if_macro, [(equal, [2, 2]), 3, [], [None]])
    print(walk(""" mwhen(2 == 2, 3) """)) # -> 3
    print(walk(""" mwhen(2 == 3, 4 / 0) """)) # -> None

    walk(""" defmacro mzero() do quote 2 end end """)
    print(walk(""" mzero() """)) # -> 2

    walk(""" defmacro mzero_no_paren do quote 3 end end """)
    print(walk(""" mzero_no_paren() """)) # -> 3

    # walk(""" mwhen(2 == 2) """) # -> Argument mismatch
    # walk(""" defmacro 2 do 3 end """) # -> Invalid defmacro syntax
