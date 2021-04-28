from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, Optional

from cma.frontend import (
    Assignment,
    BinaryOp,
    Constant,
    Identifier,
    IfElse,
    PlainStatement,
    StatementSequence,
    UnaryOp,
)


@dataclass
class SymbolicAddress:
    real_address: Optional[int] = None


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


def code(node: Any, environment: Dict[str, int]):
    if isinstance(node, PlainStatement):
        yield from code_r(node.expr, environment)
        yield "pop"
    elif isinstance(node, StatementSequence):
        for statement in node:
            yield from code(statement, environment)
    elif isinstance(node, IfElse) and node.else_branch is None:
        a = SymbolicAddress()
        yield from code_r(node.expr, environment)
        yield "jumpz", a
        yield from code(node.then_branch, environment)
        yield a
    elif isinstance(node, IfElse) and node.else_branch is not None:
        a = SymbolicAddress()
        b = SymbolicAddress()
        yield from code_r(node.expr, environment)
        yield "jumpz", a
        yield from code(node.then_branch, environment)
        yield "jump", b
        yield a
        yield from code(node.else_branch, environment)
        yield b
    else:
        raise AssertionError(f"Cannot generate code for {repr(node)}")


def render_symbolic_addresses(symbolic_code):
    curr_real_address = 0
    unprinted_instructions = deque()

    # iterate over each line in the symbolic code
    for line in symbolic_code:
        if isinstance(line, SymbolicAddress):
            # symbolic address -> set the real address if it is a
            line.real_address = curr_real_address
        else:
            # instruction -> increment the curr_real_address and queue it
            unprinted_instructions.append(line)
            curr_real_address += 1

        # iterate until the queue is empty
        while unprinted_instructions:
            first_instruction = unprinted_instructions.popleft()
            if isinstance(first_instruction, tuple):
                # tuple -> instruction references a symbolic address
                instruction, address = first_instruction
                if address.real_address is None:
                    # unresolved address -> put the line back to the front of the queue
                    unprinted_instructions.appendleft(first_instruction)
                    # break out of loop inner loop to spin the outer loop until the address is resolved
                    break
                else:
                    yield f"{instruction} {address.real_address}"
            else:
                # plain instruction
                yield first_instruction
