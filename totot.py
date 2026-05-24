#! /usr/bin/env python
import sys; sys.setrecursionlimit(200000)
import time
from toil import Interpreter

t0 = time.time()

ici = len(sys.argv) > 1 and sys.argv[1] == "--run"
i = Interpreter().init_env().stdlib()

code = f"""
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

if ici:
    print("Running"); i.run(code)
else:
    print("Walking"); i.walk(code)

print(f"Total time: {time.time() - t0:.3f}s")
