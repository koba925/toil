#! /usr/bin/env python3

from toil import Interpreter

class ToTWrapper:
    def __init__(self, go):
        self._go = go

    def scan(self, src): return self._go(f""" tot.scan('{src}') """)
    def parse(self, tokens): return self._go(f""" tot.parse({tokens}) """)
    def ast(self, src): return self._go(f""" tot.ast('{src}') """)
    def eval(self, ast): return self._go(f""" tot.eval({ast}) """)
    def walk(self, src): return self._go(f""" tot.walk('{src}') """)


if __name__ == "__main__":
    import sys
    sys.setrecursionlimit(200000)

    toil = Interpreter().init_env().stdlib()
    go = toil.run if len(sys.argv) > 1 and sys.argv[1] == "--run" else toil.walk

    go(r"""
        {Interpreter} := load('toil.toil');
        tot := Interpreter().init_env().stdlib()
    """)

    tot = ToTWrapper(go)

    # Example

    print(tot.walk(r""" match 2 case int(a) | str(a) then [a] end """)) # -> [2]
    print(tot.walk(r""" match "aaa" case int(a) | str(a) then [a] end """)) # -> ['aaa']
    print(tot.walk(r""" match [2] case int(a) | str(a) then [a] end """)) # -> None
    print(tot.walk(r""" match [2] case int(a) | str(a) | list(a) then [a] end """)) # -> [[2]]
