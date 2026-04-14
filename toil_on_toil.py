#! /usr/bin/env python3

from toil import Interpreter

i = Interpreter().init_env().stdlib()

i.walk(r"""
    deffunc isalpha params c do
       type(c) == 'str' and ('a' <= c and c <= 'z') or ('A' <= c and c <= 'Z')
    end;
    deffunc isdigit params c do type(c) == 'str' and '0' <= c and c <= '9' end;
    deffunc isalnum params c do isalpha(c) or isdigit(c) end;
    deffunc isspace params c do c == ' ' or c == "\n" end;

    deffunc is_ident_first params c do isalpha(c) or c == '_' end;
    deffunc is_ident_rest params c do isalnum(c) or c == '_' end;
    deffunc is_ident params s do is_ident_first(s[0]) end
""")

i.walk(r"""
    defclass Scanner params src do
        self._src = src;
        self._pos = 0;
        self._tokens = [];

        defmethod tokenize params do
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
                if ch == '$EOF' then
                    self._tokens.push(Ident('$EOF')); break()
                elif ch.isdigit() then
                    self._number()
                elif ch == "'" then
                    self._raw_string()
                elif ch == '"' then
                    self._string()
                elif ch.is_ident_first() then
                    self._ident()
                elif ch.in('=!<>:') then
                    self._two_char_operator('=')
                elif ch.in('+-*/%()[]{}.,;') then
                    self._tokens.push(Ident(ch)); self._advance()
                else
                    raise('Invalid character @ tokenize: ' + ch)
                end
            end;

            self._tokens
        end;

        defmethod _number params do
            start := self._pos;
            while self._current_char().isdigit() do
                self._advance()
            end;
            self._tokens.push(int(self._src.slice(start, self._pos)))
        end;

        defmethod _raw_string params do
            self._advance();
            start := self._pos;
            while (c := self._current_char()) != "'" do
                if c == '$EOF' then raise('Unterminated string @ _raw_string()') end;
                self._advance()
            end;
            self._tokens.push(self._src.slice(start, self._pos));
            self._advance()
        end;

        defmethod _string params do
            self._advance();
            s := [];
            while (c := self._current_char()) != '"' do
                if c == '$EOF' then raise('Unterminated string @ _string()') end;
                if c == '\' then
                    self._advance();
                    c := self._current_char();
                    if c == '$EOF' then raise('Unterminated string @ _string()') end;
                    match c
                        case 'n' then s.push("\n")
                        case _ then s.push(c)
                    end
                else
                    s.push(c)
                end;
                self._advance()
            end;
            self._advance();
            self._tokens.push(s.join(''))
        end;

        defmethod _ident params do
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

        defmethod _two_char_operator params successors do
            start := self._pos;
            self._advance();
            if self._current_char().in(successors) then
                self._advance()
            end;
            self._tokens.push(Ident(self._src.slice(start, self._pos)))
        end;

        defmethod _advance params do self._pos = self._pos + 1 end;

        defmethod _current_char params do
            if self._pos < self._src.len() then
                self._src[self._pos]
            else
                '$EOF'
            end
        end
    end
""")

