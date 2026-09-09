from toil import Toil
Toil().walk(r"""
def foo() do
    break
end;

i := 0; while i < 4 do
    print(i);
    foo();
    i = i + 1
end
""")
