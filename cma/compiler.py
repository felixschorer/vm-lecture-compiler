from cma.frontend.parser import C

test = [
    "test(3 + test(42))",
]
for t in test:
    print(t)
    print(C.Expression.parseString(t))
    print("")
