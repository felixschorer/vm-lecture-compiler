from dataclasses import dataclass
from typing import Any

from pyparsing import (
    Keyword,
    Optional,
    ParserElement,
    Suppress,
    Word,
    ZeroOrMore,
    alphas,
    delimitedList,
    infixNotation,
    oneOf,
    opAssoc,
    pyparsing_common,
)

from util.container import Container
from util.namespace import Namespace
from util.parse_action_for import parse_action_for

ParserElement.enablePackrat()


def in_brackets(opening: str, parser_element: ParserElement, closing: str):
    return Suppress(opening) + parser_element + Suppress(closing)


C = Namespace()

C.FOR = Keyword("for")
C.WHILE = Keyword("while")
C.SWITCH = Keyword("switch")
C.CASE = Keyword("case")
C.BREAK = Keyword("break")
C.DEFAULT = Keyword("default")

C.Keyword = C.FOR | C.WHILE | C.SWITCH | C.CASE | C.BREAK | C.DEFAULT

C.Constant = pyparsing_common.integer


@parse_action_for(C.Constant)
@dataclass(frozen=True)
class Constant:
    value: int


C.Identifier = ~C.Keyword + Word(alphas)


@parse_action_for(C.Identifier)
@dataclass(frozen=True)
class Identifier:
    name: str


C.FuncCallArguments = delimitedList(C.Expression)


@parse_action_for(C.FuncCallArguments)
class FuncCallArguments(Container):
    pass


C.FuncCall = C.Identifier + Suppress("(") + C.FuncCallArguments + Suppress(")")


@parse_action_for(C.FuncCall)
@dataclass(frozen=True)
class FuncCall:
    identifier: Identifier
    arguments: FuncCallArguments


C.Operand = C.FuncCall | C.Constant | C.LeftHandSide


def ungroup(groups):
    return [token for group in groups for token in group]


@dataclass(frozen=True)
class BinaryOp:
    left: Any
    op: str
    right: Any

    @classmethod
    def infix_notation(cls, *operators):
        def parse_action(_s, _loc, tokens):
            tokens = ungroup(tokens)
            while len(tokens) != 1:
                tokens = [cls(*tokens[:3]), *tokens[3:]]
            return tokens[0]

        return oneOf(operators), 2, opAssoc.LEFT, parse_action


@dataclass(frozen=True)
class UnaryOp:
    op: str
    expr: Any

    @classmethod
    def infix_notation(cls, *operators):
        def parse_action(_s, _loc, tokens):
            tokens = ungroup(tokens)
            return cls(*tokens)

        return oneOf(operators), 1, opAssoc.RIGHT, parse_action


C.Operation = infixNotation(
    C.Operand,
    [
        # https://en.cppreference.com/w/c/language/operator_precedence
        UnaryOp.infix_notation("-", "!"),
        BinaryOp.infix_notation("*", "/", "%"),
        BinaryOp.infix_notation("+", "-"),
        BinaryOp.infix_notation("<", "<=", ">", ">="),
        BinaryOp.infix_notation("==", "!="),
        BinaryOp.infix_notation("^"),
        BinaryOp.infix_notation("&&"),
        BinaryOp.infix_notation("||"),
    ],
)

C.LeftHandSide = C.Identifier + ZeroOrMore(
    ("[" + C.Expression + "]") | ("->" + C.Identifier) | ("." + C.Identifier)
)


@dataclass(frozen=True)
class ArrayAccess:
    accessee: Any
    expr: Any


@dataclass(frozen=True)
class StructAccess:
    accessee: Any
    field: Identifier


@dataclass(frozen=True)
class StructPointerAccess:
    accessee: Any
    pointer: Identifier


@parse_action_for(C.LeftHandSide)
def parse_left_hand_side(*tokens):
    while len(tokens) != 1:
        if tokens[1] == "[":
            tokens = [ArrayAccess(tokens[0], tokens[2]), *tokens[4:]]
        elif tokens[1] == "->":
            tokens = [StructPointerAccess(tokens[0], tokens[2]), *tokens[3:]]
        elif tokens[1] == ".":
            tokens = [StructAccess(tokens[0], tokens[2]), *tokens[3:]]
        else:
            raise AssertionError("Unsupported left hand side")
    return tokens[0]


C.Assignment = C.LeftHandSide + Suppress("=") + C.Expression


@parse_action_for(C.Assignment)
@dataclass(frozen=True)
class Assignment:
    left: Any
    right: Any


C.Expression = C.Assignment | C.Operation

C.PlainStatement = C.Expression + Suppress(";")


@parse_action_for(C.PlainStatement)
@dataclass(frozen=True)
class PlainStatement:
    expr: Any


C.Block = in_brackets("{", C.StatementSequence, "}")
C.BlockOrStatement = C.Statement | C.Block

C.If = Suppress("if") + in_brackets("(", C.Expression, ")") + C.BlockOrStatement
C.Else = Suppress("else") + C.BlockOrStatement
C.IfElse = C.If + Optional(C.Else)


@parse_action_for(C.IfElse)
@dataclass(frozen=True)
class IfElse:
    expr: Any
    then_branch: Any
    else_branch: Any = None


C.While = Suppress("while") + in_brackets("(", C.Expression, ")") + C.BlockOrStatement


@parse_action_for(C.While)
@dataclass(frozen=True)
class While:
    expr: Any
    body: Any


C.ForExpressions = (
    C.Expression + Suppress(";") + C.Expression + Suppress(";") + C.Expression
)
C.For = Suppress("for") + in_brackets("(", C.ForExpressions, ")") + C.BlockOrStatement


@parse_action_for(C.For)
@dataclass(frozen=True)
class For:
    expr1: Any
    expr2: Any
    expr3: Any
    body: Any


C.Case = (
    Suppress("case")
    + C.Constant
    + Suppress(":")
    + C.StatementSequence
    + Suppress("break;")
)


@parse_action_for(C.Case)
@dataclass(frozen=True)
class Case:
    value: Any
    body: Any


C.Cases = ZeroOrMore(C.Case)


@parse_action_for(C.Cases)
class Cases(Container):
    pass


C.Switch = (
    Suppress("switch")
    + in_brackets("(", C.Expression, ")")
    + in_brackets("{", C.Cases + Suppress("default:") + C.StatementSequence, "}")
)


@parse_action_for(C.Switch)
@dataclass(frozen=True)
class Switch:
    expr: Any
    cases: Any
    default_case: Any


C.Statement = C.PlainStatement | C.IfElse | C.While | C.For | C.Switch

C.StatementSequence = ZeroOrMore(C.Statement)


@parse_action_for(C.StatementSequence)
class StatementSequence(Container):
    pass
