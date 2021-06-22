from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Union
from weakref import WeakKeyDictionary

from cma.frontend import (
    ArrayAccess,
    Assignment,
    BinaryOp,
    Constant,
    For,
    Identifier,
    IfElse,
    PlainStatement,
    PointerDereference,
    StatementSequence,
    StructAccess,
    StructPointerAccess,
    Switch,
    UnaryOp,
    While,
)


class SymbolicAddress:
    pass


Datatype = Union["Array", "Basic", "Struct", "Pointer"]


@dataclass(frozen=True)
class EnvEntry:
    address: int
    datatype: Datatype
    local: bool = False


@dataclass(frozen=True)
class Array:
    datatype: Datatype
    length: int


@dataclass(frozen=True)
class Basic:
    pass


@dataclass(frozen=True)
class Pointer:
    datatype: Datatype


@dataclass(frozen=True)
class StructEntry:
    offset: int
    datatype: Datatype


class Struct:
    def __init__(self, *fields: Tuple[str, Datatype]):
        self.fields: Dict[str, StructEntry] = {}
        offset = 0
        for name, field_type in fields:
            self.fields[name] = StructEntry(offset, field_type)
            offset += sizeof(field_type)


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


def code_l(node: Any, environment: Dict[str, EnvEntry]):
    if isinstance(node, Identifier):
        yield f"loadc {environment[node.name].address}"
    elif isinstance(node, ArrayAccess):
        yield from code_r(node.accessee, environment)
        yield from code_r(node.expr, environment)
        yield f"loadc {sizeof(datatype(node, environment))}"
        yield "mul"
        yield "add"
    elif isinstance(node, StructAccess):
        yield from code_l(node.accessee, environment)
        yield f"loadc {datatype(node.accessee, environment).fields[node.field.name].offset}"
        yield "add"
    else:
        raise AssertionError(f"Cannot generate code_l for {repr(node)}")


def code_r(node: Any, environment: Dict[str, EnvEntry]):
    if isinstance(datatype(node, environment), Array):
        yield from code_l(node, environment)
    elif isinstance(node, BinaryOp):
        yield from code_r(node.left, environment)
        yield from code_r(node.right, environment)
        yield BINARY_OP_TO_INSTR[node.op]
    elif isinstance(node, UnaryOp):
        yield from code_r(node.expr, environment)
        yield UNARY_OP_TO_INSTR[node.op]
    elif isinstance(node, Constant):
        yield f"loadc {node.value}"
    elif isinstance(node, Assignment):
        yield from code_r(node.right, environment)
        yield from code_l(node.left, environment)
        yield "store"
    else:
        yield from code_l(node, environment)
        yield "load"


def check(start: int, end: int, b: SymbolicAddress):
    a = SymbolicAddress()
    yield "dup"
    yield f"loadc {start}"
    yield "geq"
    yield "jumpz", a
    yield "dup"
    yield f"loadc {end}"
    yield "le"
    yield "jumpz", a
    yield "jumpi", b
    yield a
    yield "pop"
    yield f"loadc {end}"
    yield "jumpi", b


def code(node: Any, environment: Dict[str, EnvEntry]):
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
    elif isinstance(node, While):
        a = SymbolicAddress()
        b = SymbolicAddress()
        yield a
        yield from code_r(node.expr, environment)
        yield "jumpz", b
        yield from code(node.body, environment)
        yield "jump", a
        yield b
    elif isinstance(node, For):
        a = SymbolicAddress()
        b = SymbolicAddress()
        yield from code_r(node.expr1, environment)
        yield "pop"
        yield a
        yield from code_r(node.expr2, environment)
        yield "jumpz", b
        yield from code(node.body, environment)
        yield from code_r(node.expr3, environment)
        yield "pop"
        yield "jump", a
        yield b
    elif isinstance(node, Switch):
        b = SymbolicAddress()
        cs = []
        d = SymbolicAddress()
        k = len(node.cases)
        yield from code_r(node.expr, environment)
        yield from check(0, k, b)

        # cases
        for case in node.cases:
            c = SymbolicAddress()
            cs.append(c)
            yield c
            yield from code(case.body, environment)
            yield "jump", d

        # default case
        c = SymbolicAddress()
        cs.append(c)
        yield c
        yield from code(node.default_case, environment)
        yield "jump", d

        # jump table
        yield b
        for c in cs:
            yield "jump", c

        yield d
    else:
        raise AssertionError(f"Cannot generate code for {repr(node)}")


def sizeof(t: Datatype):
    if isinstance(t, (Basic, Pointer)):
        return 1
    elif isinstance(t, Array):
        return sizeof(t.datatype) * t.length
    elif isinstance(t, Struct):
        return sum(sizeof(entry.datatype) for entry in t.fields.values())


def datatype(node: Any, environment: Dict[str, EnvEntry]):
    if isinstance(node, Identifier):
        return environment[node.name].datatype
    elif isinstance(node, PointerDereference):
        pointer_type = datatype(node.pointer, environment)
        if not isinstance(pointer_type, Pointer):
            raise AssertionError(f"Expected {repr(node)} to be a pointer")
        return pointer_type.datatype
    elif isinstance(node, ArrayAccess):
        array_or_pointer_type = datatype(node.accessee, environment)
        if not isinstance(array_or_pointer_type, (Pointer, Array)):
            raise AssertionError(f"Expected {repr(node)} to be a pointer or array")
        return array_or_pointer_type.datatype
    elif isinstance(node, StructAccess):
        struct_type = datatype(node.accessee, environment)
        if not isinstance(struct_type, Struct):
            raise AssertionError(f"Expected {repr(node)} to be a struct")
        return struct_type.fields[node.field.name].datatype
    elif isinstance(node, StructPointerAccess):
        struct_pointer_type = datatype(node.pointer, environment)
        if not (
            isinstance(struct_pointer_type, Pointer)
            and isinstance(struct_pointer_type.datatype, Struct)
        ):
            raise AssertionError(f"Expected {repr(node)} to be a struct")
        return struct_pointer_type.datatype.fields[node.field.name].datatype
    else:
        return Basic()


def render_symbolic_addresses(symbolic_code):
    curr_real_address = 0
    real_address_table = WeakKeyDictionary()
    unprocessed_instructions = deque()

    for line in symbolic_code:
        if isinstance(line, SymbolicAddress):
            # symbolic address -> set the real address of that address
            real_address_table[line] = curr_real_address
        else:
            # instruction -> queue it and increment the curr_real_address
            unprocessed_instructions.append(line)
            curr_real_address += 1

        # iterates until the queue is empty or until we hit a unresolved address
        # effectively a noop when we're waiting for a symbolic address to be resolved
        while unprocessed_instructions:
            instruction = unprocessed_instructions.popleft()
            if isinstance(instruction, tuple):
                # tuple -> instruction references a symbolic address
                opcode, address = instruction
                if address not in real_address_table:
                    # unresolved address -> put the line back to the front of the queue
                    unprocessed_instructions.appendleft(instruction)
                    # break out of the inner loop to spin the outer loop until the address is resolved
                    break
                else:
                    yield f"{opcode} {real_address_table[address]}"
            else:
                # plain instruction
                yield instruction
