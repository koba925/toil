#! /usr/bin/env python3

import sys
sys.setrecursionlimit(200000)

from toil import Interpreter

i = Interpreter().init_env().stdlib()

i.walk(r"""
    def isalpha(c) do
       type(c) == 'str' and ('a' <= c and c <= 'z') or ('A' <= c and c <= 'Z')
    end;
    def isdigit(c) do type(c) == 'str' and '0' <= c and c <= '9' end;
    def isalnum(c) do isalpha(c) or isdigit(c) end;
    def isspace(c) do c == ' ' or c == "\n" end;

    def is_ident_first(c) do isalpha(c) or c == '_' end;
    def is_ident_rest(c) do isalnum(c) or c == '_' end;
    def is_ident(s) do is_ident_first(s[0]) end
""")

i.walk(r"""
    defclass Scanner(src) do
        self._src = src;
        self._pos = 0;
        self._tokens = [];

        defmethod tokenize do
            # print(src)
            while True do
                while self._current_char().isspace() do self._advance() end;

                if self._current_char() == '#' then
                    while not self._current_char().in("\n", '$EOF')
                         do self._advance()
                    end;
                    continue()
                end;

                ch := self._current_char();
                if ch == '$EOF' then self._tokens.push(Ident('$EOF')); break()
                elif ch.isdigit() then self._number()
                elif ch == "'" then self._raw_string()
                elif ch == '"' then self._string()
                elif ch.is_ident_first() then self._ident()
                elif ch == '-' then self._two_char_operator('>')
                elif ch.in('=!<>:') then self._two_char_operator('=')
                elif ch.in('+*/%()[]{}.,;') then
                    self._tokens.push(Ident(ch)); self._advance()
                else raise('Invalid character @ tokenize: ' + ch)
                end
            else self._tokens end
        end;

        defmethod _number do
            start := self._pos;
            while self._current_char().isdigit() do
                self._advance()
            end;
            self._tokens.push(int(self._src.slice(start, self._pos)))
        end;

        defmethod _raw_string do
            self._advance();
            start := self._pos;
            while (c := self._current_char()) != "'" do
                if c == '$EOF' then raise('Unterminated string @ _raw_string()') end;
                self._advance()
            end;
            self._tokens.push(self._src.slice(start, self._pos));
            self._advance()
        end;

        defmethod _string do
            self._advance();
            s := [];
            while (ch := self._current_char()) != '"' do
                if ch == '$EOF' then raise('Unterminated string @ _string()') end;
                if ch == '\' then
                    self._advance();
                    ch := self._current_char();
                    if ch == '$EOF' then raise('Unterminated string @ _string()') end;
                    match ch
                        case 'n' then s.push("\n")
                        case _ then s.push(ch)
                    end
                else
                    s.push(ch)
                end;
                self._advance()
            end;
            self._advance();
            self._tokens.push(s.join(''))
        end;

        defmethod _ident do
            start := self._pos;
            self._advance();
            while self._current_char().is_ident_rest() do
                self._advance()
            end;
            token := self._src.slice(start, self._pos);
            match token
                case 'None' then self._tokens.push(None)
                case 'True' then self._tokens.push(True)
                case 'False' then self._tokens.push(False)
                case _ then self._tokens.push(Ident(token))
            end
        end;

        defmethod _two_char_operator(successors) do
            start := self._pos;
            self._advance();
            if self._current_char().in(successors) then
                self._advance()
            end;
            self._tokens.push(Ident(self._src.slice(start, self._pos)))
        end;

        defmethod _advance do self._pos = self._pos + 1 end;

        defmethod _current_char do
            if self._pos < self._src.len() then
                self._src[self._pos]
            else
                '$EOF'
            end
        end
    end
""")

