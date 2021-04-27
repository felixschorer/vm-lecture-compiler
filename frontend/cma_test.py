from frontend.cma import C

test = [
    "func(x = 42)",
]
for t in test:
    print(t)
    print(C.Expression.parseString(t))
    print("")

