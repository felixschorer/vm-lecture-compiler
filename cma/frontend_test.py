import unittest

from pyparsing import ParseException

from cma.frontend import (
    Assignment,
    BinaryOp,
    C,
    Case,
    Cases,
    Constant,
    For,
    FuncCall,
    FuncCallArguments,
    Identifier,
    IfElse,
    PlainStatement,
    StatementSequence,
    Switch,
    UnaryOp,
    While,
    ArrayAccess
)


class TestParserConstant(unittest.TestCase):
    def test_parsing_constant(self):
        data = "42"
        (result,) = C.Expression.parseString(data, parseAll=True)
        desired = Constant(value=42)
        self.assertEqual(result, desired)

    def test_parsing_constant_truncation(self):
        data = "42 43"
        with self.assertRaises(ParseException):
            C.Expression.parseString(data, parseAll=True)


class TestParserIdentifier(unittest.TestCase):
    def test_parsing_identifier(self):
        data = "asdf"
        (result,) = C.Expression.parseString(data, parseAll=True)
        desired = Identifier(name="asdf")
        self.assertEqual(result, desired)

    def test_parsing_identifier_truncation(self):
        data = "asdf asdf"
        with self.assertRaises(ParseException):
            C.Expression.parseString(data, parseAll=True)


class TestParserBinOp(unittest.TestCase):
    def test_parsing_binop_minus_constants(self):
        data = "42 - 1"
        (result,) = C.Expression.parseString(data, parseAll=True)
        desired = BinaryOp(left=Constant(value=42),
                           op="-", right=Constant(value=1))
        self.assertEqual(result, desired)

    def test_parsing_binop_plus_identifier(self):
        data = "a + b"
        (result,) = C.Expression.parseString(data, parseAll=True).asList()
        desired = BinaryOp(
            left=Identifier(name="a"), op="+", right=Identifier(name="b")
        )
        self.assertEqual(result, desired)

    def test_parsing_binop_precedence(self):
        data = "3 + d / 5"
        (result,) = C.Expression.parseString(data, parseAll=True)
        desired = BinaryOp(
            left=Constant(value=3),
            op="+",
            right=BinaryOp(left=Identifier(name="d"),
                           op="/", right=Constant(value=5)),
        )
        self.assertEqual(result, desired)


class TestParserUnaryOp(unittest.TestCase):
    def test_parsing_unaryop_minus_constants(self):
        data = "-1"
        (result,) = C.Expression.parseString(data, parseAll=True)
        desired = UnaryOp(op="-", expr=Constant(value=1))
        self.assertEqual(result, desired)


class TestParserAssignment(unittest.TestCase):
    def test_parsing_correct_constant_assignment(self):
        data = "x = 3"
        (result,) = C.Expression.parseString(data, parseAll=True)
        desired = Assignment(left=Identifier(
            name="x"), right=Constant(value=3))
        self.assertEqual(result, desired)

    def test_parsing_incorrect_constant_assignment(self):
        data = "3 = 3"
        with self.assertRaises(ParseException):
            C.Expression.parseString(data, parseAll=True)

    def test_parsing_correct_binop_assignment(self):
        data = "x = 3 + y"
        (result,) = C.Expression.parseString(data, parseAll=True)
        desired = Assignment(
            left=Identifier(name="x"),
            right=BinaryOp(left=Constant(value=3), op="+",
                           right=Identifier(name="y")),
        )
        self.assertEqual(result, desired)

    def test_parsing_incorrect_binop_assignment(self):
        data = "3 + 3 = x"
        with self.assertRaises(ParseException):
            C.Expression.parseString(data, parseAll=True)