i.walk(r"""
    defclass Parser params tokens do
        self._tokens = tokens;
        self._pos = 0;

        defmethod parse params do
            # print(self._tokens);
            expr := self._expression();
            if self._current() != Ident('$EOF') then
                raise('Extra token @ parse: ' + str(self._current()))
            end;
            expr
        end;

        defmethod _expression params do
            self._sequence()
        end;

        defmethod _sequence params do
            exprs := [self._define_assign()];
            while self._current() == Ident(';') do
                self._current_and_advance();
                exprs.push(self._define_assign())
            end;
            if exprs.len() == 1 then exprs[0] else Expr(Ident('seq'), exprs) end
        end;

        defmethod _define_assign params do
            self._binary_right({
                ':=': Ident('define'), '=': Ident('assign')
            }, self._and_or)
        end;

        defmethod _and_or params do
            left := self._not();
            while type(op := self._current()) == 'Ident' and str(op).in(['and', 'or']) do
                self._current_and_advance();
                right := self._not();
                if op == Ident('and') then
                    left := Expr(Ident('scope'), [Expr(Ident('if'), [
                        Expr(Ident('define'), [Ident('__core_and_left'), left]),
                        right,
                        Ident('__core_and_left')
                    ])])
                else
                    left := Expr(Ident('scope'), [Expr(Ident('if'), [
                        Expr(Ident('define'), [Ident('__core_or_left'), left]),
                        Ident('__core_or_left'),
                        right
                    ])])
                end
            end;
            left
        end;

        defmethod _not params do
            self._unary({'not': Ident('not')}, self._comparison)
        end;

        defmethod _comparison params do
            self._binary_left({
                '==': Ident('equal'), '!=': Ident('not_equal'),
                '<': Ident('less'), '>': Ident('greater'),
                '<=': Ident('less_equal'), '>=': Ident('greater_equal')
            }, self._add_sub)
        end;

        defmethod _add_sub params do
            self._binary_left({
                '+': Ident('add'), '-': Ident('sub')
            }, self._mul_div_mod)
        end;

        defmethod _mul_div_mod params do
            self._binary_left({
                '*': Ident('mul'), '/': Ident('div'), '%': Ident('mod')
            }, self._unaries)
        end;

        defmethod _unaries params do
            self._unary({
                '-': Ident('neg'), '+': Ident('+'), '*': Ident('*'),
                '!': Ident('!'), '!!': Ident('!!')
            }, self._call_index_dot)
        end;

        defmethod _call_index_dot params do
            target := self._primary();
            while (op := self._current()).in([Ident('('), Ident('['), Ident('.')]) do
                if op == Ident('(') then
                    self._current_and_advance();
                    target = Expr(target, self._comma_separated_exprs(Ident(')')));
                    self._consume(Ident(')'))
                elif op == Ident('[') then
                    self._current_and_advance();
                    target = Expr(Ident('index'), [target, self._expression()]);
                    self._consume(Ident(']'))
                else
                    self._current_and_advance();
                    prop := self._current_and_advance();
                    if prop.type() != 'Ident' then
                        raise('Invalid property @ _call_index_dot(): ' + str(prop))
                    end;
                    target = Expr(Ident('dot'), [target, str(prop)])
                end
            end;
            target
        end;

        defmethod _primary params do
            match self._current().type()
                case 'NoneType' then self._current_and_advance()
                case 'bool' then self._current_and_advance()
                case 'int' then self._current_and_advance()
                case 'str' then self._current_and_advance()
                case 'Ident' then
                    match str(self._current())
                        case '(' then self._group()
                        case '[' then self._list()
                        case '{' then self._dict()
                        case 'func' then self._func()
                        case 'deffunc' then self._deffunc()
                        case 'scope' then self._scope()
                        case 'if' then self._if()
                        case 'while' then self._while()
                        case 'for' then self._for()
                        case name then
                            if name.is_ident() then
                                self._current_and_advance()
                            else
                                raise('Unexpected token @ primary(): ' + str(self._current()))
                            end
                    end
                case _ then raise('Unexpected token: @ primary(): ' + str(self._current()))
            end
        end;

        defmethod _group params do
            self._current_and_advance();
            expr := self._expression();
            self._consume(Ident(')'));
            expr
        end;

        defmethod _list params do
            self._current_and_advance();
            exprs := self._comma_separated_exprs(Ident(']'));
            self._consume(Ident(']'));
            exprs
        end;

        defmethod _dict params do
            deffunc _parse_key_value params dic do
                match self._current().type()
                    case 'Ident' then
                        key := str(self._current_and_advance());
                        if self._current() == Ident(':') then
                            self._current_and_advance();
                            dic[key] = self._expression()
                        else
                            dic[key] = Ident(key)
                        end
                    case 'str' then
                        key := self._current_and_advance();
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

        defmethod _func params do
            self._current_and_advance();
            params := self._comma_separated_exprs(Ident('do'));
            self._consume(Ident('do'));
            body_expr := self._expression();
            self._consume(Ident('end'));
            Expr(Ident('func'), [params, body_expr])
        end;

        defmethod _deffunc params do
            self._current_and_advance();
            name := self._current_and_advance();
            self._consume(Ident('params'));
            params := self._comma_separated_exprs(Ident('do'));
            self._consume(Ident('do'));
            body_expr := self._expression();
            self._consume(Ident('end'));
            Expr(Ident('define'), [name, Expr(Ident('func'), [params, body_expr])])
        end;

        defmethod _scope params do
            self._current_and_advance();
            body_expr := self._expression();
            self._consume(Ident('end'));
            Expr(Ident('scope'), [body_expr])
        end;

        defmethod _if params do
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
            Expr(Ident('if'), [cond_expr, then_expr, else_expr])
        end;

        defmethod _while params do
            self._current_and_advance();
            cond_expr := self._expression();
            self._consume(Ident('do'));
            body_expr := self._expression();
            self._consume(Ident('end'));
            Expr(Ident('while'), [cond_expr, body_expr])
        end;

        defmethod _for params do
            self._current_and_advance();
            var_expr := self._expression();
            self._consume(Ident('in'));
            coll_expr := self._expression();
            self._consume(Ident('do'));
            body_expr := self._expression();
            self._consume(Ident('end'));
            Expr(Ident('scope'), [Expr(Ident('seq'), [
                Expr(Ident('define'), [Ident('__for_coll'), coll_expr]),
                Expr(Ident('define'), [Ident('__for_index'), -1]),
                Expr(Ident('while'), [
                    Expr(Ident('less'), [
                        Expr(Ident('add'), [Ident('__for_index'), 1]),
                        Expr(Ident('len'), [Ident('__for_coll')])
                    ]),
                    Expr(Ident('seq'), [
                        Expr(Ident('assign'), [
                            Ident('__for_index'),
                            Expr(Ident('add'), [Ident('__for_index'), 1])
                        ]),
                        Expr(Ident('scope'), [Expr(Ident('seq'), [
                            Expr(Ident('define'), [
                                var_expr,
                                Expr(Ident('index'), [
                                    Ident('__for_coll'),
                                    Ident('__for_index')
                                ])
                            ]),
                            body_expr
                        ])])
                    ])
                ])
            ])])
        end;

        defmethod _binary_left params ops, sub_elem do
            left := sub_elem();
            while type(op := self._current()) == 'Ident' and str(op).in(ops) do
                self._current_and_advance();
                right := sub_elem();
                left = Expr(ops[str(op)], [left, right])
            end;
            left
        end;

        defmethod _binary_right params ops, sub_elem do
            left := sub_elem();
            if type(op := self._current()) == 'Ident' and str(op).in(ops) then
                self._current_and_advance();
                right := self._binary_right(ops, sub_elem);
                Expr(ops[str(op)], [left, right])
            else
                left
            end
        end;

        defmethod _unary params ops, sub_elem do
            if type(op := self._current()) == 'Ident' and str(op).in(ops) then
                self._current_and_advance();
                Expr(ops[str(op)], [self._unary(ops, sub_elem)])
            else
                sub_elem()
            end
        end;

        defmethod _comma_separated_exprs params terminator do
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

        defmethod _consume params expected do
            if self._current() == expected then
                self._current_and_advance()
            else
                raise('Expected ' + str(expected) + ' @ consume: '
                      + str(self._current()))
            end
        end;

        defmethod _current params do self._tokens[self._pos] end;

        defmethod _current_and_advance params do
            self._pos = self._pos + 1;
            self._tokens[self._pos - 1]
        end
    end
""")

