#! /usr/bin/env python3

class Sym(str):
    def __repr__(self): return super().__repr__()[1:-1]


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
                case "'":
                    self._raw_string()
                case "\"":
                    self._string()
                case c if is_name_first(c):
                    self._name()
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
        return exprs[0] if len(exprs) == 1 else (Sym("seq"), exprs)

    def _define_assign(self):
        return self._binary_right({
            Sym(":="): Sym("define"), Sym("="): Sym("assign")
        }, self._and_or)

    def _and_or(self):
        left = self._not()
        while type(self._current_token()) is Sym and \
                (op := self._current_token()) in (Sym("and"), Sym("or")):
            self._advance()
            right = self._not()
            if op == Sym("and"):
                left = (Sym("if"), left, right, left)
            else:
                left = (Sym("if"), left, left, right)
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
        }, self._unaries)

    def _unaries(self):
        return self._unary({
            Sym("-"): Sym("neg"), Sym("*"): Sym("*")
        }, self._call_index_dot)

    def _call_index_dot(self):
        target = self._primary()
        while type(self._current_token()) is Sym and \
                self._current_token() in (Sym("("), Sym("["), Sym(".")):
            match self._current_token():
                case Sym("("):
                    self._advance()
                    target = (target, self._comma_separated_exprs(Sym(")")))
                case Sym("["):
                    self._advance()
                    index = self._expression()
                    self._consume(Sym("]"))
                    target = (Sym("index"), [target, index])
                case Sym("."):
                    self._advance()
                    assert type(self._current_token()) is Sym, \
                        f"Illegal property @ _call_index_dot(): {self._current_token()}"
                    attr = self._advance()
                    target = (Sym("dot"), [target, str(attr)])
        return target

    def _primary(self):
        match self._current_token():
            case Sym("("): return self._paren()
            case Sym("["): return self._array()
            case Sym("{"): return self._dic()
            case None | bool() | int(): return self._advance()
            case s if type(s) == str: return self._advance()
            case Sym("func"): return self._func()
            case Sym("deffunc"): return self._deffunc()
            case Sym("scope"): return self._scope()
            case Sym("if"): return self._if()
            case Sym("match"): return self._match()
            case Sym("while"): return self._while()
            case Sym("for"): return self._for()
            case Sym("try"): return self._try()
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
                case illegal:
                    assert False, f"Illegal key @ _dic(): {illegal}"

        self._advance()
        dic = {}
        if self._current_token() != Sym("}"):
            _parse_key_value(dic)
            while self._current_token() != Sym("}"):
                self._consume(Sym(","))
                _parse_key_value(dic)
        self._advance()
        return dic

    def _func(self):
        self._advance()
        params = self._comma_separated_exprs(Sym("do"))
        body_expr = self._expression()
        self._consume(Sym("end"))
        return (Sym("func"), params, body_expr)

    def _deffunc(self):
        self._advance()
        name = self._advance()
        assert is_name(name), f"Expected function name @ deffunc: {name}"
        self._consume(Sym("params"))
        params = self._comma_separated_exprs(Sym("do"))
        body_expr = self._expression()
        self._consume(Sym("end"))
        return (Sym("define"), [name, (Sym("func"), params, body_expr)])

    def _scope(self):
        self._advance()
        body_expr = self._expression()
        self._consume(Sym("end"))
        return (Sym("scope"), body_expr)

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
        return (Sym("if"), cond_expr, then_expr, else_expr)

    def _while(self):
        self._advance()
        cond_expr = self._expression()
        self._consume(Sym("do"))
        body_expr = self._expression()
        self._consume(Sym("end"))
        return (Sym("while"), cond_expr, body_expr)

    def _for(self):
        self._advance()
        var_expr = self._expression()
        self._consume(Sym("in"))
        coll_expr = self._expression()
        self._consume(Sym("do"))
        body_expr = self._expression()
        self._consume(Sym("end"))
        return (Sym("scope"), (Sym("seq"), [
            (Sym("define"), [Sym("__for_coll"), coll_expr]),
            (Sym("define"), [Sym("__for_index"), -1]),
            (Sym("while"),
                (Sym("less"), [(Sym("add"), [Sym("__for_index"), 1]), (Sym("len"), [Sym("__for_coll")])]),
                (Sym("seq"), [
                    (Sym("assign"), [Sym("__for_index"), (Sym("add"), [Sym("__for_index"), 1])]),
                    (Sym("scope"), (Sym("seq"), [
                        (Sym("define"), [var_expr, (Sym("index"), [Sym("__for_coll"), Sym("__for_index")])]),
                        body_expr
                    ]))
                ])
            )
        ]))

    def _try(self):
        self._advance()
        body_expr = self._expression()
        clauses = []
        while self._current_token() == Sym("except"):
            self._advance()
            cond_expr = self._expression()
            self._consume(Sym("then"))
            except_expr = self._expression()
            clauses.append((cond_expr, except_expr))
        self._consume(Sym("end"))
        return (Sym("try"), body_expr, clauses)

    def _match(self):
        self._advance()
        val_expr = self._expression()
        cases = []
        while self._current_token() == Sym("case"):
            self._advance()
            pattern = self._expression()
            self._consume(Sym("then"))
            body_expr = self._expression()
            cases.append((pattern, body_expr))
        self._consume(Sym("end"))
        return (Sym("match"), val_expr, cases)

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
        content = "__builtins__" if Sym("__builtins__") in self._vars else \
                  "__stdlib__" if Sym("__stdlib__") in self._vars else \
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
            case (Sym("ast"), [expr]):
                return expr
            case (Sym("define"), [left_expr, right_expr]):
                return self._evaluate_define(left_expr, right_expr, env)
            case (Sym("assign"), [left_expr, right_expr]):
                return self._evaluate_assign(left_expr, right_expr, env)
            case (Sym("seq"), exprs):
                return self._evaluate_seq(exprs, env)
            case (Sym("if"), cond_expr, then_expr, else_expr):
                return self._evaluate_if(cond_expr, then_expr, else_expr, env)
            case (Sym("match"), val_expr, cases):
                return self._evaluate_match(val_expr, cases, env)
            case (Sym("while"), cond_expr, body_expr):
                return self._evaluate_while(cond_expr, body_expr, env)
            case (Sym("break"), args):
                assert len(args) <= 1, f"Break takes zero or one argument @ evaluate(): {args}"
                raise BreakException(self.evaluate(args[0], env) if args else None)
            case (Sym("continue"), args):
                assert len(args) == 0, f"Continue takes no arguments @ evaluate(): {args}"
                raise ContinueException()
            case (Sym("func"), params, body):
                return (Sym("closure"), params, body, env)
            case (Sym("return"), args):
                assert len(args) <= 1, f"Return takes zero or one argument @ evaluate(): {args}"
                raise ReturnException(self.evaluate(args[0], env) if args else None)
            case (Sym("try"), body_expr, clauses):
                return self._evaluate_try(body_expr, clauses, env)
            case (Sym("raise"), args):
                assert len(args) <= 1, f"Raise takes zero or one argument @ evaluate(): {args}"
                raise ToilException(self.evaluate(args[0], env) if args else None)
            case (Sym("scope"), expr):
                return self.evaluate(expr, Environment(env))
            case (Sym("dot"), [target, attr]):
                return self._evaluate_dot(target, attr, env)
            case (op_expr, args_expr) if isinstance(expr, tuple):
                return self._eval_op(op_expr, args_expr, env)
            case unexpected:
                assert False, f"Unexpected expression @ evaluate(): {unexpected}"

    def _evaluate_define(self, left_expr, right_expr, env):
        right_val = self.evaluate(right_expr, env)
        if self._match_pattern(left_expr, right_val, env):
            return right_val
        assert False, f"Doesn't match @ _evaluate_define(): {left_expr}, {right_val}"

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
                        assert False, f"Illegal indexing @ _evaluate_assign(): {coll_val}"
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

    def _evaluate_match(self, val_expr, cases, env):
        val = self.evaluate(val_expr, env)
        for pattern, body_expr in cases:
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

    def _evaluate_try(self, body_expr, clauses, env):
        try:
            return self.evaluate(body_expr, env)
        except ToilException as toil_exception:
            for cond_expr, except_expr in clauses:
                if self._match_pattern(cond_expr, toil_exception.e, env):
                    return self.evaluate(except_expr, env)
            raise toil_exception

    def _evaluate_dot(self, target, attr, env):
        target_val = self.evaluate(target, env)
        match target_val:
            case dict() if attr in target_val:
                attr_val = target_val[attr]
                match attr_val:
                    case (Sym("closure"), [Sym("self"), *_], _, _):
                        return lambda args: self.apply(attr_val, [target_val] + args)
                return attr_val

        attr_val = env.val(attr)
        match attr_val:
            case c if callable(c):
                return lambda args: c([target_val] + args)
            case (Sym("closure"), _, _, _):
                return lambda args: self.apply(attr_val, [target_val] + args)

    def _eval_op(self, op_expr, args_expr, env):
        op_val = self.evaluate(op_expr, env)
        args_val = [self.evaluate(arg, env) for arg in args_expr]
        return self.apply(op_val, args_val)

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
                assert False, f"Illegal operator @ apply(): {op_val}"

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

    def _import(self, path):
        with open(path, "r") as f: src = f.read()
        module_env = Environment(self._env)
        ast = self.parse(self.scan(src))
        return Evaluator().evaluate(ast, module_env)

    def init_env(self):
        self._env.define(Sym("__builtins__"), None)

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

        self._env.define(Sym("str"), lambda args: str(args[0]))
        self._env.define(Sym("int"), lambda args: int(args[0]))
        self._env.define(Sym("chr"), lambda args: chr(args[0]))
        self._env.define(Sym("ord"), lambda args: ord(args[0]))
        self._env.define(Sym("join"), lambda args: str(args[1]).join(map(str, args[0])))

        self._env.define(Sym("has"), lambda args: args[1] in args[0])
        self._env.define(Sym("keys"), lambda args: list(args[0].keys()))
        self._env.define(Sym("items"), lambda args: [list(e) for e in args[0].items()])
        self._env.define(Sym("copy"), lambda args: args[0].copy())

        self._env.define(Sym("sym"), lambda args: Sym(args[0]))
        self._env.define(Sym("expr"), lambda args: tuple(args))

        self._env.define(Sym("print"), lambda args: print(*args))

        self._env = Environment(self._env)
        return self

    def stdlib(self):
        self.go(""" __stdlib__ := None """)
        self.go("""
            deffunc first params a do a[0] end;
            deffunc rest params a do slice(a, 1, None) end;
            deffunc last params a do a[-1] end
        """)
        self.go("""
            deffunc map params a, f do
                b := []; l := len(a);
                i := 0; while i < l do
                    push(b, f(a[i]));
                    i = i + 1
                end;
                b
            end
        """)
        self.go("""
            deffunc filter params a, f do
                b := []; l := len(a);
                i := 0; while i < l do
                    if f(a[i]) then push(b, a[i]) end;
                    i = i + 1
                end;
                b
            end
        """)
        self.go("""
            deffunc zip params a, b do
                z := []; la := len(a); lb := len(b);
                i := 0; while i < la and i < lb do
                    push(z, [a[i], b[i]]);
                    i = i + 1
                end;
                z
            end
        """)
        self.go("""
            deffunc reduce params a, f, init do
                acc := init; l := len(a);
                i := 0; while i < l do
                    acc = f(acc, a[i]);
                    i = i + 1
                end;
                acc
            end
        """)
        self.go("""
            deffunc reverse params a do
                b := []; i := len(a) - 1;
                while i >= 0 do
                    push(b, a[i]);
                    i = i - 1
                end;
                b
            end
        """)
        self.go("""
            deffunc range params start, stop do
                b := [];
                i := start; while i < stop do
                    push(b, i);
                    i = i + 1
                end;
                b
            end
        """)
        self.go("""
            deffunc enumerate params a do
                zip(range(0, len(a)), a)
            end
        """)

        self._env = Environment(self._env)
        return self

    def scan(self, src):
        return Scanner(src).tokenize()

    def parse(self, tokens):
        return Parser(tokens).parse()

    def ast(self, src):
        return self.parse(self.scan(src))

    def evaluate(self, expr):
        try:
            return Evaluator().evaluate(expr, self._env)
        except ToilException as e: assert False, f"ToilException @ evaluate(): {e.e}"
        except ReturnException: assert False, "Return from top level @ evaluate()"
        except ContinueException: assert False, "Continue at top level @ evaluate()"
        except BreakException: assert False, "Break at top level @ evaluate()"

    def go(self, src):
        return self.evaluate(self.ast(src))

