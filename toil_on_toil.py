#! /usr/bin/env python3

from toil import Interpreter

i = Interpreter().init_env().corelib().stdlib()

i.walk("""
    deffunc isalpha params c do
       ('a' <= c and c <= 'z') or ('A' <= c and c <= 'Z')
    end;
    deffunc isdigit params c do '0' <= c and c <= '9' end;
    deffunc isalnum params c do isalpha(c) or isdigit(c) end;
    deffunc isspace params c do c == ' ' or c == '\n' end;

    deffunc is_ident_first params c do isalpha(c) or c == '_' end;
    deffunc is_ident_rest params c do isalnum(c) or c == '_' end;
    deffunc is_ident params s do is_ident_first(s[0]) end;
""")

i.walk("""
    deffunc Scanner params src do
        self := {};
        self._src = src;
        self._pos = 0;
        self._tokens = [];

        self.tokenize = func self do
            while True do
                while self._current_char().isspace() do self._advance() end;

                ch := self._current_char();
                if ch == ident('$EOF') then
                    self._tokens.push(ch); break()
                elif ch.isdigit() then
                    self._number()
                elif ch.is_ident_first() then
                    self._ident()
                elif ch.in(':') then
                    self._two_char_operator('=')
                elif ch.in('=,;') then
                    self._tokens.push(ident(ch)); self._advance()
                else
                    raise('Invalid character @ tokenize: ' + ch)
                end
            end;

            self._tokens
        end;

        self._two_char_operator = func self, successors do
            start := self._pos;
            self._advance();
            if self._current_char().in(successors) then
                self._advance()
            end;
            self._tokens.push(ident(self._src.slice(start, self._pos)))
        end;

        self._number = func self do
            start := self._pos;
            while self._current_char().isdigit() do
                self._advance()
            end;
            self._tokens.push(int(self._src.slice(start, self._pos)))
        end;

        self._ident = func self do
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
                case _ then self._tokens.push(ident(token))
            end
        end;

        self._advance = func self do self._pos = self._pos + 1 end;

        self._current_char = func self do
            if self._pos < self._src.len() then
                self._src[self._pos]
            else
                ident('$EOF')
            end
        end;

        self
    end
""")

i.walk("""
    deffunc Parser params tokens do
        self := {};
        self._tokens = tokens;
        self._pos = 0;

        self.parse = func self do
            expr := self._expression();
            if self._current() != ident('$EOF') then
                raise('Extra token @ parse: ' + str(self._current()))
            end;
            expr
        end;

        self._expression = func self do
            self._sequence()
        end;

        self._sequence = func self do
            exprs := [self._define_assign()];
            while self._current() == ident(';') do
                self._current_and_advance();
                exprs.push(self._define_assign())
            end;
            if exprs.len() == 1 then exprs[0] else expr(ident('seq'), exprs) end
        end;

        self._define_assign = func self do
            self._binary_right({
                ':=': ident('define'),
                '=': ident('assign')
            }, self._primary)
        end;

        self._binary_right = func self, ops, sub_elem do
            left := sub_elem();
            if self._current().type() == 'ident' and
               (op := str(self._current())).in(ops) then
                self._current_and_advance();
                right := self._binary_right(ops, sub_elem);
                expr(ops[op], [left, right])
            else
                left
            end
        end;

        self._primary = func self do
            match self._current().type()
                case 'NoneType' then self._current_and_advance()
                case 'bool' then self._current_and_advance()
                case 'int' then self._current_and_advance()
                case 'ident' then
                    match str(self._current())
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

        self._scope = func self do
            self._current_and_advance();
            body_expr := self._expression();
            self._consume(ident('end'));
            expr(ident('scope'), [body_expr])
        end;

        self._if = func self do
            self._current_and_advance();
            cond_expr := self._expression();
            self._consume(ident('then'));
            then_expr := self._expression();
            else_expr := None;
            if self._current() == ident('elif') then
                else_expr = self._if()
            elif self._current() == ident('else') then
                self._current_and_advance();
                else_expr = self._expression();
                self._consume(ident('end'))
            else
                else_expr = None;
                self._consume(ident('end'))
            end;
            expr(ident('if'), [cond_expr, then_expr, else_expr])
        end;

        self._while = func self do
            self._current_and_advance();
            cond_expr := self._expression();
            self._consume(ident('do'));
            body_expr := self._expression();
            self._consume(ident('end'));
            expr(ident('while'), [cond_expr, body_expr])
        end;


        self._consume = func self, expected do
            if self._current() == expected then
                self._current_and_advance()
            else
                raise('Expected ' + expected + ' @ consume: ' + str(self._current()))
            end
        end;

        self._current = func self do self._tokens[self._pos] end;

        self._current_and_advance = func self do
            self._pos = self._pos + 1;
            self._tokens[self._pos - 1]
        end;

        self
    end
""")

