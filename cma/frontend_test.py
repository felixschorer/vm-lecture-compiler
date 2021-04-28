import unittest

from pyparsing import ParseException

from cma.frontend import (
    Assignment,
    BinaryOp,
    C,
    Constant,
    FuncCall,
    FuncCallArguments,
    Identifier,
    PlainStatement,
    UnaryOp,
)


class TestParserConstant(unittest.TestCase):
    def test_parsing_constant(self):
        data = "42"
        result = C.Expression.parseString(data, parseAll=True).asList()
        desired = [Constant(value=42)]
        self.assertEqual(result, desired)

    def test_parsing_constant_truncation(self):
        data = "42 43"
        with self.assertRaises(ParseException):
            C.Expression.parseString(data, parseAll=True)


class TestParserIdentifier(unittest.TestCase):
    def test_parsing_identifier(self):
        data = "asdf"
        result = C.Expression.parseString(data, parseAll=True).asList()
        desired = [Identifier(name="asdf")]
        self.assertEqual(result, desired)

    def test_parsing_identifier_truncation(self):
        data = "asdf asdf"
        with self.assertRaises(ParseException):
            C.Expression.parseString(data, parseAll=True)


class TestParserBinOp(unittest.TestCase):
    def test_parsing_binop_minus_constants(self):
        data = "42 - 1"
        result = C.Expression.parseString(data, parseAll=True).asList()
        desired = [BinaryOp(left=Constant(value=42), op="-", right=Constant(value=1))]
        self.assertEqual(result, desired)

    def test_parsing_binop_plus_identifier(self):
        data = "a + b"
        result = C.Expression.parseString(data, parseAll=True).asList()
        desired = [
            BinaryOp(left=Identifier(name="a"), op="+", right=Identifier(name="b"))
        ]
        self.assertEqual(result, desired)

    def test_parsing_binop_precedence(self):
        data = "3 + d / 5"
        result = C.Expression.parseString(data, parseAll=True).asList()
        desired = [
            BinaryOp(
                left=Constant(value=3),
                op="+",
                right=BinaryOp(
                    left=Identifier(name="d"), op="/", right=Constant(value=5)
                ),
            )
        ]
        self.assertEqual(result, desired)


class TestParserUnaryOp(unittest.TestCase):
    def test_parsing_unaryop_minus_constants(self):
        data = "-1"
        result = C.Expression.parseString(data, parseAll=True).asList()
        desired = [UnaryOp(op="-", expr=Constant(value=1))]
        self.assertEqual(result, desired)


class TestParserAssignment(unittest.TestCase):
    def test_parsing_correct_constant_assignment(self):
        data = "x = 3"
        result = C.Expression.parseString(data, parseAll=True).asList()
        desired = [Assignment(left=Identifier(name="x"), right=Constant(value=3))]
        self.assertEqual(result, desired)

    def test_parsing_incorrect_constant_assignment(self):
        data = "3 = 3"
        with self.assertRaises(ParseException):
            C.Expression.parseString(data, parseAll=True)

    def test_parsing_correct_binop_assignment(self):
        data = "x = 3 + y"
        result = C.Expression.parseString(data, parseAll=True).asList()
        desired = [
            Assignment(
                left=Identifier(name="x"),
                right=BinaryOp(
                    left=Constant(value=3), op="+", right=Identifier(name="y")
                ),
            )
        ]
        self.assertEqual(result, desired)

    def test_parsing_incorrect_binop_assignment(self):
        data = "3 + 3 = x"
        with self.assertRaises(ParseException):
            C.Expression.parseString(data, parseAll=True)


class TestParserFuncCall(unittest.TestCase):
    def test_parsing_func_call(self):
        data = "fib(n - 1) + fib(n - 2)"
        result = C.Expression.parseString(data, parseAll=True).asList()
        desired = [
            BinaryOp(
                left=FuncCall(
                    identifier=Identifier(name="fib"),
                    arguments=FuncCallArguments(
                        BinaryOp(
                            left=Identifier(name="n"), op="-", right=Constant(value=1)
                        ),
                    ),
                ),
                op="+",
                right=FuncCall(
                    identifier=Identifier(name="fib"),
                    arguments=FuncCallArguments(
                        BinaryOp(
                            left=Identifier(name="n"), op="-", right=Constant(value=2)
                        ),
                    ),
                ),
            )
        ]
        self.assertEqual(result, desired)
