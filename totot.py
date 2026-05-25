#! /usr/bin/env python
import sys; sys.setrecursionlimit(200000)
import time
from toil_final import Interpreter

t0 = time.time()

ici = len(sys.argv) > 1 and sys.argv[1] == "--run"
print("Running" if ici else "Walking")
jit = len(sys.argv) > 1 and sys.argv[1] == "--jit"
print("JIT enabled" if jit else "JIT disabled")

i = Interpreter().init_env().stdlib()

code = f"""
    __jit__ := {jit};
    print("Loading ToT");
    {{Interpreter}} := load("toil.toil", {ici});
    tot := Interpreter().init_env().stdlib();
    print("Walk");
    tot.walk('
        print("Loading ToToT");
        {{Interpreter}} := load("toil.toil");
        totot := Interpreter().init_env().stdlib();
        print("Walk");
        totot.walk("for i in [1, 2, 3] do print(i) end");
        totot.walk("for i in [1, 2, 3].filter(x -> x % 2 == 1) do print(i) end")
    ')
"""

i.run(code) if ici else i.walk(code)

print(f"Total time: {time.time() - t0:.3f}s")