if __name__ == "__main__":
    import sys

    i = Interpreter().init_env().stdlib()

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

    print(i.go(""" ast(if True then 2 else 3 end) """)) # -> (if, True, 2, 3)
    print(i.go(""" expr(sym("if"), True, 2, 3) """)) # -> (if, True, 2, 3)
    print(i.go(""" eval_expr(expr(sym("if"), True, 2, 3)) """)) # -> 2

    print(i.go(""" ast(add(2, 3)) """)) # -> (add, [2, 3])
    print(i.go(""" expr(sym("add"), [2, 3]) """)) # -> (add, [2, 3])
    print(i.go(""" eval_expr(expr(sym("add"), [2, 3])) """)) # -> 5

    print(i.go(""" ast(
        a := 2;
        b := 3;
        if a == b then a + b else a * b end
    ) """)) # -> (seq, [(define, [a, 2]), (define, [b, 3]), (if, (equal, [a, b]), (add, [a, b]), (mul, [a, b]))])
    print(i.go("""
        expr(sym("seq"), [
            expr(sym("define"), [sym("a"), 2]),
            expr(sym("define"), [sym("b"), 3]),
            expr(sym("if"),
                expr(sym("equal"), [sym("a"), sym("b")]),
                expr(sym("add"), [sym("a"), sym("b")]),
                expr(sym("mul"), [sym("a"), sym("b")])
            )
        ])
    """)) # -> (seq, [(define, [a, 2]), (define, [b, 3]), (if, (equal, [a, b]), (add, [a, b]), (mul, [a, b]))])
    print(i.go(""" eval_expr(
        expr(sym("seq"), [
            expr(sym("define"), [sym("a"), 2]),
            expr(sym("define"), [sym("b"), 3]),
            expr(sym("if"),
                expr(sym("equal"), [sym("a"), sym("b")]),
                expr(sym("add"), [sym("a"), sym("b")]),
                expr(sym("mul"), [sym("a"), sym("b")])
            )
        ])
    ) """)) # -> 6
