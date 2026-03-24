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

if __name__ == "__main__":

    # example

    i.walk("""
        print("# isalpha");

        print(isalpha("a")); # -> True
        print(isalpha("z")); # -> True
        print(isalpha("A")); # -> True
        print(isalpha("Z")); # -> True
        print(isalpha("0")); # -> False
        print(isalpha("9")); # -> False
        print(isalpha("_")); # -> False
        print(isalpha("$")); # -> False

        None
    """)

    i.walk("""
        print("# isdigit");

        print(isdigit("a")); # -> False
        print(isdigit("z")); # -> False
        print(isdigit("A")); # -> False
        print(isdigit("Z")); # -> False
        print(isdigit("0")); # -> True
        print(isdigit("9")); # -> True
        print(isdigit("_")); # -> False
        print(isdigit("$")); # -> False

        None
    """)

    i.walk("""
        print("# isalnum");

        print(isalnum("a")); # -> True
        print(isalnum("z")); # -> True
        print(isalnum("A")); # -> True
        print(isalnum("Z")); # -> True
        print(isalnum("0")); # -> True
        print(isalnum("9")); # -> True
        print(isalnum("_")); # -> False
        print(isalnum("$")); # -> False

        None
    """)

    i.walk("""
        print("# is_name_first");

        print(is_name_first("a")); # -> True
        print(is_name_first("z")); # -> True
        print(is_name_first("A")); # -> True
        print(is_name_first("Z")); # -> True
        print(is_name_first("0")); # -> False
        print(is_name_first("9")); # -> False
        print(is_name_first("_")); # -> True
        print(is_name_first("$")); # -> False

        None
    """)

    i.walk("""
        print("# is_name_rest");

        print(is_name_rest("a")); # -> True
        print(is_name_rest("z")); # -> True
        print(is_name_rest("A")); # -> True
        print(is_name_rest("Z")); # -> True
        print(is_name_rest("0")); # -> True
        print(is_name_rest("9")); # -> True
        print(is_name_rest("_")); # -> True
        print(is_name_rest("$")); # -> False

        None
    """)

    i.walk("""
        print("# is_name");

        print(is_name(sym("a"))); # -> True
        print(is_name(sym("_abc"))); # -> True
        print(is_name(sym("0a"))); # -> False
        print(is_name(sym("$a"))); # -> False
        print(is_name("a")); # -> False

        None
    """)
