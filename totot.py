#! /usr/bin/env python
import sys; sys.setrecursionlimit(200000)
import time
from toil import Interpreter

t0 = time.time()

i = Interpreter().init_env().stdlib()
i.walk(r"""
    tot := load('tot.toil');
    tot.walk('
        print("Loading");
        totot := load("tot.toil");
        print("Walk");
        totot.walk("for i in [1, 2, 3] do print(i) end");
        totot.walk("for i in [1, 2, 3].filter(x -> x % 2 == 1) do print(i) end")
    ')
""")

print(f"Total time: {time.time() - t0:.3f}s")

# Result
#
# Debug run
#
# l$  cd /workspaces/toil ; /usr/bin/env /usr/local/bin/python /home/vscode/.vscode-server/extensions/ms-python.debugpy-2025.18.0-linux-x64/bundled/libs/debugpy/adapter/../../debugpy/launcher 58809 -- /workspaces/toil/totot.py
# Defining utility functions
# Defining Scanner
# Defining Parser
# Defining Environment
# Defining Evaluator
# Defining Interpreter
# Initializing interpreter
# Defining first
# Defining rest
# Defining last
# Defining range
# Defining map
# Defining filter
# Defining zip
# Defining reduce
# Defining reverse
# Defining enumerate
# Defining all
# Defining any
# Loading
# Defining utility functions
# Defining Scanner
# Defining Parser
# Defining Environment
# Defining Evaluator
# Defining Interpreter
# Initializing interpreter
# Defining first
# Defining rest
# Defining last
# Defining range
# Defining map
# Defining filter
# Defining zip
# Defining reduce
# Defining reverse
# Defining enumerate
# Defining all
# Defining any
# Walk
# 1
# 2
# 3
# 1
# 3
# Total time: 4948.066s
#
# Run from command line
# # $ python -u totot.py | ./timestamp.py
# [  0.502s] (+  0.502s) Defining utility functions
# [  0.502s] (+  0.000s) Defining Scanner
# [  0.502s] (+  0.000s) Defining Parser
# [  0.502s] (+  0.000s) Defining Environment
# [  0.502s] (+  0.000s) Defining Evaluator
# [  0.502s] (+  0.000s) Defining Interpreter
# [  0.502s] (+  0.000s) Initializing interpreter
# [ 11.173s] (+ 10.671s) Defining first
# [ 11.179s] (+  0.006s) Defining rest
# [ 11.190s] (+  0.010s) Defining last
# [ 11.197s] (+  0.007s) Defining range
# [ 11.206s] (+  0.010s) Defining map
# [ 11.215s] (+  0.009s) Defining filter
# [ 11.224s] (+  0.009s) Defining zip
# [ 11.232s] (+  0.008s) Defining reduce
# [ 11.243s] (+  0.011s) Defining reverse
# [ 11.252s] (+  0.009s) Defining enumerate
# [ 11.262s] (+  0.010s) Defining all
# [ 11.266s] (+  0.004s) Defining any
# [ 12.191s] (+  0.925s) Loading
# [ 82.321s] (+ 70.129s) Defining utility functions
# [ 82.327s] (+  0.007s) Defining Scanner
# [ 82.330s] (+  0.002s) Defining Parser
# [ 82.332s] (+  0.003s) Defining Environment
# [ 82.335s] (+  0.003s) Defining Evaluator
# [ 82.339s] (+  0.004s) Defining Interpreter
# [ 82.344s] (+  0.005s) Initializing interpreter
# [290.874s] (+208.529s) Defining first
# [291.111s] (+  0.238s) Defining rest
# [291.344s] (+  0.233s) Defining last
# [291.590s] (+  0.246s) Defining range
# [291.820s] (+  0.230s) Defining map
# [292.097s] (+  0.277s) Defining filter
# [292.409s] (+  0.312s) Defining zip
# [292.738s] (+  0.328s) Defining reduce
# [293.094s] (+  0.356s) Defining reverse
# [293.440s] (+  0.346s) Defining enumerate
# [293.765s] (+  0.325s) Defining all
# [294.101s] (+  0.336s) Defining any
# [294.297s] (+  0.196s) Walk
# [308.145s] (+ 13.848s) 1
# [308.536s] (+  0.391s) 2
# [308.925s] (+  0.390s) 3
# [332.508s] (+ 23.582s) 1
# [332.707s] (+  0.199s) 3
# [332.720s] (+  0.013s) Total time: 332.671s
