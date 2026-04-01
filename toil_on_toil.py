#! /usr/bin/env python3

from toil import Interpreter

i = Interpreter().init_env().stdlib()

i.walk("""
    deffunc isalpha params c do
       type(c) == 'str' and ('a' <= c and c <= 'z') or ('A' <= c and c <= 'Z')
    end;
    deffunc isdigit params c do type(c) == 'str' and '0' <= c and c <= '9' end;
    deffunc isalnum params c do isalpha(c) or isdigit(c) end;
    deffunc isspace params c do c == ' ' or c == '\n' end;

    deffunc is_ident_first params c do isalpha(c) or c == '_' end;
    deffunc is_ident_rest params c do isalnum(c) or c == '_' end;
    deffunc is_ident params s do is_ident_first(s[0]) end
""")

i.walk("""
    defclass Scanner params src do
        self._src = src;
        self._pos = 0;
        self._tokens = [];

        defmethod tokenize params do
            while True do
                while self._current_char().isspace() do self._advance() end;

                ch := self._current_char();
                if ch == '$EOF' then
                    self._tokens.push(Ident('$EOF')); break()
                elif ch.isdigit() then
                    self._number()
                elif ch.is_ident_first() then
                    self._ident()
                elif ch.in(':') then
                    self._two_char_operator('=')
                elif ch.in('=(),;') then
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

i.walk("""
    defclass Parser params tokens do
        self._tokens = tokens;
        self._pos = 0;

        defmethod parse params do
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
                ':=': Ident('define'),
                '=': Ident('assign')
            }, self._call)
        end;

        defmethod _call params do
            target := self._primary();
            while self._current() == Ident('(') do
                self._current_and_advance();
                target = Expr(target, self._comma_separated_exprs(Ident(')')));
                self._consume(Ident(')'))
            end;
            target
        end;

        defmethod _primary params do
            match self._current().type()
                case 'NoneType' then self._current_and_advance()
                case 'bool' then self._current_and_advance()
                case 'int' then self._current_and_advance()
                case 'Ident' then
                    match str(self._current())
                        case 'func' then self._func()
                        case 'scope' then self._scope()
                        case 'if' then self._if()
                        case 'while' then self._while()
                        case name then
                            if name.is_ident() then
                                self._current_and_advance()
                            else
                                raise('Unexpected token: ' + str(self._current()))
                            end
                    end
                case _ then raise('Unexpected token: ' + str(self._current()))
            end
        end;

        defmethod _func params do
            self._current_and_advance();
            params := self._comma_separated_exprs(Ident('do'));
            self._consume(Ident('do'));
            body_expr := self._expression();
            self._consume(Ident('end'));
            Expr(Ident('func'), [params, body_expr])
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

        defmethod _binary_right params ops, sub_elem do
            left := sub_elem();
            if self._current().type() == 'Ident' and
               (op := str(self._current())).in(ops) then
                self._current_and_advance();
                right := self._binary_right(ops, sub_elem);
                Expr(ops[op], [left, right])
            else
                left
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

