#! /usr/bin/env python3

from toil import Interpreter

class ToTWrapper:
    def __init__(self, toil): self._toil = toil
    def scan(self, src): return self._toil.walk(f""" tot.scan('{src}') """)
    def parse(self, tokens): return self._toil.walk(f""" tot.parse({tokens}) """)
    def ast(self, src): return self._toil.walk(f""" tot.ast('{src}') """)
    def eval(self, ast): return self._toil.walk(f""" tot.eval({ast}) """)
    def walk(self, src): return self._toil.walk(f""" tot.walk('{src}') """)


if __name__ == "__main__":
    import sys
    sys.setrecursionlimit(200000)

    toil = Interpreter().init_env().stdlib()
    toil.walk(r"""
        {Interpreter} := load('toil.toil');
        tot := Interpreter().init_env().stdlib()
    """)

    tot = ToTWrapper(toil)

    # Example

    print(tot.walk(r""" match 2 case int(a) | str(a) then [a] end """)) # -> [2]
    print(tot.walk(r""" match "aaa" case int(a) | str(a) then [a] end """)) # -> ['aaa']
    print(tot.walk(r""" match [2] case int(a) | str(a) then [a] end """)) # -> None
    print(tot.walk(r""" match [2] case int(a) | str(a) | list(a) then [a] end """)) # -> [[2]]
