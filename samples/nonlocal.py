def foo(a):
    def bar():
        nonlocal a
        print(a)
        a = 3

    bar()
    print(a)

foo(2)