i.walk("""
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

i.walk("""
    defclass Evaluator params do
        defmethod eval params expr, env do
            # print(expr);
            match expr.type()
                case 'NoneType' then expr
                case 'bool' then expr
                case 'int' then expr
                case 'Ident' then env.val(str(expr))
                case 'Expr' then
                    match expr
                        case Expr(Ident('func'), [params, body_expr]) then
                            Expr(Ident('closure'), [params, body_expr, env])
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
                        case Expr(op_expr, args_expr) then
                            self._op(op_expr, args_expr, env)
                    end
            end
        end;

        defmethod _define params name, val_expr, env do
            val := self.eval(val_expr, env);
            env.define(str(name), val)
        end;

        defmethod _assign params name, val_expr, env do
            val := self.eval(val_expr, env);
            env.assign(str(name), val)
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
                self.eval(body_expr, env)
            end
        end;

        defmethod _op params op_expr, args_expr, env do
            op_val := self.eval(op_expr, env);
            args_val := args_expr.map(func arg do self.eval(arg, env) end);
            self.apply(op_val, args_val)
        end;

        defmethod apply params op_val, args_val do
            match op_val
                case Expr(Ident("hostfunc"), f) then f(args_val)
                case Expr(Ident("closure"), [params, body_expr, closure_env]) then
                    new_env := Environment(closure_env);
                    for [param, arg] in zip(params, args_val) do
                        new_env.define(str(param), arg)
                    end;
                    self.eval(body_expr, new_env)
                case _ then raise('Invalid operator @ apply: ' + str(op_val))
            end
        end
    end
""")

i.walk("""
    defclass Interpreter params do
        self._env = Environment(None);

        defmethod init_env params do
            self._env = Environment(None);
            self._builtins();
            self
        end;

        defmethod _builtins params do
            self._env.define("__builtins", None);

            self._env.define("add", Expr(Ident("hostfunc"), func args do args[0] + args[1] end));
            self._env.define("sub", Expr(Ident("hostfunc"), func args do args[0] - args[1] end));
            self._env.define("mul", Expr(Ident("hostfunc"), func args do args[0] * args[1] end));
            self._env.define("div", Expr(Ident("hostfunc"), func args do args[0] / args[1] end));
            self._env.define("mod", Expr(Ident("hostfunc"), func args do args[0] % args[1] end));
            self._env.define("neg", Expr(Ident("hostfunc"), func args do -args[0] end));

            self._env.define("equal", Expr(Ident("hostfunc"), func args do args[0] == args[1] end));
            self._env.define("not_equal", Expr(Ident("hostfunc"), func args do args[0] != args[1] end));
            self._env.define("less", Expr(Ident("hostfunc"), func args do args[0] < args[1] end));
            self._env.define("greater", Expr(Ident("hostfunc"), func args do args[0] > args[1] end));
            self._env.define("less_equal", Expr(Ident("hostfunc"), func args do args[0] <= args[1] end));
            self._env.define("greater_equal", Expr(Ident("hostfunc"), func args do args[0] >= args[1] end));
            self._env.define("not", Expr(Ident("hostfunc"), func args do not args[0] end));

            self._env.define("len", Expr(Ident("hostfunc"), func args do len(args[0]) end));
            self._env.define("index", Expr(Ident("hostfunc"), func args do index(args[0], args[1]) end));
            self._env.define("slice", Expr(Ident("hostfunc"), func args do slice(args[0], args[1], args[2]) end));
            self._env.define("push", Expr(Ident("hostfunc"), func args do push(args[0], args[1]) end));
            self._env.define("pop", Expr(Ident("hostfunc"), func args do pop(args[0]) end));
            self._env.define("in", Expr(Ident("hostfunc"), func args do in(args[0], args[1]) end));
            self._env.define("copy", Expr(Ident("hostfunc"), func args do copy(args[0]) end));

            self._env.define("chr", Expr(Ident("hostfunc"), func args do chr(args[0]) end));
            self._env.define("ord", Expr(Ident("hostfunc"), func args do ord(args[0]) end));
            self._env.define("join", Expr(Ident("hostfunc"), func args do join(args[0], args[1]) end));

            self._env.define("keys", Expr(Ident("hostfunc"), func args do keys(args[0]) end));
            self._env.define("items", Expr(Ident("hostfunc"), func args do items(args[0]) end));

            self._env.define("type", Expr(Ident("hostfunc"), func args do type(args[0]) end));
            self._env.define("str", Expr(Ident("hostfunc"), func args do str(args[0]) end));
            self._env.define("int", Expr(Ident("hostfunc"), func args do int(args[0]) end));
            self._env.define("Ident", Expr(Ident("hostfunc"), func args do Ident(args[0]) end));
            self._env.define("Expr", Expr(Ident("hostfunc"), func args do apply(Expr, args) end));

            self._env.define("print", Expr(Ident("hostfunc"), func args do apply(print, args) end))
        end;

        defmethod scan params src do Scanner(src).tokenize() end;
        defmethod parse params tokens do Parser(tokens).parse() end;
        defmethod ast params src do Parser(self.scan(src)).parse() end;
        defmethod eval params ast do Evaluator().eval(ast, self._env) end;
        defmethod walk params src do self.eval(self.ast(src)) end
    end
""")

if __name__ == "__main__":
    i.walk(r"""
        tot := Interpreter().init_env()
    """)

    # Example

    i.walk(r"""
        # User defined function
        print(tot.scan('func do 2 end')); # -> [func, do, 2, end, $EOF]
        print(tot.ast('func do 2 end')); # -> (func, [[], 2])
        print(tot.walk('func do 2 end ()')); # -> 2

        print(tot.scan('func a do add(a, 2) end')); # -> [func, a, do, add, (, a, ,, 2, ), end, $EOF]
        print(tot.ast('func a do add(a, 2) end')); # -> (func, [[a], (add, [a, 2])])
        print(tot.walk('func a do add(a, 2) end (3)')); # -> 5

        print(tot.scan('func a, b do add(a, b) end')); # -> [func, a, ,, b, do, add, (, a, ,, b, ), end, $EOF]
        print(tot.ast('func a, b do add(a, b) end')); # -> (func, [[a, b], (add, [a, b])])
        print(tot.walk('func a, b do add(a, b) end (2, 3)')); # -> 5

        print(tot.walk('func a, b do add(a, b) end (add(2, 3), 4; 5)')); # -> 10
        print(tot.walk('
           myadd := func a, b do add(a, b) end;
           myadd(2, 3)
        ')); # -> 5

        print(tot.walk('func a, b do add(a, b) end (2, 3, 4)')); # -> 5 (not an error)
        # print(tot.walk('func a, b do add(a, b) end (2)')); # -> Undefined variable @ val: b
        # print(tot.walk('func a add(a, 2) end')); # -> Expected do @ consume: add
        # print(tot.walk('func a do add(a, 2)')); # -> Expected end @ consume: $EOF

        None
    """) # ->, b

    i.walk(r"""
        # GCD by recursion with function calls
        tot.walk('
            gcd := func a, b do
                if equal(b, 0) then
                    a
                else
                    gcd(b, mod(a, b))
                end
            end
        ');
        tot.walk('print(gcd(12, 18))'); # -> 6
        None
    """)

    i.walk(r"""
        # Factorial by recursion with function calls
        tot.walk('
            fac := func n do
                if equal(n, 0) then 1
                else mul(n, fac(sub(n, 1)))
                end
            end
        ');
        tot.walk('print(fac(0))'); # -> 1
        tot.walk('print(fac(1))'); # -> 1
        tot.walk('print(fac(4))'); # -> 24

        None
    """)

    i.walk(r"""
        # Fibonacci by recursive with function calls
        tot.walk('
            fib := func n do
                if equal(n, 0) then 0
                elif equal(n, 1) then 1
                else add(fib(sub(n, 1)), fib(sub(n, 2)))
                end
            end
        ');
        tot.walk('print(fib(0))'); # -> 0
        tot.walk('print(fib(1))'); # -> 1
        tot.walk('print(fib(6))'); # -> 8

        None
    """)

    i.walk(r"""
        # Mutual recursion
        tot.walk('
            even := func n do
                if equal(n, 0) then True else odd(sub(n, 1)) end
            end;

            odd := func n do
                if equal(n, 0) then False else even(sub(n, 1)) end
            end
        ');

        tot.walk('print(even(2))'); # -> True
        tot.walk('print(even(3))'); # -> False
        tot.walk('print(odd(2))'); # -> False
        tot.walk('print(odd(3))'); # -> True

        None
    """)

    i.walk(r"""
        # Closure and state: Counter
        tot.walk('
            make_counter := func do
                count := 0;
                func do
                    count = add(count, 1);
                    count
                end
            end;

            c1 := make_counter();
            c2 := make_counter()
        ');

        tot.walk('print(c1())'); # -> 1
        tot.walk('print(c2())'); # -> 1
        tot.walk('print(c1())'); # -> 2
        tot.walk('print(c2())'); # -> 2

        None
    """)