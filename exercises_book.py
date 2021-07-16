import cma.backend
from cma.backend_test import (
    basic_addr,
    generate_expression_code,
    generate_statement_code,
)


def e1_1():
    c_code = "a = 2*(c+(b-3))"
    environment = {"a": basic_addr(5), "b": basic_addr(6), "c": basic_addr(7)}
    result = generate_expression_code(c_code, environment)
    print(f"e1.1: {result}")


def e1_2():
    c_code = "b = b*(a+3)"
    environment = {"a": basic_addr(5), "b": basic_addr(6), "c": basic_addr(7)}
    result = generate_expression_code(c_code, environment)
    print(f"e1.2: {result}")


def e2_1():
    c_code = "while (x > y) { if(2 * y > x){ y = y + x; } else{ x = x - y;}} "
    environment = {"x": basic_addr(2), "y": basic_addr(3), "z": basic_addr(5)}
    result = generate_statement_code(c_code, environment)
    print(f"e2.1: {result}")


def e2_2():
    # TODO: Fix frontend to parse ! correctly in the following line
    # c_code = "for (x=0; x < 42; x = x + z){ if(!(x = y)){z = z + 1;}}"
    c_code = "for (x=0; x < 42; x = x + z){ if(x = y){z = z + 1;}}"
    environment = {"x": basic_addr(2), "y": basic_addr(3), "z": basic_addr(5)}
    result = generate_statement_code(c_code, environment)
    print(f"e2.2: {result}")


def e3():
    c_code = "z = 1; while (n > 0) { j = 1; y = x; while (2 * j <= n) { y = y * y; j = j * 2; } z = y * z; n = n - j; } "
    environment = {
        "n": basic_addr(1),
        "j": basic_addr(2),
        "x": basic_addr(3),
        "y": basic_addr(4),
        "z": basic_addr(5),
    }
    result = generate_statement_code(c_code, environment)
    print(f"e3: {result}")


e1_1()
e1_2()
e2_1()
e2_2()
e3()
