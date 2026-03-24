#! /usr/bin/env python3

from toil import Interpreter

i = Interpreter().init_env().corelib().stdlib()

i.walk("""
    deffunc isalpha params c do
       ('a' <= c and c <= 'z') or ('A' <= c and c <= 'Z')
    end;
    deffunc isdigit params c do '0' <= c and c <= '9' end;
    deffunc isalnum params c do isalpha(c) or isdigit(c) end;

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

        self.tokenize = func self do [int(src)] end;

        self
    end
""")

i.walk("""
    deffunc Parser params tokens do
        self := {};
        self._tokens = tokens;
        self._pos = 0;

        self.parse = func self do tokens[0] end;

        self
    end
""")

i.walk("""
    deffunc Evaluator params do
        self := {};

        self.eval = func self, expr do expr end;

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

    i.walk("""
        i := Interpreter();

        print(i.scan("2")); # -> [2]
        print(i.parse([2])); # -> 2
        print(i.ast("2")); # -> 2
        print(i.eval(2)); # -> 2
        print(i.walk("2")); # -> 2

        None
    """)
