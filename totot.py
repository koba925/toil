#! /usr/bin/env python
import sys; sys.setrecursionlimit(200000)
from toil import Interpreter

i = Interpreter().init_env().stdlib()
i.walk(r"""
    tot := load('tot.toil');
    tot.walk('
        print("Loading");
        totot := load("tot.toil");
        print("Walk");
        totot.walk("for i in [1, 2, 3] do print(i) end")
    ')
""")

# Result
#
# $ python -u totot.py | ./timestamp.py
# [  0.516s] (+  0.516s) Defining utility functions
# [  0.516s] (+  0.000s) Defining Scanner
# [  0.516s] (+  0.000s) Defining Parser
# [  0.516s] (+  0.000s) Defining Environment
# [  0.517s] (+  0.001s) Defining Evaluator
# [  0.518s] (+  0.001s) Defining Interpreter
# [  0.519s] (+  0.001s) Initializing interpreter
# [ 11.359s] (+ 10.840s) Defining first
# [ 11.364s] (+  0.006s) Defining rest
# [ 11.370s] (+  0.006s) Defining last
# [ 11.377s] (+  0.007s) Defining range
# [ 11.384s] (+  0.008s) Defining map
# [ 11.391s] (+  0.006s) Defining filter
# [ 11.401s] (+  0.010s) Defining zip
# [ 11.406s] (+  0.006s) Defining reduce
# [ 11.412s] (+  0.006s) Defining reverse
# [ 11.422s] (+  0.010s) Defining enumerate
# [ 11.431s] (+  0.009s) Defining all
# [ 11.439s] (+  0.008s) Defining any
# [ 11.987s] (+  0.547s) Loading
# [ 75.756s] (+ 63.770s) Defining utility functions
# [ 75.762s] (+  0.006s) Defining Scanner
# [ 75.765s] (+  0.003s) Defining Parser
# [ 75.768s] (+  0.003s) Defining Environment
# [ 75.771s] (+  0.003s) Defining Evaluator
# [ 75.774s] (+  0.003s) Defining Interpreter
# [ 75.777s] (+  0.003s) Initializing interpreter
# [284.590s] (+208.813s) Defining first
# [284.890s] (+  0.299s) Defining rest
# [285.179s] (+  0.289s) Defining last
# [285.476s] (+  0.297s) Defining range
# [285.914s] (+  0.438s) Defining map
# [286.383s] (+  0.469s) Defining filter
# [286.785s] (+  0.402s) Defining zip
# [287.223s] (+  0.438s) Defining reduce
# [287.653s] (+  0.430s) Defining reverse
# [288.077s] (+  0.425s) Defining enumerate
# [288.483s] (+  0.405s) Defining all
# [288.902s] (+  0.419s) Defining any
# [289.088s] (+  0.186s) Walk
# [305.365s] (+ 16.278s) 1
# [307.738s] (+  2.372s) 2
# [310.159s] (+  2.421s) 3
# Total time: 311.179s