i.walk(r"""
    defclass Parser(tokens) do
        self._tokens = tokens;
        self._pos = 0;

        defmethod parse do
            # print(self._tokens);
            expr := self._expression();
            if self._current() != Ident('$EOF') then
                raise('Extra token @ parse: ' + str(self._current()))
            end;
            expr
        end;

        defmethod _expression do
            self._sequence()
        end;

        defmethod _sequence do
            exprs := [self._define_assign()];
            while self._current() == Ident(';') do
                self._current_and_advance();
                exprs.push(self._define_assign())
            end;
            if exprs.len() == 1 then exprs[0] else tuple(Ident('seq'), exprs) end
        end;

        defmethod _define_assign do
            self._binary_right({
                ':=': Ident('define'), '=': Ident('assign')
            }, self._arrow)
        end;

        defmethod _arrow do
            left := self._and_or();
            if self._current() == Ident('->') then
                self._current_and_advance();
                right := self._arrow();
                params_ := if left.type() == 'list' then left else [left] end;
                tuple(Ident('func'), [params_, right])
            else
                left
            end
        end;

        defmethod _and_or do
            self._binary_right({
                'and': Ident('and'), 'or': Ident('or')
            }, self._not)
        end;

        defmethod _not do
            self._unary({'not': Ident('not')}, self._comparison)
        end;

        defmethod _comparison do
            self._binary_left({
                '==': Ident('equal'), '!=': Ident('not_equal'),
                '<': Ident('less'), '>': Ident('greater'),
                '<=': Ident('less_equal'), '>=': Ident('greater_equal')
            }, self._add_sub)
        end;

        defmethod _add_sub do
            self._binary_left({
                '+': Ident('add'), '-': Ident('sub')
            }, self._mul_div_mod)
        end;

        defmethod _mul_div_mod do
            self._binary_left({
                '*': Ident('mul'), '/': Ident('div'), '%': Ident('mod')
            }, self._unaries)
        end;

        defmethod _unaries do
            self._unary({
                '-': Ident('neg'), '+': Ident('+'), '*': Ident('*')
            }, self._call_index_dot)
        end;

        defmethod _call_index_dot do
            target := self._primary();
            while (op := self._current()).in([Ident('('), Ident('['), Ident('.')]) do
                if op == Ident('(') then
                    self._current_and_advance();
                    target = tuple(target, self._comma_separated_exprs(Ident(')')));
                    self._consume(Ident(')'))
                elif op == Ident('[') then
                    self._current_and_advance();
                    target = tuple(Ident('index'), [target, self._expression()]);
                    self._consume(Ident(']'))
                else
                    self._current_and_advance();
                    attr_name := self._current_and_advance();
                    if attr_name.type() != 'Ident' then
                        raise('Invalid attribute @ _call_index_dot(): ' + str(attr_name))
                    end;
                    target = tuple(Ident('dot'), [target, str(attr_name)])
                end
            end;
            target
        end;

        defmethod _primary do
            match self._current()
                case None then self._current_and_advance()
                case bool(_) or int(_) or str(_) then self._current_and_advance()
                case Ident('(') then self._group()
                case Ident('[') then self._list()
                case Ident('{') then self._dict()
                case Ident('func') then self._func()
                case Ident('def') then self._def()
                case Ident('scope') then self._scope()
                case Ident('if') then self._if()
                case Ident('match') then self._match()
                case Ident('while') then self._while()
                case Ident('for') then self._for()
                case Ident('try') then self._try()
                case Ident('defclass') then self._defclass()
                case Ident('defmethod') then self._defmethod()
                case Ident(name) then
                    if name.is_ident() then
                        self._current_and_advance()
                    else
                        raise('Unexpected token @ primary(): ' + str(self._current()))
                    end
                case _ then raise('Unexpected token: @ primary(): ' + str(self._current()))
            end
        end;

        defmethod _group do
            self._current_and_advance();
            expr := self._expression();
            self._consume(Ident(')'));
            expr
        end;

        defmethod _list do
            self._current_and_advance();
            exprs := self._comma_separated_exprs(Ident(']'));
            self._consume(Ident(']'));
            exprs
        end;

        defmethod _dict do
            def _parse_key_value(dic) do
                match self._current()
                    case Ident('*') then
                        self._current_and_advance();
                        dic['*'] = self._current_and_advance()
                    case Ident(key) then
                        self._current_and_advance();
                        if self._current() == Ident(':') then
                            self._current_and_advance();
                            dic[key] = self._expression()
                        else
                            dic[key] = Ident(key)
                        end
                    case str(key) then
                        self._current_and_advance();
                        self._consume(Ident(':'));
                        dic[key] = self._expression()
                    case _ then
                        raise('Invalid key @ _dict(): ' + str(self._current()))
                end
            end;

            self._current_and_advance();
            dic := {};
            if self._current() != Ident('}') then
                _parse_key_value(dic);
                while self._current() != Ident('}') do
                    self._consume(Ident(','));
                    _parse_key_value(dic)
                end
            end;
            self._current_and_advance();
            dic
        end;

        defmethod _func do
            self._current_and_advance();
            params := self._comma_separated_exprs(Ident('do'));
            self._consume(Ident('do'));
            body_expr := self._expression();
            self._consume(Ident('end'));
            tuple(Ident('func'), [params, body_expr])
        end;

        defmethod _def do
            self._current_and_advance();
            call_expr := self._expression();
            self._consume(Ident('do'));
            body_expr := self._expression();
            self._consume(Ident('end'));
            match call_expr
                case tuple(name, args) then
                    tuple(Ident('define'), [name, tuple(Ident('func'), [args, body_expr])])
                case Ident(name) then
                    tuple(Ident('define'), [call_expr, tuple(Ident('func'), [[], body_expr])])
                case _ then
                    raise('Invalid def syntax @ _def(): ' + str(call_expr))
            end
        end;

        defmethod _scope do
            self._current_and_advance();
            body_expr := self._expression();
            self._consume(Ident('end'));
            tuple(Ident('scope'), [body_expr])
        end;

        defmethod _if do
            self._current_and_advance();
            cond_expr := self._expression();
            self._consume(Ident('then'));
            then_expr := self._expression();
            else_expr := None;
            if self._current() == Ident('elif') then
                else_expr = self._if()
            elif self._current() == Ident('else') then
                self._current_and_advance();
                else_expr = self._expression();
                self._consume(Ident('end'))
            else
                else_expr = None;
                self._consume(Ident('end'))
            end;
            tuple(Ident('if'), [cond_expr, then_expr, else_expr])
        end;

        defmethod _match do
            self._current_and_advance();
            val_expr := self._expression();
            cases := [];
            while self._current() == Ident('case') do
                self._current_and_advance();
                pattern := self._expression();
                self._consume(Ident('then'));
                body_expr := self._expression();
                cases.push(tuple(pattern, body_expr))
            end;
            self._consume(Ident('end'));
            tuple(Ident('match'), [val_expr, cases])
        end;

        defmethod _while do
            self._current_and_advance();
            cond_expr := self._expression();
            self._consume(Ident('do'));
            body_expr := self._expression();
            then_expr := if self._current() == Ident('then') then
                self._current_and_advance();
                [self._expression()]
            else [] end;
            else_expr := if self._current() == Ident('else') then
                self._current_and_advance();
                [self._expression()]
            else [] end;
            self._consume(Ident('end'));
            tuple(Ident('while'), [cond_expr, body_expr, then_expr, else_expr])
        end;

        defmethod _try do
            self._current_and_advance();
            body_expr := self._expression();
            clauses := [];
            while self._current() == Ident('except') do
                self._current_and_advance();
                cond_expr := self._expression();
                self._consume(Ident('then'));
                except_expr := self._expression();
                clauses.push([cond_expr, except_expr])
            end;
            self._consume(Ident('end'));
            tuple(Ident('try'), [body_expr, clauses])
        end;

        defmethod _for do
            self._current_and_advance();
            var_expr := self._expression();
            self._consume(Ident('in'));
            coll_expr := self._expression();
            self._consume(Ident('do'));
            body_expr := self._expression();
            then_expr := if self._current() == Ident('then') then
                self._current_and_advance();
                [self._expression()]
            else [] end;
            else_expr := if self._current() == Ident('else') then
                self._current_and_advance();
                [self._expression()]
            else [] end;
            self._consume(Ident('end'));
            tuple(Ident('for'), [var_expr, coll_expr, body_expr, then_expr, else_expr])
        end;

        defmethod _defclass do
            self._current_and_advance();
            call_expr := self._expression();
            self._consume(Ident('do'));
            body_expr := self._expression();
            self._consume(Ident('end'));

            match call_expr
                case tuple(name, args) then
                    tuple(Ident('define'), [
                        name,
                        tuple(Ident('func'), [
                            args,
                            tuple(Ident('seq'), [
                                tuple(Ident('define'), [Ident('self'), {}]),
                                body_expr,
                                Ident('self')
                            ])
                        ])
                    ])
                case Ident(name) then
                    tuple(Ident('define'), [
                        call_expr,
                        tuple(Ident('func'), [
                            [],
                            tuple(Ident('seq'), [
                                tuple(Ident('define'), [Ident('self'), {}]),
                                body_expr,
                                Ident('self')
                            ])
                        ])
                    ])
                case _ then
                    raise('Invalid defclass syntax @ _defclass(): ' + str(call_expr))
            end
        end;

        defmethod _defmethod do
            self._current_and_advance();
            call_expr := self._expression();
            self._consume(Ident('do'));
            body_expr := self._expression();
            self._consume(Ident('end'));

            match call_expr
                case tuple(name, args) then
                    tuple(Ident('assign'), [
                        tuple(Ident('dot'), [Ident('self'), str(name)]),
                        tuple(Ident('func'), [[Ident('self')] + args, body_expr])
                    ])
                case Ident(name) then
                    tuple(Ident('assign'), [
                        tuple(Ident('dot'), [Ident('self'), str(name)]),
                        tuple(Ident('func'), [[Ident('self')], body_expr])
                    ])
                case _ then
                    raise('Invalid defmethod syntax @ _defmethod(): ' + str(call_expr))
            end
        end;

        defmethod _binary_left(ops, sub_elem) do
            left := sub_elem();
            while type(op := self._current()) == 'Ident' and str(op).in(ops) do
                self._current_and_advance();
                right := sub_elem();
                left = tuple(ops[str(op)], [left, right])
            end;
            left
        end;

        defmethod _binary_right(ops, sub_elem) do
            left := sub_elem();
            if type(op := self._current()) == 'Ident' and str(op).in(ops) then
                self._current_and_advance();
                right := self._binary_right(ops, sub_elem);
                tuple(ops[str(op)], [left, right])
            else
                left
            end
        end;

        defmethod _unary(ops, sub_elem) do
            if type(op := self._current()) == 'Ident' and str(op).in(ops) then
                self._current_and_advance();
                tuple(ops[str(op)], [self._unary(ops, sub_elem)])
            else
                sub_elem()
            end
        end;

        defmethod _comma_separated_exprs(terminator) do
            cse := [];
            if self._current() != terminator then
                cse.push(self._expression());
                while self._current() == Ident(',') do
                    self._current_and_advance();
                    cse.push(self._expression())
                end
            end;
            cse
        end;

        defmethod _consume(expected) do
            if self._current() == expected then
                self._current_and_advance()
            else
                raise('Expected ' + str(expected) + ' @ consume: '
                      + str(self._current()))
            end
        end;

        defmethod _current do self._tokens[self._pos] end;

        defmethod _current_and_advance do
            self._pos = self._pos + 1;
            self._tokens[self._pos - 1]
        end
    end
""")

