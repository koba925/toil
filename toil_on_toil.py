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
            if self._current_token() != sym('$EOF') then
                raise('Extra token @ parse: ' + str(self._current_token()))
            end;
            expr
        end;

        self._expression = func self do
            self._primary()
        end;

        self._primary = func self do
            match self._current_token().type()
                case 'int' then self._current_and_advance()
                case _ then raise('Unexpected token: ' + str(self._current_token()))
            end
        end;

        self._current_token = func self do self._tokens[self._pos] end;

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
            match expr.type()
                case 'int' then expr
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

    # example

    i.walk(r"""
        tot := Interpreter()
    """)

    i.walk(r"""
        # Overall structure
        print(tot.scan('2')); # -> [2, $EOF]
        print(tot.parse([2, sym('$EOF')])); # -> 2
        print(tot.ast('2')); # -> 2
        print(tot.eval(2)); # -> 2
        print(tot.walk('2')); # -> 2

        # Numbers
        print(tot.walk('2')); # -> 2
        print(tot.walk('23')); # -> 23
        print(tot.walk('0')); # -> 0
        print(tot.walk('023')); # -> 23

        # Whitespace
        print(tot.walk('  2')); # -> 2
        print(tot.walk('2  ')); # -> 2
        print(tot.walk("\n  2  \n")); # -> 2

        # Empty source
        tot.walk(''); # -> Error

        # Invalid character
        # tot.walk('~') # -> Error

        # Extra token
        # tot.walk('2 3'); # -> Error

        None
    """)
