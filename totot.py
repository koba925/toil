#! /usr/bin/env python
import sys; sys.setrecursionlimit(200000)
import time
from toil import Interpreter

t0 = time.time()
print("Start")

i = Interpreter().init_env().stdlib()
i.walk(r"""
    print("Loading ToT");
    tot := load('tot.toil');
    tot.walk('
        print("Loading ToToT");
        totot := load("tot.toil");
        print("Walk");
        totot.walk("for i in [1, 2, 3] do print(i) end");
        totot.walk("for i in [1, 2, 3].filter(x -> x % 2 == 1) do print(i) end")
    ')
""")

print(f"Total time: {time.time() - t0:.3f}s")
