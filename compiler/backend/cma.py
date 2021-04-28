from compiler.frontend.cma import Assignment, BinaryOp, Constant, Identifier, UnaryOp
from typing import Any, Dict

BINARY_OP_TO_INSTR = {
    "*": "mul",
    "/": "div",
    "%": "mod",
    "+": "add",
    "-": "sub",
    "<": "le",
    "<=": "leq",
    ">": "gr",
    ">=": "geq",
    "==": "eq",
    "!=": "neq",
    "^": "xor",
    "&&": "and",
    "||": "or",
}


UNARY_OP_TO_INSTR = {"-": "neg", "!": "not"}


def code_l(node: Any, environment: Dict[str, int]):
    if isinstance(node, Identifier):
        yield f"loadc {environment[node.name]}"
    else:
        raise AssertionError(f"Cannot generate code_l for {repr(node)}")


def code_r(node: Any, environment: Dict[str, int]):
    if isinstance(node, BinaryOp):
        yield from code_r(node.left, environment)
        yield from code_r(node.right, environment)
        yield BINARY_OP_TO_INSTR[node.op]
    elif isinstance(node, UnaryOp):
        yield from code_r(node.expr, environment)
        yield UNARY_OP_TO_INSTR[node.op]
    elif isinstance(node, Constant):
        yield f"loadc {node.value}"
    elif isinstance(node, Identifier):
        yield from code_l(node, environment)
        yield "load"
    elif isinstance(node, Assignment):
        yield from code_r(node.right, environment)
        yield from code_l(node.left, environment)
        yield "store"
    else:
        raise AssertionError(f"Cannot generate code_r for {repr(node)}")
