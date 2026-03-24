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

    deffunc is_name_first params c do isalpha(c) or c == '_' end;
    deffunc is_name_rest params c do isalnum(c) or c == '_' end;
    deffunc is_name params expr do
       expr.type() == 'sym' and is_name_first(str(expr)[0])
    end
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
                if ch == sym('$EOF') then
                    self._tokens.push(ch); break()
                elif ch.isdigit() then
                    self._number()
                elif ch.is_name_first() then
                    self._name()
                else
                    raise('Invalid character @ tokenize: ' + ch)
                end
            end;

            self._tokens
        end;

        self._number = func self do
            start := self._pos;
            while self._current_char().isdigit() do
                self._advance()
            end;
            self._tokens.push(int(self._src.slice(start, self._pos)))
        end;

        self._name = func self do
            start := self._pos;
            self._advance();
            while self._current_char().is_name_rest() do
                self._advance()
            end;
            token := self._src.slice(start, self._pos);
            match token
                case 'None' then self._tokens.push(None)
                case 'True' then self._tokens.push(True)
                case 'False' then self._tokens.push(False)
                case _ then self._tokens.push(sym(token))
            end
        end;

        self._advance = func self do self._pos = self._pos + 1 end;

        self._current_char = func self do
            if self._pos < self._src.len() then
                self._src[self._pos]
            else
                sym('$EOF')
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
            if self._current() != sym('$EOF') then
                raise('Extra token @ parse: ' + str(self._current()))
            end;
            expr
        end;

        self._expression = func self do
            self._primary()
        end;

        self._primary = func self do
            match self._current().type()
                case 'NoneType' then self._current_and_advance()
                case 'bool' then self._current_and_advance()
                case 'int' then self._current_and_advance()
                case 'sym' then
                    match str(self._current())
                        case 'if' then self._if()
                    end
                case _ then raise('Unexpected token: ' + str(self._current()))
            end
        end;

        self._if = func self do
            self._current_and_advance();
            cond_expr := self._expression();
            self._consume(sym('then'));
            then_expr := self._expression();
            else_expr := None;
            if self._current() == sym('elif') then
                else_expr = self._if()
            elif self._current() == sym('else') then
                self._current_and_advance();
                else_expr = self._expression();
                self._consume(sym('end'))
            else
                else_expr = None;
                self._consume(sym('end'))
            end;
            expr(sym('if'), [cond_expr, then_expr, else_expr])
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
    deffunc Evaluator params do
        self := {};

        self.eval = func self, expr do
            # print(expr);
            match expr.type()
                case 'NoneType' then expr
                case 'bool' then expr
                case 'int' then expr
                case 'expr' then
                    match expr
                        case expr(sym('if'), [cond_expr, then_expr, else_expr]) then
                            self._if(cond_expr, then_expr, else_expr)
                    end
            end
        end;

        self._if = func self, cond_expr, then_expr, else_expr do
            if self.eval(cond_expr) then
                self.eval(then_expr)
            else
                self.eval(else_expr)
            end
        end;

        self
    end
""")

i.walk("""
    deffunc Interpreter params do
        self := {};

        self.scan = func self, src do Scanner(src).tokenize() end;
        self.parse = func self, tokens do Parser(tokens).parse() end;
        self.ast = func self, src do Parser(self.scan(src)).parse() end;
        self.eval = func self, ast do Evaluator().eval(ast) end;
        self.walk = func self, src do self.eval(self.ast(src)) end;

        self
    end
""")

if __name__ == "__main__":

    # Example

    i.walk(r"""
        tot := Interpreter()
    """)

    i.walk(r"""
        # If
        print(tot.walk('if True then 2 end')); # -> 2
        print(tot.walk('if False then 2 end')); # -> None
        print(tot.walk('if True then 2 else 3 end')); # -> 2
        print(tot.walk('if False then 2 else 3 end')); # -> 3
        print(tot.walk('if True then 2 elif True then 3 end')); # -> 2
        print(tot.walk('if False then 2 elif True then 3 end')); # -> 3
        print(tot.walk('if False then 2 elif False then 3 end')); # -> None
        print(tot.walk('if False then 2 elif True then 3 else 4 end')); # -> 3
        print(tot.walk('if True then 2 elif True then 3 else 4 end')); # -> 2
        print(tot.walk('if False then 2 elif False then 3 else 4 end')); # -> 4
        print(tot.walk('if False then 2 elif False then 3 elif True then 4 else 5 end')); # -> 4

        # tot.walk('if True 2 end'); # -> Error
        # tot.walk('if True then 2'); # -> Error
        # tot.walk('if True then 2 3 end'); # -> Error
        # tot.walk('if True then 2 else 3'); # -> Error
        # tot.walk('if False then 2 elif True 3 end'); # -> Error
        # tot.walk('if False then 2 elif True then 3'); # -> Error

        None
    """)
