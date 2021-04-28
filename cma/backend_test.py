import unittest

from cma.backend import code, code_r, render_symbolic_addresses
from cma.frontend import C


class TestArithmeticCodeGeneration(unittest.TestCase):
    def test_simple_arithmetic_expression(self):
        data = "x = y - 1"
        environment = {"x": 4, "y": 7}
        (node,) = C.Expression.parseString(data, parseAll=True)
        result = list(code_r(node, environment))
        desired = ["loadc 7", "load", "loadc 1", "sub", "loadc 4", "store"]
        self.assertEqual(result, desired)


class TestStatementCodeGeneration(unittest.TestCase):
    def test_simple_statement_sequence(self):
        data = "x = 42; y = 2;"
        environment = {"x": 4, "y": 7}
        (node,) = C.StatementSequence.parseString(data, parseAll=True)
        result = list(code(node, environment))
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
        data = """
        if (x > y) 
            x = x - y; 
        else y = y - x;
        """
        environment = {"x": 4, "y": 7}
        (node,) = C.IfElse.parseString(data, parseAll=True)
        result = list(render_symbolic_addresses(code(node, environment)))
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