i.walk(r"""
    defclass Environment params parent do
        self._parent = parent;
        self._vars = {};

        defmethod define params name, val do
            self._vars[name] = val
        end;

        defmethod lookup params name do
            if name.in(self._vars) then
                self._vars
            elif self._parent != None then
                self._parent.lookup(name)
            else
                None
            end
        end;

        defmethod val params name do
            vars := self.lookup(name);
            if vars == None then raise('Undefined variable @ val: ' + name) end;
            vars[name]
        end;

        defmethod assign params name, val do
            vars := self.lookup(name);
            if vars == None then raise('Undefined variable @ assign: ' + name) end;
            vars[name] = val
        end
    end
""")

i.walk(r"""
    defclass Evaluator params do
        defmethod eval params expr, env do
            # print(expr);
            match expr.type()
                case 'NoneType' then expr
                case 'bool' then expr
                case 'int' then expr
                case 'str' then expr
                case 'list' then expr.map(func e do self.eval(e, env) end)
                case 'dict' then
                    expr.keys().map(func k do
                        [self.eval(k, env), self.eval(expr[k], env)]
                    end).dict()
                case 'Ident' then env.val(str(expr))
                case 'Expr' then
                    match expr
                        case Expr(Ident('quote'), [expr]) then
                            expr
                        case Expr(Ident('func'), [params, body_expr]) then
                            Expr(Ident('closure'), [params, body_expr, env])
                        case Expr(Ident('return'), args) then
                            raise(['ReturnException',
                                if args.len() == 0 then None else
                                    self.eval(args[0], env)
                                end
                            ])
                        case Expr(Ident('dot'), [target_expr, prop_expr]) then
                            self._dot(target_expr, prop_expr, env)
                        case Expr(Ident('scope'), [body_expr]) then
                            self.eval(body_expr, Environment(env))
                        case Expr(Ident('define'), [name, val_expr]) then
                            self._define(name, val_expr, env)
                        case Expr(Ident('assign'), [name, val_expr]) then
                            self._assign(name, val_expr, env)
                        case Expr(Ident('seq'), exprs) then
                            self._seq(exprs, env)
                        case Expr(Ident('if'), [cond_expr, then_expr, else_expr]) then
                            self._if(cond_expr, then_expr, else_expr, env)
                        case Expr(Ident('while'), [cond_expr, body_expr]) then
                            self._while(cond_expr, body_expr, env)
                        case Expr(Ident('continue'), []) then
                            raise(['ContinueException'])
                        case Expr(Ident('break'), args) then
                            raise(['BreakException',
                                if args.len() == 0 then None else
                                    self.eval(args[0], env)
                                end
                            ])
                        case Expr(op_expr, args_expr) then
                            self._op(op_expr, args_expr, env)
                    end
            end
        end;

        defmethod _dot params target_expr, prop_expr, env do
            target_val := self.eval(target_expr, env);
            prop_val := self.eval(prop_expr, env);
            if target_val.type() == 'dict' and prop_val.in(target_val) then
                target_val[prop_val]
            else
                func_val := env.val(prop_val);
                Expr(Ident('hostfunc'), func args do
                    self.apply(func_val, [target_val] + args)
                end)
            end
        end;

        defmethod _define params name, val_expr, env do
            val := self.eval(val_expr, env);
            env.define(str(name), val)
        end;

        defmethod _assign params left_expr, right_expr, env do
            deffunc _set_val params coll_expr, index_expr, right_val do
                coll_val := self.eval(coll_expr, env);
                index_val := self.eval(index_expr, env);
                coll_val[index_val] = right_val
            end;

            right_val := self.eval(right_expr, env);
            match left_expr.type()
                case 'Ident' then
                    env.assign(str(left_expr), right_val)
                case 'Expr' then
                    match left_expr
                        case Expr(Ident('index'), [coll_expr, index_expr]) then
                            _set_val(coll_expr, index_expr, right_val)
                        case Expr(Ident('dot'), [coll_expr, index_expr]) then
                            _set_val(coll_expr, index_expr, right_val)
                        case _ then
                            raise('Invalid assign target @ _assign: ' + str(left_expr))
                    end
                case _ then
                    raise('Invalid assign target @ _assign: ' + str(left_expr))
            end
        end;

        defmethod _seq params exprs, env do
            for expr in exprs do
                self.eval(expr, env)
            end
        end;

        defmethod _if params cond_expr, then_expr, else_expr, env do
            if self.eval(cond_expr, env) then
                self.eval(then_expr, env)
            else
                self.eval(else_expr, env)
            end
        end;

        defmethod _while params cond_expr, body_expr, env do
            while self.eval(cond_expr, env) do
                try
                    self.eval(body_expr, env)
                except ['ContinueException'] then continue()
                except ['BreakException', val] then return(val)
                end
            end
        end;

        defmethod _op params op_expr, args_expr, env do
            op_val := self.eval(op_expr, env);
            args_val := args_expr.map(func arg do self.eval(arg, env) end);
            self.apply(op_val, args_val)
        end;

        defmethod apply params op_val, args_val do
            match op_val
                case Expr(Ident('hostfunc'), f) then f(args_val)
                case Expr(Ident('closure'), [params, body_expr, closure_env]) then
                    new_env := Environment(closure_env);
                    for [param, arg] in zip(params, args_val) do
                        new_env.define(str(param), arg)
                    end;
                    try
                        self.eval(body_expr, new_env)
                    except ['ReturnException', val] then
                        val
                    end
                case _ then raise('Invalid operator @ apply: ' + str(op_val))
            end
        end
    end
""")