i.walk("""
    deffunc Environment params parent do
        self := {};
        self._parent = parent;
        self._vars = {};

        self.define = func self, name, val do
            self._vars[name] = val
        end;

        self.lookup = func self, name do
            if name.in(self._vars) then
                self._vars
            elif self._parent != None then
                self._parent.lookup(name)
            else
                None
            end
        end;

        self.val = func self, name do
            vars := self.lookup(name);
            if vars == None then
                raise('Undefined variable @ val: ' + name)
            end;
            vars[name]
        end;

        self.set_val = func self, name, val do
            vars := self.lookup(name);
            if vars == None then
                raise('Undefined variable @ set_val: ' + name)
            end;
            vars[name] = val
        end;

        self
    end
""")

i.walk("""
    deffunc Evaluator params do
        self := {};

        self.eval = func self, expr, env do
            # print(expr);
            match expr.type()
                case 'NoneType' then expr
                case 'bool' then expr
                case 'int' then expr
                case 'ident' then env.val(str(expr))
                case 'expr' then
                    match expr
                        case expr(ident('scope'), [body_expr]) then
                            self.eval(body_expr, Environment(env))
                        case expr(ident('define'), [name, val_expr]) then
                            self._define(name, val_expr, env)
                        case expr(ident('assign'), [name, val_expr]) then
                            self._assign(name, val_expr, env)
                        case expr(ident('seq'), exprs) then
                            self._seq(exprs, env)
                        case expr(ident('if'), [cond_expr, then_expr, else_expr]) then
                            self._if(cond_expr, then_expr, else_expr, env)
                        case expr(ident('while'), [cond_expr, body_expr]) then
                            self._while(cond_expr, body_expr, env)
                    end
            end
        end;

        self._define = func self, name, val_expr, env do
            val := self.eval(val_expr, env);
            env.define(str(name), val)
        end;

        self._assign = func self, name, val_expr, env do
            val := self.eval(val_expr, env);
            env.set_val(str(name), val)
        end;

        self._seq = func self, exprs, env do
            for expr in exprs do
                self.eval(expr, env)
            end
        end;

        self._if = func self, cond_expr, then_expr, else_expr, env do
            if self.eval(cond_expr, env) then
                self.eval(then_expr, env)
            else
                self.eval(else_expr, env)
            end
        end;

        self._while = func self, cond_expr, body_expr, env do
            while self.eval(cond_expr, env) do
                self.eval(body_expr, env)
            end
        end;

        self
    end
""")

i.walk("""
    deffunc Interpreter params do
        self := {};
        self._env = Environment(None);

        self.init_env = func self do
            self._env = Environment(None);
            self
        end;

        self.scan = func self, src do Scanner(src).tokenize() end;
        self.parse = func self, tokens do Parser(tokens).parse() end;
        self.ast = func self, src do Parser(self.scan(src)).parse() end;
        self.eval = func self, ast do Evaluator().eval(ast, self._env) end;
        self.walk = func self, src do self.eval(self.ast(src)) end;

        self
    end
""")

if __name__ == "__main__":

    # Example

    i.walk(r"""
        tot := Interpreter().init_env()
    """)

    i.walk(r"""
        # While
        print(tot.walk('a := True; while a do a = False end')); # -> False
        print(tot.walk('a := False; while a do a = False end')); # -> None

        None
    """)
