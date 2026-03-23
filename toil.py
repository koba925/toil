#! /usr/bin/env python3

class Sym(str):
    def __repr__(self): return super().__repr__()[1:-1]


def is_name_first(c): return c.isalpha() or c == "_"
def is_name_rest(c): return c.isalnum() or c == "_"
def is_name(expr): return isinstance(expr, Sym) and is_name_first(expr[0])


class RuleCollector:
    def __init__(self, src):
        self._src = src

    def collect(self):
        custom_rules = {}
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
                case "'":
                    self._raw_string()
                case "\"":
                    self._string()
                case c if is_name_first(c):
                    self._name()
                case "!" as ch:
                    start = self._pos
                    self._advance()
                    if self._current_char() in ("=", "!"):
                        self._advance()
                    self._tokens.append(Sym(self._src[start:self._pos]))
                case ("=" | "!" | "<" | ">" | ":") as ch:
                    start = self._pos
                    self._advance()
                    if self._current_char() == "=":
                        self._advance()
                    self._tokens.append(Sym(self._src[start:self._pos]))
                case ("+" | "-" | "*" | "/" | "%" | "(" | ")" | "[" | "]" | "{" | "}" | "." | ";" | ",") as ch:
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
        return self._tokens.append("".join(s))

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
    def __init__(self, tokens, custom_rules):
        self._tokens = tokens
        self._pos = 0
        self._custom_rules = custom_rules

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
        return exprs[0] if len(exprs) == 1 else (Sym("seq"), exprs)

    def _define_assign(self):
        return self._binary_right({
            Sym(":="): Sym("define"), Sym("="): Sym("assign")
        }, self._and_or)

    def _and_or(self):
        return self._binary_left({
            Sym("and"): Sym("and"), Sym("or"): Sym("or"),
        }, self._not)

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
        }, self._unaries)

    def _unaries(self):
        return self._unary({
            Sym("-"): Sym("neg"), Sym("+"): Sym("+"), Sym("*"): Sym("*"),
            Sym("!"): Sym("!"), Sym("!!"): Sym("!!")
        }, self._call_index_dot)

    def _call_index_dot(self):
        target = self._primary()
        while type(self._current_token()) is Sym and \
                self._current_token() in (Sym("("), Sym("["), Sym(".")):
            match self._current_token():
                case Sym("("):
                    self._advance()
                    target = (target, self._comma_separated_exprs(Sym(")")))
                    self._consume(Sym(")"))
                case Sym("["):
                    self._advance()
                    index = self._expression()
                    self._consume(Sym("]"))
                    target = (Sym("index"), [target, index])
                case Sym("."):
                    self._advance()
                    assert type(self._current_token()) is Sym, \
                        f"Invalid property @ _call_index_dot(): {self._current_token()}"
                    attr = self._advance()
                    target = (Sym("dot"), [target, str(attr)])
        return target

    def _primary(self):
        match self._current_token():
            case Sym("("): return self._paren()
            case Sym("["): return self._array()
            case Sym("{"): return self._dic()
            case None | bool() | int(): return self._advance()
            case s if type(s) is str: return self._advance()
            case Sym(name) if name in self._custom_rules:
                return self._custom(self._custom_rules[name])
            case Sym(name) if is_name(name): return self._advance()
            case unexpected:
                assert False, f"Unexpected token @ _primary(): {unexpected}"

    def _paren(self):
        self._advance()
        expr = self._expression()
        self._consume(Sym(")"))
        return expr

    def _array(self):
        self._advance()
        array = self._comma_separated_exprs(Sym("]"))
        self._consume(Sym("]"))
        return array

    def _dic(self):
        def _parse_key_value(dic):
            match self._current_token():
                case Sym("*"):
                    self._advance()
                    rest_name = self._advance()
                    assert is_name(rest_name), f"Expected rest pattern name @ _dic(): {rest_name}"
                    dic[Sym("*")] = rest_name
                case Sym():
                    key = str(self._advance())
                    if self._current_token() == Sym(":"):
                        self._advance()
                        dic[key] = self._expression()
                    else:
                        dic[key] = Sym(key)
                case str():
                    key = self._advance()
                    self._consume(Sym(":"))
                    dic[key] = self._expression()
                case Invalid:
                    assert False, f"Invalid key @ _dic(): {Invalid}"

        self._advance()
        dic = {}
        if self._current_token() != Sym("}"):
            _parse_key_value(dic)
            while self._current_token() != Sym("}"):
                self._consume(Sym(","))
                _parse_key_value(dic)
        self._advance()
        return dic

    def _custom(self, rule):
        def match_args(rule):
            args = []
            for current, next in zip(rule, rule[1:] + [None]):
                match current:
                    case "EXPR":
                        args.append(self._expression())
                    case "EXPRS":
                        args.append(self._comma_separated_exprs(Sym(next)))
                    case ("*", [subrule]):
                        subargs = []
                        while self._current_token() == subrule[0]:
                            subargs.append(match_args(subrule))
                        args.append(subargs)
                    case ("+", [subrule]):
                        if self._current_token() == subrule[0]:
                            args.append(match_args(subrule))
                        else:
                            args.append([])
                    case delimiter:
                        self._consume(Sym(delimiter))
            return args

        self._advance()
        op = Sym(rule[0])
        args = match_args(rule[1:])
        return (op, args)

    def _binary_left(self, ops, sub_elem):
        left = sub_elem()
        while type(self._current_token()) is Sym and \
                (op := self._current_token()) in ops:
            self._advance()
            right = sub_elem()
            left = (ops[op], [left, right])
        return left

    def _binary_right(self, ops, sub_elem):
        left = sub_elem()
        if type(self._current_token()) is Sym and \
                (op := self._current_token()) in ops:
            self._advance()
            right = self._binary_right(ops, sub_elem)
            return (ops[op], [left, right])
        return left

    def _unary(self, ops, sub_elem):
        if type(self._current_token()) is Sym and \
                (op := self._current_token()) in ops:
            self._advance()
            return (ops[op], [self._unary(ops, sub_elem)])
        else:
            return sub_elem()

    def _comma_separated_exprs(self, terminator):
        cse = []
        if self._current_token() != terminator:
            cse.append(self._expression())
            while self._current_token() == Sym(","):
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


