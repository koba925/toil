#! /usr/bin/env python
import sys, time
t0 = tp = time.time()
for line in sys.stdin:
    tc = time.time()
    sys.stdout.write(f"[{tc-t0:7.3f}s] (+{tc-tp:7.3f}s) {line}")
    tp = tc
print(f"Total time: {time.time()-t0:.3f}s")