class TestParserFuncCall(unittest.TestCase):
    def test_parsing_func_call(self):
        data = "fib(n - 1) + fib(n - 2)"
        (result,) = C.Expression.parseString(data, parseAll=True)
        desired = BinaryOp(
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
        self.assertEqual(result, desired)


class TestArrayAccess(unittest.TestCase):
    def test_simple_array_assignment(self):
        data = "a[2] = 42"
        (result,) = C.Expression.parseString(data, parseAll=True)
        desired = Assignment(left=ArrayAccess(identifier=Identifier(
            name='a'), expr=Constant(value=2)), right=Constant(value=42))
        self.assertEqual(result, desired)

    def test_simple_array_access(self):
        data = "b = a[1]"
        (result,) = C.Expression.parseString(data, parseAll=True)
        desired = Assignment(left=Identifier(name='b'), right=ArrayAccess(
            identifier=Identifier(name='a'), expr=Constant(value=1)))
        self.assertEqual(result, desired)


class TestParserStatement(unittest.TestCase):
    def test_parse_plain_statement(self):
        data = "x = 42;"
        (result,) = C.Statement.parseString(data, parseAll=True)
        desired = PlainStatement(
            expr=Assignment(left=Identifier(name="x"),
                            right=Constant(value=42))
        )
        self.assertEqual(result, desired)

    def test_parse_statements(self):
        data = "x = 42; y = 2;"
        (result,) = C.StatementSequence.parseString(data, parseAll=True)
        desired = StatementSequence(
            PlainStatement(
                expr=Assignment(left=Identifier(name="x"),
                                right=Constant(value=42))
            ),
            PlainStatement(
                expr=Assignment(left=Identifier(name="y"),
                                right=Constant(value=2))
            ),
        )
        self.assertEqual(result, desired)

    def test_parse_incorrect_statements(self):
        data = "x = 42; y = 2"
        with self.assertRaises(ParseException):
            C.StatementSequence.parseString(data, parseAll=True)

    def test_parse_if_else_if_statement(self):
        data = "if (x < 0) x = 0; else if (1 < x) x = 1;"
        (result,) = C.Statement.parseString(data, parseAll=True)
        desired = IfElse(
            expr=BinaryOp(left=Identifier(name="x"),
                          op="<", right=Constant(value=0)),
            then_branch=PlainStatement(
                expr=Assignment(left=Identifier(name="x"),
                                right=Constant(value=0))
            ),
            else_branch=IfElse(
                expr=BinaryOp(
                    left=Constant(value=1), op="<", right=Identifier(name="x")
                ),
                then_branch=PlainStatement(
                    expr=Assignment(left=Identifier(name="x"),
                                    right=Constant(value=1))
                ),
                else_branch=None,
            ),
        )
        self.assertEqual(result, desired)

    def test_parse_while_statement(self):
        data = "while (a > 0) { c = c + 1; a = a - b; }"
        (result,) = C.Statement.parseString(data, parseAll=True)
        desired = While(
            expr=BinaryOp(left=Identifier(name="a"),
                          op=">", right=Constant(value=0)),
            body=StatementSequence(
                PlainStatement(
                    expr=Assignment(
                        left=Identifier(name="c"),
                        right=BinaryOp(
                            left=Identifier(name="c"), op="+", right=Constant(value=1)
                        ),
                    )
                ),
                PlainStatement(
                    expr=Assignment(
                        left=Identifier(name="a"),
                        right=BinaryOp(
                            left=Identifier(name="a"),
                            op="-",
                            right=Identifier(name="b"),
                        ),
                    )
                ),
            ),
        )
        self.assertEqual(result, desired)

    def test_parse_for_statement(self):
        data = "for (i = 0; i < 10; i = i + 1) x = x * i;"
        (result,) = C.Statement.parseString(data, parseAll=True)
        desired = For(
            expr1=Assignment(left=Identifier(name="i"),
                             right=Constant(value=0)),
            expr2=BinaryOp(left=Identifier(name="i"),
                           op="<", right=Constant(value=10)),
            expr3=Assignment(
                left=Identifier(name="i"),
                right=BinaryOp(
                    left=Identifier(name="i"), op="+", right=Constant(value=1)
                ),
            ),
            body=PlainStatement(
                expr=Assignment(
                    left=Identifier(name="x"),
                    right=BinaryOp(
                        left=Identifier(name="x"), op="*", right=Identifier(name="i")
                    ),
                )
            ),
        )
        self.assertEqual(result, desired)

    def test_parse_switch_statement(self):
        data = """
        switch (x) {
            case 0:
                x = 1;
                y = x;
                break;
            case 1:
                break;
            default:
                x = 1;
        }
        """
        (result,) = C.Statement.parseString(data, parseAll=True)
        desired = Switch(
            expr=Identifier(name="x"),
            cases=Cases(
                Case(
                    value=Constant(value=0),
                    body=StatementSequence(
                        PlainStatement(
                            expr=Assignment(
                                left=Identifier(name="x"), right=Constant(value=1)
                            )
                        ),
                        PlainStatement(
                            expr=Assignment(
                                left=Identifier(name="y"), right=Identifier(name="x")
                            )
                        ),
                    ),
                ),
                Case(value=Constant(value=1), body=StatementSequence()),
            ),
            default_case=StatementSequence(
                PlainStatement(
                    expr=Assignment(left=Identifier(name="x"),
                                    right=Constant(value=1))
                )
            ),
        )
        self.assertEqual(result, desired)