class Environment:
    def __init__(self, parent=None):
        self._parent = parent
        self._vars = {}

    def __repr__(self):
        content = "__builtins" if Sym("__builtins") in self._vars else \
                  "__corelib" if Sym("__corelib") in self._vars else \
                  "__stdlib" if Sym("__stdlib") in self._vars else \
                  ", ".join(self._vars)
        return f"[{content}]" + (f" < {self._parent}" if self._parent else "")

    def define(self, name: Sym, val):
        self._vars[name] = val
        return val

    def lookup(self, name: Sym):
        if name in self._vars:
            return self._vars
        elif self._parent is not None:
            return self._parent.lookup(name)
        else:
            return None

    def val(self, name: Sym):
        vars = self.lookup(name)
        assert vars is not None, f"Undefined variable @ val(): {name}"
        return vars[name]

    def set_val(self, name: Sym, val):
        vars = self.lookup(name)
        assert vars is not None, f"Undefined variable @ set_val(): {name}"
        vars[name] = val
        return val


class ToilException(Exception):
    def __init__(self, e=None):
        self.e = e

class ReturnException(Exception):
    def __init__(self, val=None): self.val = val

class BreakException(Exception):
    def __init__(self, val=None): self.val = val

class ContinueException(Exception): pass

class Evaluator:
    def evaluate(self, expr, env):
        match expr:
            case None | bool() | int():
                return expr
            case s if type(s) is str:
                return s
            case exprs if type(exprs) is list:
                return [self.evaluate(expr, env) for expr in exprs]
            case exprs if type(exprs) is dict:
                return {key: self.evaluate(val, env) for key, val in exprs.items()}
            case Sym(name):
                return env.val(name)
            case (Sym("quote"), [expr]):
                return expr
            case (Sym("__core_qq"), [expr]):
                return self._evaluate_quasiquote(expr, env)
            case (Sym("define"), [left_expr, right_expr]):
                return self._evaluate_define(left_expr, right_expr, env)
            case (Sym("assign"), [left_expr, right_expr]):
                return self._evaluate_assign(left_expr, right_expr, env)
            case (Sym("seq"), exprs):
                return self._evaluate_seq(exprs, env)
            case (Sym("__core_if"), [cond_expr, then_expr, else_expr]):
                return self._evaluate_if(cond_expr, then_expr, else_expr, env)
            case (Sym("__core_match"), [val_expr, cases_expr]):
                return self._evaluate_match(val_expr, cases_expr, env)
            case (Sym("__core_while"), [cond_expr, body_expr]):
                return self._evaluate_while(cond_expr, body_expr, env)
            case (Sym("break"), args):
                assert len(args) <= 1, f"Break takes zero or one argument @ evaluate(): {args}"
                raise BreakException(self.evaluate(args[0], env) if args else None)
            case (Sym("continue"), args):
                assert len(args) == 0, f"Continue takes no arguments @ evaluate(): {args}"
                raise ContinueException()
            case (Sym("__core_func"), [params, body]):
                return (Sym("closure"), params, body, env)
            case (Sym("return"), args):
                assert len(args) <= 1, f"Return takes zero or one argument @ evaluate(): {args}"
                raise ReturnException(self.evaluate(args[0], env) if args else None)
            case (Sym("expand"), [(op_expr, args_expr)]):
                return self._eval_expand(op_expr, args_expr, env)
            case (Sym("__core_macro"), [params, body]):
                return (Sym("mclosure"), params, body, env)
            case (Sym("__core_try"), [body_expr, clauses_expr]):
                return self._evaluate_try(body_expr, clauses_expr, env)
            case (Sym("raise"), args):
                assert len(args) <= 1, f"Raise takes zero or one argument @ evaluate(): {args}"
                raise ToilException(self.evaluate(args[0], env) if args else None)
            case (Sym("__core_scope"), [expr]):
                return self.evaluate(expr, Environment(env))
            case (Sym("dot"), [target_expr, attr_expr]):
                return self._evaluate_dot(target_expr, attr_expr, env)
            case (op_expr, args_expr) if isinstance(expr, tuple):
                return self._eval_op(op_expr, args_expr, env)
            case unexpected:
                assert False, f"Unexpected expression @ evaluate(): {unexpected}"

    def _evaluate_quasiquote(self, expr, env):
        def items(exprs):
            quoted = []
            for expr in exprs:
                match expr:
                    case (Sym("!!"), [elem]):
                        quoted += self.evaluate(elem, env)
                    case _:
                        quoted.append(self._evaluate_quasiquote(expr, env))
            return quoted

        match expr:
            case [*exprs] if isinstance(expr, list):
                return items(exprs)
            case (Sym("!"), [elem]):
                return self.evaluate(elem, env)
            case (*exprs,):
                return tuple(items(exprs))
            case _:
                return expr

    def _evaluate_define(self, left_expr, right_expr, env):
        right_val = self.evaluate(right_expr, env)
        if self._match_pattern(left_expr, right_val, env):
            return right_val
        assert False, f"Pattern mismatch @ _evaluate_define(): {left_expr}, {right_val}"

    def _evaluate_assign(self, left_expr, right_expr, env):
        right_val = self.evaluate(right_expr, env)
        match left_expr:
            case Sym(name):
                return env.set_val(name, right_val)
            case (Sym("index"), [coll_expr, index_expr]) | (Sym("dot"), [coll_expr, index_expr]):
                coll_val = self.evaluate(coll_expr, env)
                index_val = self.evaluate(index_expr, env)
                match coll_val, index_val:
                    case list(), int():
                        coll_val[index_val] = right_val
                    case dict(), str():
                        coll_val[index_val] = right_val
                    case _:
                        assert False, f"Invalid indexing @ _evaluate_assign(): {coll_val}"
                return right_val
            case unexpected:
                assert False, f"Invalid assign target @ _evaluate_assign(): {unexpected}"

    def _evaluate_seq(self, exprs, env):
        val = None
        for expr in exprs:
            val = self.evaluate(expr, env)
        return val

    def _evaluate_if(self, cond_expr, then_expr, else_expr, env):
        new_env = Environment(env)
        if self.evaluate(cond_expr, new_env):
            return self.evaluate(then_expr, new_env)
        else:
            return self.evaluate(else_expr, new_env)

    def _evaluate_match(self, val_expr, cases_expr, env):
        val = self.evaluate(val_expr, env)
        for pattern, body_expr in cases_expr:
            new_env = Environment(env)
            if self._match_pattern(pattern, val, new_env):
                return self.evaluate(body_expr, new_env)
        return None

    def _evaluate_while(self, cond_expr, body_expr, env):
        while self.evaluate(cond_expr, env):
            try:
                self.evaluate(body_expr, env)
            except ContinueException: continue
            except BreakException as e: return e.val
        return None

    def _evaluate_try(self, body_expr, clauses_expr, env):
        try:
            return self.evaluate(body_expr, env)
        except ToilException as toil_exception:
            for cond_expr, except_expr in clauses_expr:
                if self._match_pattern(cond_expr, toil_exception.e, env):
                    return self.evaluate(except_expr, env)
            raise toil_exception

    def _evaluate_dot(self, target_expr, attr_expr, env):
        target_val = self.evaluate(target_expr, env)
        match target_val:
            case dict() if attr_expr in target_val:
                attr_val = target_val[attr_expr]
                match attr_val:
                    case (Sym("closure"), [Sym("self"), *_], _, _):
                        return lambda args: self.apply(attr_val, [target_val] + args)
                return attr_val

        attr_val = env.val(attr_expr)
        match attr_val:
            case c if callable(c):
                return lambda args: c([target_val] + args)
            case (Sym("closure"), _, _, _):
                return lambda args: self.apply(attr_val, [target_val] + args)

    def _eval_op(self, op_expr, args_expr, env):
        op_val = self.evaluate(op_expr, env)
        match op_val:
            case (Sym("mclosure"), params, body_expr, mclosure_env):
                new_env = Environment(mclosure_env)
                expanded = self._expand(params, args_expr, body_expr, new_env)
                # print(expanded)
                return self.evaluate(expanded, env)
            case _:
                args_val = [self.evaluate(arg, env) for arg in args_expr]
                return self.apply(op_val, args_val)

    def _eval_expand(self, op_expr, args_expr, env):
        match self.evaluate(op_expr, env):
            case (Sym("mclosure"), params, body_expr, mclosure_env):
                new_env = Environment(mclosure_env)
                return self._expand(params, args_expr, body_expr, new_env)
            case _:
                assert False, f"Cannot expand non-macro @ expand(): {op_expr}"

    def _expand(self, params, args_expr, body_expr, env):
        if self._match_pattern(params, args_expr, env):
            try:
                return self.evaluate(body_expr, env)
            except ReturnException as e: return e.val
        assert False, f"Argument mismatch @ expand(): {params}, {args_expr}"

    def apply(self, op_val, args_val):
        match op_val:
            case c if callable(c):
                return c(args_val)
            case (Sym("closure"), params, body, closure_env):
                new_env = Environment(closure_env)
                if self._match_pattern(params, args_val, new_env):
                    try:
                        return self.evaluate(body, new_env)
                    except ReturnException as e: return e.val
                assert False, f"Argument mismatch @ apply(): {params}, {args_val}"
            case _:
                assert False, f"Invalid operator @ apply(): {op_val}"

    def _match_pattern(self, pattern, value, env):
        def match_list():
            match pattern:
                case [*prefix, (Sym("*"), [Sym(rest_name)])]:
                    if len(value) < len(prefix): return False
                    for sub_pattern, sub_value in zip(prefix, value):
                        if not self._match_pattern(sub_pattern, sub_value, env):
                            return False
                    env.define(rest_name, value[len(prefix):])
                    return True
                case _:
                    if len(pattern) != len(value): return False
                    for sub_pattern, sub_value in zip(pattern, value):
                        if not self._match_pattern(sub_pattern, sub_value, env):
                            return False
                    return True

        def match_dict():
            rest_name = pattern.get(Sym("*"))

            fixed_patterns = pattern.copy()
            remaining_values = value.copy()

            if rest_name is not None:
                assert is_name(rest_name), f"Invalid dict rest pattern @ match_dict(): {rest_name}"
                del fixed_patterns[Sym("*")]

            for key, sub_pattern in fixed_patterns.items():
                if key not in remaining_values:
                    return False
                if not self._match_pattern(sub_pattern, remaining_values[key], env):
                    return False
                del remaining_values[key]

            if rest_name is not None:
                env.define(rest_name, remaining_values)
            return True

        match pattern:
            case Sym("_"):
                return True
            case Sym(name):
                env.define(name, value)
                return True
            case list():
                if not isinstance(value, list): return False
                return match_list()
            case dict():
                if not isinstance(value, dict): return False
                return match_dict()
            case _:
                return pattern == value

