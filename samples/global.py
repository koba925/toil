a = 2

def bar():
    global a
    print(a)
    a = 3

bar()
print(a)