i.walk(r"""
    defclass Environment(parent) do
        self._parent = parent;
        self._vars = {};

        defmethod define(name, val) do
            self._vars[name] = val
        end;

        defmethod lookup(name) do
            if name.in(self._vars) then
                self._vars
            elif self._parent != None then
                self._parent.lookup(name)
            else
                None
            end
        end;

        defmethod val(name) do
            vars := self.lookup(name);
            if vars == None then raise('Undefined variable @ val: ' + name) end;
            vars[name]
        end;

        defmethod assign(name, val) do
            vars := self.lookup(name);
            if vars == None then raise('Undefined variable @ assign: ' + name) end;
            vars[name] = val
        end
    end
""")

i.walk(r"""
    defclass Evaluator do
        defmethod eval(expr, env) do
            # print(expr);
            match expr
                case None then expr
                case bool(_) or int(_) or str(_) then expr
                case list(_) then expr.map(e -> self.eval(e, env))
                case dict(_) then
                    expr.items().map([[k, v]] -> [k, self.eval(v, env)]).dict()
                case Ident(name) then env.val(name)
                case tuple(Ident('quote'), [expr]) then
                    expr
                case tuple(Ident('func'), [params, body_expr]) then
                    tuple(Ident('closure'), [params, body_expr, env, None])
                case tuple(Ident('return'), args) then
                    raise(['ReturnException', self._eval_optional_arg(args, env)])
                case tuple(Ident('dot'), [target_expr, attr_expr]) then
                    self._dot(target_expr, attr_expr, env)
                case tuple(Ident('scope'), [body_expr]) then
                    self.eval(body_expr, Environment(env))
                case tuple(Ident('define'), [left_expr, right_expr]) then
                    self._define(left_expr, right_expr, env)
                case tuple(Ident('assign'), [left_expr, right_expr]) then
                    self._assign(left_expr, right_expr, env)
                case tuple(Ident('seq'), exprs) then
                    self._seq(exprs, env)
                case tuple(Ident('if'), [cond_expr, then_expr, else_expr]) then
                    self._if(cond_expr, then_expr, else_expr, env)
                case tuple(Ident('match'), [val_expr, cases]) then
                    self._match(val_expr, cases, env)
                case tuple(Ident('and'), [left_expr, right_expr]) then
                    self.eval(left_expr, env) and self.eval(right_expr, env)
                case tuple(Ident('or'), [left_expr, right_expr]) then
                    self.eval(left_expr, env) or self.eval(right_expr, env)
                case tuple(Ident('while'), [cond_expr, body_expr, then_expr, else_expr]) then
                    self._while(cond_expr, body_expr, then_expr, else_expr, env)
                case tuple(Ident('for'), [var_expr, coll_expr, body_expr, then_expr, else_expr]) then
                    self._for(var_expr, coll_expr, body_expr, then_expr, else_expr, env)
                case tuple(Ident('try'), [body_expr, clauses]) then
                    self._try(body_expr, clauses, env)
                case tuple(Ident('raise'), [val]) then
                    raise(self.eval(val, env))
                case tuple(Ident('continue'), []) then
                    raise(['ContinueException'])
                case tuple(Ident('break'), []) then
                    raise(['BreakException'])
                case tuple(op_expr, args_expr) then
                    self._op(op_expr, args_expr, env)
            end
        end;

        defmethod _dot(target_expr, attr_name, env) do
            target_val := self.eval(target_expr, env);
            if target_val.type() == 'dict' and attr_name.in(target_val) then
                attr_val := target_val[attr_name];
                match attr_val
                    case tuple(Ident('closure'), [[Ident('self'), *_], _, _, _]) then
                        tuple(Ident('hostfunc'), args ->
                            self.apply(attr_val, [target_val] + args)
                        )
                    case _ then
                        attr_val
                end
            else
                func_val := env.val(attr_name);
                tuple(Ident('hostfunc'), args ->
                    self.apply(func_val, [target_val] + args)
                )
            end
        end;

        defmethod _define(left_expr, right_expr, env) do
            right_val := self.eval(right_expr, env);
            match left_expr
                case Ident(name) then
                    old_val_dict := env.lookup(name);
                    if old_val_dict != None then
                        right_val = self._overload_closure(right_val, old_val_dict, name)
                    end
            end;
            if self._match_pattern(left_expr, right_val, env) then
                right_val
            else
                raise('Pattern mismatch @ _define(): ' + str(left_expr) + ', ' + str(right_val))
            end
        end;

        defmethod _assign(left_expr, right_expr, env) do
            def _set_val(coll_expr, index_expr, right_val) do
                coll_val := self.eval(coll_expr, env);
                index_val := self.eval(index_expr, env);
                right_val = self._overload_closure(right_val, coll_val, index_val);
                coll_val[index_val] = right_val
            end;

            right_val := self.eval(right_expr, env);
            match left_expr
                case Ident(name) then
                    env.assign(name, right_val)
                case tuple(Ident('index'), [coll_expr, index_expr]) then
                        _set_val(coll_expr, index_expr, right_val)
                case tuple(Ident('dot'), [coll_expr, index_expr]) then
                        _set_val(coll_expr, index_expr, right_val)
                case _ then
                    raise('Invalid assign target @ _assign: ' + str(left_expr))
            end
        end;

        defmethod _overload_closure(right_val, coll_val, index_val) do
            if type(coll_val) != 'dict' or type(index_val) != 'str' then
                return(right_val)
            end;
            if index_val.in(coll_val) then
                old_val := coll_val[index_val];
                match [right_val, old_val]
                    case [
                        tuple(Ident('closure'), [pat, body, env_, _]),
                        tuple(Ident('closure'), _)
                    ] then
                        return(tuple(Ident('closure'), [pat, body, env_, old_val]))
                end
            end;
            right_val
        end;

        defmethod _seq(exprs, env) do
            for expr in exprs do
                val := self.eval(expr, env)
            then val end
        end;

        defmethod _if(cond_expr, then_expr, else_expr, env) do
            if self.eval(cond_expr, env) then
                self.eval(then_expr, env)
            else
                self.eval(else_expr, env)
            end
        end;

        defmethod _match(val_expr, cases, env) do
            val := self.eval(val_expr, env);
            for tuple(pattern, body_expr) in cases do
                if self._match_pattern(pattern, val, env) then
                    return(self.eval(body_expr, env))
                end
            end;
            None
        end;

        defmethod _while(cond_expr, body_expr, then_expr, else_expr, env) do
            while self.eval(cond_expr, env) do
                try
                    self.eval(body_expr, env)
                except ['ContinueException'] then continue()
                except ['BreakException'] then break()
                end
            then
                self._eval_optional_arg(then_expr, env)
            else
                self._eval_optional_arg(else_expr, env)
            end
        end;

        defmethod _for(
            var_expr, coll_expr, body_expr, then_expr, else_expr, env)
        do
            coll_val := self.eval(coll_expr, env);
            for val in coll_val do
                if not self._match_pattern(var_expr, val, env) then
                    raise('Pattern mismatch @ _for: ' + str(var_expr) + ', ' + str(val))
                end;
                try
                    self.eval(body_expr, env)
                except ['ContinueException'] then continue()
                except ['BreakException'] then break()
                end
            then
                self._eval_optional_arg(then_expr, env)
            else
                self._eval_optional_arg(else_expr, env)
            end
        end;

        defmethod _eval_optional_arg(args, env) do
            if args.len() == 0 then None else self.eval(args[0], env) end
        end;

        defmethod _try(body_expr, clauses, env) do
            try
                self.eval(body_expr, env)
            except e then
                match e
                    case ['ReturnException', _] then raise(e)
                    case ['ContinueException'] then raise(e)
                    case ['BreakException'] then raise(e)
                    case _ then None
                end;
                for [cond_expr, except_expr] in clauses do
                    if self._match_pattern(cond_expr, e, env) then
                        return(self.eval(except_expr, env))
                    end
                end;
                raise(e)
            end
        end;

        defmethod _op(op_expr, args_expr, env) do
            op_val := self.eval(op_expr, env);
            args_val := args_expr.map(arg -> self.eval(arg, env));
            self.apply(op_val, args_val)
        end;

        defmethod apply(op_val, args_val) do
            match op_val
                case tuple(Ident('hostfunc'), f) then f(args_val)
                case tuple(Ident('closure'), [params_, body_expr, closure_env, fallback]) then
                    new_env := Environment(closure_env);
                    if self._match_pattern(params_, args_val, new_env) then
                        try
                            return(self.eval(body_expr, new_env))
                        except ['ReturnException', val] then
                            return(val)
                        end
                    end;
                    if fallback != None then
                        return(self.apply(fallback, args_val))
                    end;
                    raise('Pattern mismatch @ apply: ' + str(params_) + ', ' + str(args_val))
                case _ then raise('Invalid operator @ apply: ' + str(op_val))
            end
        end;

        defmethod _match_pattern(pattern, value, env) do
            def _match_list do
                i := 0; lpat := pattern.len(); lval := value.len();

                no_star := True;
                while i < lpat do
                    sub_pat := pattern[i];
                    match sub_pat
                        case tuple(Ident('*'), [Ident(rest_name)]) then
                            no_star = False; break()
                    end;
                    if i >= lval then return(False) end;
                    sub_val := value[i];
                    if not self._match_pattern(sub_pat, sub_val, env) then
                        return(False)
                    end;
                    i = i + 1
                end;
                if no_star then return(i == lval) end;

                lrest := lval - lpat + 1;
                if lrest < 0 then return(False) end;
                env.define(rest_name, value.slice(i, i + lrest));
                i = i + 1;

                while i < lpat do
                    sub_pat := pattern[i];
                    match sub_pat
                        case tuple(Ident('*'), [Ident(rest_name)]) then return(False)
                    end;
                    sub_val := value[i + lrest - 1];
                    if not self._match_pattern(sub_pat, sub_val, env) then
                        return(False)
                    end;
                    i = i + 1
                end;

                True
            end;

            def _match_dict do
                tmp_pat := pattern.copy(); rest_name := None; tmp_val := value.copy();
                if '*'.in(pattern) then
                    tmp_pat.pop('*');
                    rest_name = pattern['*']
                end;

                for [key, sub_pat] in tmp_pat.items() do
                    if not key.in(tmp_val) then return(False) end;
                    if not self._match_pattern(sub_pat, tmp_val[key], env) then
                        return(False)
                    end;
                    tmp_val.pop(key)
                end;

                if rest_name != None then
                    env.define(str(rest_name), tmp_val)
                end;
                True
            end;

            match pattern
                case Ident(name) then env.define(name, value); True
                case list(_) then value.type() == 'list' and _match_list()
                case dict(_) then value.type() == 'dict' and _match_dict()
                case tuple(Ident('or'), [left_pat, right_pat]) then
                    self._match_pattern(left_pat, value, env) or
                    self._match_pattern(right_pat, value, env)
                case tuple(Ident('Ident'), [name_pat]) then
                    value.type() == 'Ident' and
                    self._match_pattern(name_pat, str(value), env)
                case tuple(Ident('tuple'), expr_pats) then
                    value.type() == 'tuple' and expr_pats.len() == value.len() and
                    zip(expr_pats, value).all(
                        [[p, v]] -> self._match_pattern(p, v, env)
                    )
                case tuple(Ident(typ), [val_pat]) then
                    value.type() == typ and self._match_pattern(val_pat, value, env)
                case _ then
                    pattern.type() == value.type() and pattern == value
            end
        end
    end
""")

