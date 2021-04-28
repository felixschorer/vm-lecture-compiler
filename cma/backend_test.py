import unittest
from cma.backend import code_r
from cma.frontend import C


class TestArithmeticCodeGeneration(unittest.TestCase):
    def test_simple_arithmetic_expression(self):
        code = "x = y - 1"
        environment = {"x": 4, "y": 7}
        (node,) = C.Expression.parseString(code, parseAll=True)
        result = list(code_r(node, environment))
        desired = ["loadc 7", "load", "loadc 1", "sub", "loadc 4", "store"]
        self.assertEqual(result, desired)