class Interpreter:
    def __init__(self):
        self._env = Environment()
        self._custom_rules = {}

    def _import(self, path):
        with open(path, "r") as f: src = f.read()
        module_env = Environment(self._env)
        ast = self.parse(self.scan(src))
        return Evaluator().evaluate(ast, module_env)

    def init_env(self):
        self._env.define(Sym("__builtins"), None)

        self._env.define(Sym("import"), lambda args: self._import(args[0]))

        self._env.define(Sym("eval"), lambda args: Evaluator().evaluate(self.ast(args[0]), self._env))
        self._env.define(Sym("eval_expr"), lambda args: Evaluator().evaluate(args[0], self._env))
        self._env.define(Sym("apply"), lambda args: Evaluator().apply(args[0], args[1]))

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

        self._env.define(Sym("len"), lambda args: len(args[0]))
        self._env.define(Sym("index"), lambda args: args[0][args[1]])
        self._env.define(Sym("slice"), lambda args: args[0][args[1]:args[2]])
        self._env.define(Sym("push"), lambda args: args[0].append(args[1]))
        self._env.define(Sym("pop"), lambda args: args[0].pop())

        self._env.define(Sym("chr"), lambda args: chr(args[0]))
        self._env.define(Sym("ord"), lambda args: ord(args[0]))
        self._env.define(Sym("join"), lambda args: str(args[1]).join(map(str, args[0])))

        self._env.define(Sym("has"), lambda args: args[1] in args[0])
        self._env.define(Sym("keys"), lambda args: list(args[0].keys()))
        self._env.define(Sym("items"), lambda args: [list(e) for e in args[0].items()])
        self._env.define(Sym("copy"), lambda args: args[0].copy())

        self._env.define(Sym("str"), lambda args: str(args[0]))
        self._env.define(Sym("int"), lambda args: int(args[0]))
        self._env.define(Sym("sym"), lambda args: Sym(args[0]))
        self._env.define(Sym("expr"), lambda args: tuple(args))

        self._env.define(Sym("print"), lambda args: print(*args))

        self._env = Environment(self._env)
        return self

    def corelib(self):
        self.walk("""
            __corelib := None;

            #rule {func: [__core_func, EXPRS, do, EXPR, end]}
            #rule {macro: [__core_macro, EXPRS, do, EXPR, end]}

            #rule {scope: [__core_scope, EXPR, end]}

            #rule {qq: [__core_qq, EXPR, end]}

            __core_defmacro := macro name, params_, body do
                qq !name := macro !!params_ do !body end end
            end;
            #rule {defmacro: [__core_defmacro, EXPR, params, EXPRS, do, EXPR, end]}

            __core_qqs := macro expr do qq qq scope !expr end end end end;
            #rule {qqs: [__core_qqs, EXPR, end]}

            __core_deffunc := macro name, params_, body do
                qq !name := func !!params_ do !body end end
            end;
            #rule {deffunc: [__core_deffunc, EXPR, params, EXPRS, do, EXPR, end]}

            #rule {pif: [__core_if, EXPR, then, EXPR, else, EXPR, end]}

            __core_if_macro := macro cnd, thn, elifs, els do scope
                __core_if_expr := pif els == [] then None else els[0] end;
                i := len(elifs) - 1;
                while i >= 0 do
                    [__core_if_elif_cnd, __core_if_elif_thn] := elifs[i];
                    __core_if_expr = qq
                        pif !__core_if_elif_cnd then
                            !__core_if_elif_thn
                        else
                            !__core_if_expr
                        end
                    end;
                    i = i - 1
                end;
                qq pif !cnd then !thn else !__core_if_expr end end
            end end;
            #rule {if: [__core_if_macro, EXPR, then, EXPR, *[elif, EXPR, then, EXPR], +[else, EXPR], end]}

            #rule {match: [__core_match, EXPR, *[case, EXPR, then, EXPR], end]}

            _aif := macro cnd, thn, els do qqs
                pif it := !cnd then !thn else !els end
            end end;
            #rule {aif: [_aif, EXPR, then, EXPR, else, EXPR, end]}

            and := macro a, b do qq aif !a then !b else it end end end;
            or := macro a, b do qq aif !a then it else !b end end end;

            #rule {while: [__core_while, EXPR, do, EXPR, end]}

            __core_for := macro var, coll, body do qqs
                __core_for_coll := !coll;
                __core_for_index := -1;
                while __core_for_index + 1 < len(__core_for_coll) do
                    __core_for_index = __core_for_index + 1;
                    scope
                        !var := __core_for_coll[__core_for_index];
                        !body
                    end
                end
            end end
            #rule {for: [__core_for, EXPR, in, EXPR, do, EXPR, end]}

            #rule {try: [__core_try, EXPR, *[except, EXPR, then, EXPR], end]}
        """)

        self._env = Environment(self._env)
        return self

    def stdlib(self):
        self.walk("""
            __stdlib := None;

            deffunc first params a do a[0] end;
            deffunc rest params a do slice(a, 1, None) end;
            deffunc last params a do a[-1] end;

            deffunc map params a, f do
                b := []; l := len(a);
                i := 0; while i < l do
                    push(b, f(a[i]));
                    i = i + 1
                end;
                b
            end;

            deffunc filter params a, f do
                b := []; l := len(a);
                i := 0; while i < l do
                    if f(a[i]) then push(b, a[i]) end;
                    i = i + 1
                end;
                b
            end;

            deffunc zip params a, b do
                z := []; la := len(a); lb := len(b);
                i := 0; while i < la and i < lb do
                    push(z, [a[i], b[i]]);
                    i = i + 1
                end;
                z
            end;

            deffunc reduce params a, f, init do
                acc := init; l := len(a);
                i := 0; while i < l do
                    acc = f(acc, a[i]);
                    i = i + 1
                end;
                acc
            end;

            deffunc reverse params a do
                b := []; i := len(a) - 1;
                while i >= 0 do
                    push(b, a[i]);
                    i = i - 1
                end;
                b
            end;

            deffunc range params start, stop do
                b := [];
                i := start; while i < stop do
                    push(b, i);
                    i = i + 1
                end;
                b
            end;

            deffunc enumerate params a do
                zip(range(0, len(a)), a)
            end
        """)

        self._env = Environment(self._env)
        return self

    def collect_rules(self, src):
        self._custom_rules = {**self._custom_rules, **RuleCollector(src).collect()}

    def scan(self, src):
        return Scanner(src).tokenize()

    def parse(self, tokens):
        return Parser(tokens, self._custom_rules).parse()

    def ast(self, src):
        self.collect_rules(src)
        return self.parse(self.scan(src))

    def evaluate(self, expr):
        try:
            return Evaluator().evaluate(expr, self._env)
        except ToilException as e: assert False, f"ToilException @ evaluate(): {e.e}"
        except ReturnException: assert False, "Return from top level @ evaluate()"
        except ContinueException: assert False, "Continue at top level @ evaluate()"
        except BreakException: assert False, "Break at top level @ evaluate()"

    def walk(self, src):
        return self.evaluate(self.ast(src))

if __name__ == "__main__":
    import sys

    i = Interpreter().init_env().corelib().stdlib()

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
            result = i.walk(f.read())
        exit(result if isinstance(result, int) else 0)

    if len(sys.argv) > 1:
        if sys.argv[1] == "--repl":
            repl()
        else:
            run(sys.argv[1])

    # Example

    print(i.walk(""" if True then 2 else 3 end """))
    print(i.walk(""" if False then 2 elif True then 3 else 4 end """))
