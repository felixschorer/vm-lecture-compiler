from dataclasses import dataclass
from typing import Any, List

from pyparsing import (
    Group,
    ParserElement,
    Suppress,
    Word,
    alphas,
    delimitedList,
    infixNotation,
    oneOf,
    opAssoc,
    pyparsing_common,
)

from namespace import Namespace
from parse_action_for import parse_action_for

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


C.LValue = C.Identifier


C.FuncCallArguments = delimitedList(C.Expression)


@parse_action_for(C.FuncCallArguments)
def group_func_call_arguments(*tokens):
    return tokens


C.FuncCall = C.Identifier + Suppress("(") + C.FuncCallArguments + Suppress(")")


@parse_action_for(C.FuncCall)
@dataclass(frozen=True)
class FuncCall:
    identifier: Identifier
    arguments: List[Any]


C.Operand = C.FuncCall | C.Constant | C.Identifier


def ungroup(groups):
    return [token for group in groups for token in group]


@dataclass(frozen=True)
class BinaryOp:
    left: Any
    op: str
    right: Any

    @classmethod
    def infix_notation(cls, operator, assoc):
        def parse_action(_s, _loc, tokens):
            tokens = ungroup(tokens)
            if assoc == opAssoc.LEFT:
                while len(tokens) != 1:
                    tokens = [cls(*tokens[:3]), *tokens[3:]]
            else:
                while len(tokens) != 1:
                    tokens = [*tokens[:-3], cls(*tokens[-3:])]
            return tokens[0]

        return operator, 2, assoc, parse_action


@dataclass(frozen=True)
class UnaryOp:
    op: str
    expr: Any

    @classmethod
    def infix_notation(cls, operator):
        def parse_action(_s, _loc, tokens):
            tokens = ungroup(tokens)
            return cls(*tokens)

        return operator, 1, opAssoc.RIGHT, parse_action


C.Operation = infixNotation(
    C.Operand,
    [
        UnaryOp.infix_notation(oneOf("+ -")),
        BinaryOp.infix_notation(oneOf("* /"), opAssoc.LEFT),
        BinaryOp.infix_notation(oneOf("+ -"), opAssoc.LEFT),
    ],
)

C.Assignment = C.LValue + Suppress("=") + C.Expression


@parse_action_for(C.Assignment)
@dataclass(frozen=True)
class Assignment:
    left: Any
    right: Any


C.Expression = C.Assignment | C.Operation