i.walk(r"""
    defclass Interpreter params do
        self._env = Environment(None);

        defmethod init_env params do
            self._env = Environment(None);
            self._builtins();
            self
        end;

        defmethod _builtins params do
            self._env.define('__builtins', None);

            self._env.define('add', Expr(Ident('hostfunc'), func args do args[0] + args[1] end));
            self._env.define('sub', Expr(Ident('hostfunc'), func args do args[0] - args[1] end));
            self._env.define('mul', Expr(Ident('hostfunc'), func args do args[0] * args[1] end));
            self._env.define('div', Expr(Ident('hostfunc'), func args do args[0] / args[1] end));
            self._env.define('mod', Expr(Ident('hostfunc'), func args do args[0] % args[1] end));
            self._env.define('neg', Expr(Ident('hostfunc'), func args do -args[0] end));

            self._env.define('equal', Expr(Ident('hostfunc'), func args do args[0] == args[1] end));
            self._env.define('not_equal', Expr(Ident('hostfunc'), func args do args[0] != args[1] end));
            self._env.define('less', Expr(Ident('hostfunc'), func args do args[0] < args[1] end));
            self._env.define('greater', Expr(Ident('hostfunc'), func args do args[0] > args[1] end));
            self._env.define('less_equal', Expr(Ident('hostfunc'), func args do args[0] <= args[1] end));
            self._env.define('greater_equal', Expr(Ident('hostfunc'), func args do args[0] >= args[1] end));
            self._env.define('not', Expr(Ident('hostfunc'), func args do not args[0] end));

            self._env.define('len', Expr(Ident('hostfunc'), func args do len(args[0]) end));
            self._env.define('index', Expr(Ident('hostfunc'), func args do index(args[0], args[1]) end));
            self._env.define('slice', Expr(Ident('hostfunc'), func args do slice(args[0], args[1], args[2]) end));
            self._env.define('push', Expr(Ident('hostfunc'), func args do push(args[0], args[1]) end));
            self._env.define('pop', Expr(Ident('hostfunc'), func args do pop(args[0]) end));
            self._env.define('in', Expr(Ident('hostfunc'), func args do in(args[0], args[1]) end));
            self._env.define('copy', Expr(Ident('hostfunc'), func args do copy(args[0]) end));

            self._env.define('chr', Expr(Ident('hostfunc'), func args do chr(args[0]) end));
            self._env.define('ord', Expr(Ident('hostfunc'), func args do ord(args[0]) end));
            self._env.define('join', Expr(Ident('hostfunc'), func args do join(args[0], args[1]) end));

            self._env.define('keys', Expr(Ident('hostfunc'), func args do keys(args[0]) end));
            self._env.define('items', Expr(Ident('hostfunc'), func args do items(args[0]) end));

            self._env.define('type', Expr(Ident('hostfunc'), func args do type(args[0]) end));
            self._env.define('str', Expr(Ident('hostfunc'), func args do str(args[0]) end));
            self._env.define('int', Expr(Ident('hostfunc'), func args do int(args[0]) end));
            self._env.define('list', Expr(Ident('hostfunc'), func args do list(args[0]) end));
            self._env.define('dict', Expr(Ident('hostfunc'), func args do dict(args[0]) end));
            self._env.define('Ident', Expr(Ident('hostfunc'), func args do Ident(args[0]) end));
            self._env.define('Expr', Expr(Ident('hostfunc'), func args do apply(Expr, args) end));

            self._env.define('print', Expr(Ident('hostfunc'), func args do apply(print, args) end));

            self._env.define('eval_expr', Expr(Ident('hostfunc'), func args do
                Evaluator().eval(args[0], self._env)
            end))
        end;

        defmethod stdlib params do
            self.walk('
                deffunc first params a do a[0] end;
                deffunc rest params a do slice(a, 1, None) end;
                deffunc last params a do a[-1] end
            ');
            self.walk('
                deffunc range params start, stop, step do
                    b := [];
                    i := start; while i < stop do push(b, i); i = i + step end;
                    b
                end
            ');
            self.walk('
                deffunc map params a, f do
                    b := [];
                    for x in a do push(b, f(x)) end;
                    b
                end
            ');
            self.walk('
                deffunc filter params a, f do
                    b := [];
                    for x in a do if f(x) then push(b, x) end end;
                    b
                end
            ');
            self.walk('
                deffunc zip params a, b do
                    z := []; la := len(a); lb := len(b);
                    i := 0; while i < la and i < lb do
                        push(z, [a[i], b[i]]); i = i + 1
                    end;
                    z
                end
            ');
            self.walk('
                deffunc reduce params a, f, init do
                    acc := init;
                    for x in a do acc = f(acc, x) end;
                    acc
                end
            ');
            self.walk('
                deffunc reverse params a do
                    b := []; l := len(a);
                    for i in range(1, l + 1, 1) do push(b, a[l - i]) end;
                    b
                end
            ');
            self.walk('
                deffunc enumerate params a do
                    zip(range(0, len(a), 1), a)
                end
            ');

            self._env = Environment(self._env);
            self
        end;

        defmethod scan params src do Scanner(src).tokenize() end;
        defmethod parse params tokens do Parser(tokens).parse() end;
        defmethod ast params src do Parser(self.scan(src)).parse() end;
        defmethod eval params ast do Evaluator().eval(ast, self._env) end;
        defmethod walk params src do
            try
                self.eval(self.ast(src))
            except ['ReturnException', val] then
                raise('Return from top level @ evaluate(): ' + str(val))
            except ['ContinueException'] then
                raise('Continue at top level @ evaluate()')
            except ['BreakException', val] then
                raise('Break at top level @ evaluate(): ' + str(val))
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

    # Dot notation
    walk(r""" a := {aaa: 2 , bbb: 3} """)

    print(scan(r""" a.aaa """)) # -> [a, ., aaa, $EOF]
    print(ast(r""" a.aaa """)) # -> (dot, [a, 'aaa'])
    print(walk(r""" a.aaa """)) # -> 2

    walk(r""" a.bbb = 4 """)
    print(walk(r""" a """)) # -> {'aaa': 2, 'bbb': 4}
    walk(r""" a.ccc = 5 """)
    print(walk(r""" a """)) # -> {'aaa': 2, 'bbb': 4, 'ccc': 5}

    walk(r""" a.ddd = add """)
    print(walk(r""" a.ddd(2, 3) """)) # -> 5

    # walk(r""" a.not_found """) # -> KeyError
    # walk(r""" a.1 """) # -> Invalid property
    # walk(r""" [2, 3].aaa """) # -> TypeError
    # walk(r""" [2, 3].aaa = 4 """) # -> Invalid indexing

    # UFCS
    print(walk(r""" 2.add(3) """)) # -> 5
    print(walk(r""" [2, 3, 4].len().add(5) """)) # -> 8

    walk(r""" deffunc myadd params a, b do a + b end """)
    print(walk(r""" 2.myadd(3) """))

    # walk(r""" 2.not_found() """) # -> Undefined variable
    # walk(r""" foo := 2; 3.foo() """) # -> Invalid operator

    # Examples with UFCS

    print(walk(r"""
        deffunc quicksort params a do
            if len(a) <= 1 then a else
                pivot := first(a); rem := rest(a);
                left := rem.filter(func x do x < pivot end);
                right := rem.filter(func x do x >= pivot end);
                quicksort(left) + [pivot] + quicksort(right)
            end
        end;

        quicksort([5, 3, 8, 4, 2])
    """))

    print(walk(r"""
        deffunc sieve params n do
            s := [False, False] + [True] * (n - 2);
            i := 2; while i * i < n do
                if s[i] then
                    for j in range(i * i, n, i) do s[j] = False end
                end;
                i = i + 1
            end;

            enumerate(s).filter(last).map(first)
        end;

        sieve(10)
    """))
