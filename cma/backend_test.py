import unittest

from cma.backend import code, code_r, render_symbolic_addresses
from cma.frontend import C


def generate_expression_code(c_code, environment):
    (node,) = C.Expression.parseString(c_code, parseAll=True)
    return list(render_symbolic_addresses(code_r(node, environment)))


def generate_statement_code(c_code, environment):
    (node,) = C.StatementSequence.parseString(c_code, parseAll=True)
    return list(render_symbolic_addresses(code(node, environment)))


class TestArithmeticCodeGeneration(unittest.TestCase):
    def test_simple_arithmetic_expression(self):
        c_code = "x = y - 1"
        environment = {"x": 4, "y": 7}
        result = generate_expression_code(c_code, environment)
        desired = ["loadc 7", "load", "loadc 1", "sub", "loadc 4", "store"]
        self.assertEqual(result, desired)


class TestStatementCodeGeneration(unittest.TestCase):
    def test_simple_statement_sequence(self):
        c_code = "x = 42; y = 2;"
        environment = {"x": 4, "y": 7}
        result = generate_statement_code(c_code, environment)
        desired = [
            "loadc 42",
            "loadc 4",
            "store",
            "pop",
            "loadc 2",
            "loadc 7",
            "store",
            "pop",
        ]
        self.assertEqual(result, desired)

    def test_simple_if_else_statement(self):
        c_code = """
        if (x > y) 
            x = x - y; 
        else y = y - x;
        """
        environment = {"x": 4, "y": 7}
        result = generate_statement_code(c_code, environment)
        desired = [
            "loadc 4",
            "load",
            "loadc 7",
            "load",
            "gr",
            "jumpz 15",
            "loadc 4",
            "load",
            "loadc 7",
            "load",
            "sub",
            "loadc 4",
            "store",
            "pop",
            "jump 23",
            "loadc 7",
            "load",
            "loadc 4",
            "load",
            "sub",
            "loadc 7",
            "store",
            "pop",
        ]
        self.assertEqual(result, desired)