i.walk(r"""
    defclass Interpreter do
        self._env = Environment(None);

        defmethod init_env do
            self._env = Environment(None);
            self._builtins();
            self
        end;

        defmethod _builtins do
            def make_hostfunc(f) do tuple(Ident('hostfunc'), args -> f(args)) end;

            self._env.define('__builtins', None);

            self._env.define('add', tuple(Ident('hostfunc'), args -> args[0] + args[1]));
            self._env.define('sub', tuple(Ident('hostfunc'), args -> args[0] - args[1]));
            self._env.define('mul', tuple(Ident('hostfunc'), args -> args[0] * args[1]));
            self._env.define('div', tuple(Ident('hostfunc'), args -> args[0] / args[1]));
            self._env.define('mod', tuple(Ident('hostfunc'), args -> args[0] % args[1]));
            self._env.define('neg', tuple(Ident('hostfunc'), args -> -args[0]));

            self._env.define('equal', tuple(Ident('hostfunc'), args -> args[0] == args[1]));
            self._env.define('not_equal', tuple(Ident('hostfunc'), args -> args[0] != args[1]));
            self._env.define('less', tuple(Ident('hostfunc'), args -> args[0] < args[1]));
            self._env.define('greater', tuple(Ident('hostfunc'), args -> args[0] > args[1]));
            self._env.define('less_equal', tuple(Ident('hostfunc'), args -> args[0] <= args[1]));
            self._env.define('greater_equal', tuple(Ident('hostfunc'), args -> args[0] >= args[1]));
            self._env.define('not', tuple(Ident('hostfunc'), args -> not args[0]));

            self._env.define('len', tuple(Ident('hostfunc'), args -> len(args[0])));
            self._env.define('index', tuple(Ident('hostfunc'), args -> index(args[0], args[1])));
            self._env.define('slice', tuple(Ident('hostfunc'), args -> slice(args[0], args[1], args[2])));
            self._env.define('push', tuple(Ident('hostfunc'), args -> push(args[0], args[1])));
            self._env.define('pop', tuple(Ident('hostfunc'), args -> pop(args[0])));
            self._env.define('in', tuple(Ident('hostfunc'), args -> in(args[0], args[1])));
            self._env.define('copy', tuple(Ident('hostfunc'), args -> copy(args[0])));

            self._env.define('chr', tuple(Ident('hostfunc'), args -> chr(args[0])));
            self._env.define('ord', tuple(Ident('hostfunc'), args -> ord(args[0])));
            self._env.define('join', tuple(Ident('hostfunc'), args -> join(args[0], args[1])));

            self._env.define('keys', tuple(Ident('hostfunc'), args -> keys(args[0])));
            self._env.define('items', tuple(Ident('hostfunc'), args -> items(args[0])));

            self._env.define('type', tuple(Ident('hostfunc'), args -> type(args[0])));
            self._env.define('bool', tuple(Ident('hostfunc'), args -> bool(args[0])));
            self._env.define('int', tuple(Ident('hostfunc'), args -> int(args[0])));
            self._env.define('str', tuple(Ident('hostfunc'), args -> str(args[0])));
            self._env.define('list', tuple(Ident('hostfunc'), args -> list(args[0])));
            self._env.define('dict', tuple(Ident('hostfunc'), args -> dict(args[0])));
            self._env.define('Ident', tuple(Ident('hostfunc'), args -> Ident(args[0])));
            self._env.define('tuple', tuple(Ident('hostfunc'), args -> apply(tuple, args)));

            self._env.define('print', tuple(Ident('hostfunc'), args -> apply(print, args)));

            self._env.define('read', tuple(Ident('hostfunc'), args -> read(args[0])));
            self._env.define('load', tuple(Ident('hostfunc'), args -> self._load(args[0])));

            self._env.define('eval', tuple(Ident('hostfunc'), args ->
                Evaluator().eval(self.ast(args[0]), self._env)
            ));
            self._env.define('eval_expr', tuple(Ident('hostfunc'), args ->
                Evaluator().eval(args[0], self._env)
            ));
            self._env.define('apply', tuple(Ident('hostfunc'), args ->
                Evaluator().apply(args[0], args[1])
            ))
        end;

        defmethod stdlib do
            self.walk('
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

                def reduce(a, f, init) do
                    acc := init;
                    for x in a do acc = f(acc, x) then acc end
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
            ');

            self._env = Environment(self._env);
            self
        end;

        defmethod _load(path) do
            src := read(path);
            module_env := Environment(self._env);
            expr := self.ast(src);
            Evaluator().eval(expr, module_env)
        end;

        defmethod scan(src) do Scanner(src).tokenize() end;
        defmethod parse(tokens) do Parser(tokens).parse() end;
        defmethod ast(src) do Parser(self.scan(src)).parse() end;
        defmethod eval(ast) do Evaluator().eval(ast, self._env) end;
        defmethod walk(src) do
            try
                self.eval(self.ast(src))
            except ['ReturnException', val] then
                raise('Return from top level @ walk(): ' + str(val))
            except ['ContinueException'] then
                raise('Continue at top level @ walk()')
            except ['BreakException'] then
                raise('Break at top level @ walk()')
            end
        end
    end
""")

if __name__ == "__main__":
    i.walk(r"""
        tot := Interpreter().init_env().stdlib()
    """)
    def scan(src): return i.walk(f""" tot.scan('{src}') """)
    def ast(src): return i.walk(f""" tot.ast('{src}') """)
    def walk(src): return i.walk(f""" tot.walk('{src}') """)

    # Example

    # Lazy evaluation
    print(walk("""
        def force(thunk) do thunk() end;
        def stream_car(s) do s[0] end;
        def stream_cdr(s) do force(s[1]) end;

        def take(n, s) do
            if n == 0 then
                []
            else
                [stream_car(s)] + take(n - 1, stream_cdr(s))
            end
        end;

        def count_from(n) do
            [n, [] -> count_from(n + 1)]
        end;

        take(5, count_from(1))
    """)) # -> [1, 2, 3, 4, 5]