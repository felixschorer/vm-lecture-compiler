from dataclasses import dataclass
from typing import Any, Tuple

from pyparsing import (
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

C = Namespace()

C.Constant = pyparsing_common.integer


@parse_action_for(C.Constant)
@dataclass(frozen=True)
class Constant:
    value: int


C.Identifier = Word(alphas)


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


C.Operand = C.FuncCall | C.Constant | C.Identifier


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

C.LeftHandSide = C.Identifier

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


C.Statement = C.PlainStatement

C.StatementSequence = ZeroOrMore(C.Statement)


@parse_action_for(C.StatementSequence)
class StatementSequence(Container):
    pass
