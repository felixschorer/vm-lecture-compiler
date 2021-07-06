import unittest

from cma.backend import (
    Array,
    Basic,
    EnvEntry,
    LazyStruct,
    Pointer,
    Struct,
    code,
    code_r,
    datatype,
    render_symbolic_addresses,
    sizeof,
)
from cma.frontend import (
    AddressOf,
    ArrayAccess,
    C,
    Constant,
    Identifier,
    PointerDereference,
    StructAccess,
    StructPointerAccess,
)


def generate_expression_code(c_code, environment):
    (node,) = C.Expression.parseString(c_code, parseAll=True)
    return list(render_symbolic_addresses(code_r(node, environment)))


def generate_statement_code(c_code, environment):
    (node,) = C.StatementSequence.parseString(c_code, parseAll=True)
    return list(render_symbolic_addresses(code(node, environment)))


def basic_addr(addr: int):
    return EnvEntry(addr, Basic())


class TestArithmeticCodeGeneration(unittest.TestCase):
    def test_simple_arithmetic_expression(self):
        c_code = "x = y - 1"
        environment = {"x": basic_addr(4), "y": basic_addr(7)}
        result = generate_expression_code(c_code, environment)
        desired = ["loadc 7", "load", "loadc 1", "sub", "loadc 4", "store"]
        self.assertEqual(result, desired)


class TestExpressionCodeGeneration(unittest.TestCase):
    def test_malloc_call(self):
        c_code = "malloc(1 + a)"
        environment = {"a": basic_addr(4)}
        result = generate_expression_code(c_code, environment)
        desired = ["loadc 1", "loadc 4", "load", "add", "new"]
        self.assertEqual(result, desired)

    def test_free_call(self):
        c_code = "free(1 + a);"
        environment = {"a": basic_addr(4)}
        result = generate_statement_code(c_code, environment)
        desired = ["loadc 1", "loadc 4", "load", "add", "pop"]
        self.assertEqual(result, desired)


class TestSizeof(unittest.TestCase):
    def test_array_of_stucts(self):
        data = Array(Struct(("a", Basic()), ("b", Pointer(Basic()))), 5)
        desired = 10
        result = sizeof(data)
        self.assertEqual(result, desired)

    def test_struct_containing_array(self):
        data = Struct(("a", Array(Basic(), 3)), ("b", Pointer(Basic())))
        desired = 4
        result = sizeof(data)
        self.assertEqual(result, desired)


class TestDatatype(unittest.TestCase):
    def test_basic(self):
        node = Identifier(name="foo")
        environment = {"foo": basic_addr(42)}
        desired = Basic()
        result = datatype(node, environment)
        self.assertEqual(result, desired)

    def test_pointer(self):
        node = PointerDereference(pointer=Identifier(name="foo"))
        environment = {"foo": EnvEntry(42, Pointer(Basic()))}
        desired = Basic()
        result = datatype(node, environment)
        self.assertEqual(result, desired)

    def test_array(self):
        node = ArrayAccess(accessee=Identifier(name="foo"), expr=Constant(42))
        environment = {"foo": EnvEntry(42, Array(Basic(), 42))}
        desired = Basic()
        result = datatype(node, environment)
        self.assertEqual(result, desired)

    def test_array_pointer(self):
        node = ArrayAccess(accessee=Identifier(name="foo"), expr=Constant(42))
        environment = {"foo": EnvEntry(42, Pointer(Basic()))}
        desired = Basic()
        result = datatype(node, environment)
        self.assertEqual(result, desired)

    def test_struct(self):
        node = StructAccess(
            accessee=Identifier(name="foo"), field=Identifier(name="bar")
        )
        environment = {"foo": EnvEntry(42, Struct(("bar", Basic())))}
        desired = Basic()
        result = datatype(node, environment)
        self.assertEqual(result, desired)

    def test_struct_pointer(self):
        node = StructPointerAccess(
            pointer=Identifier(name="foo"), field=Identifier(name="bar")
        )
        environment = {"foo": EnvEntry(42, Pointer(Struct(("bar", Basic()))))}
        desired = Basic()
        result = datatype(node, environment)
        self.assertEqual(result, desired)

    def test_address_of(self):
        node = AddressOf(value=Identifier(name="foo"))
        environment = {"foo": basic_addr(42)}
        desired = Pointer(Basic())
        result = datatype(node, environment)
        self.assertEqual(result, desired)


class TestStatementCodeGeneration(unittest.TestCase):
    def test_simple_statement_sequence(self):
        c_code = "x = 42; y = 2;"
        environment = {"x": basic_addr(4), "y": basic_addr(7)}
        result = generate_statement_code(c_code, environment)
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
        c_code = """
        if (x > y) 
            x = x - y; 
        else y = y - x;
        """
        environment = {"x": basic_addr(4), "y": basic_addr(7)}
        result = generate_statement_code(c_code, environment)
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

    def test_simple_while_statement(self):
        c_code = "while (a > 0) { c = c + 1; a = a - b; }"
        environment = {"a": basic_addr(7), "b": basic_addr(8), "c": basic_addr(9)}
        result = generate_statement_code(c_code, environment)
        desired = [
            "loadc 7",
            "load",
            "loadc 0",
            "gr",
            "jumpz 21",
            "loadc 9",
            "load",
            "loadc 1",
            "add",
            "loadc 9",
            "store",
            "pop",
            "loadc 7",
            "load",
            "loadc 8",
            "load",
            "sub",
            "loadc 7",
            "store",
            "pop",
            "jump 0",
        ]
        self.assertEqual(result, desired)

    def test_simple_for(self):
        c_code = "for (i = 0; i < 10; i = i + 1) x = x * i;"
        environment = {"i": basic_addr(1), "x": basic_addr(42)}
        result = generate_statement_code(c_code, environment)
        desired = [
            "loadc 0",
            "loadc 1",
            "store",
            "pop",
            "loadc 1",
            "load",
            "loadc 10",
            "le",
            "jumpz 25",
            "loadc 42",
            "load",
            "loadc 1",
            "load",
            "mul",
            "loadc 42",
            "store",
            "pop",
            "loadc 1",
            "load",
            "loadc 1",
            "add",
            "loadc 1",
            "store",
            "pop",
            "jump 4",
        ]
        self.assertEqual(result, desired)

    def test_simple_switch(self):
        c_code = """
        switch (x) {
            case 0:
                x = 0;
                break;
            default:
                x = 1;
        }
        """
        environment = {"x": basic_addr(42)}
        result = generate_statement_code(c_code, environment)
        desired = [
            "loadc 42",
            "load",
            "dup",
            "loadc 0",
            "geq",
            "jumpz 11",
            "dup",
            "loadc 1",
            "le",
            "jumpz 11",
            "jumpi 24",
            "pop",
            "loadc 1",
            "jumpi 24",
            "loadc 0",
            "loadc 42",
            "store",
            "pop",
            "jump 26",
            "loadc 1",
            "loadc 42",
            "store",
            "pop",
            "jump 26",
            "jump 14",
            "jump 19",
        ]
        self.assertEqual(result, desired)


class TestDataStructure(unittest.TestCase):
    def test_array_access(self):
        c_code = "foo[42]"
        environment = {"foo": EnvEntry(2, Array(Basic(), 100))}
        result = generate_expression_code(c_code, environment)
        desired = ["loadc 2", "loadc 42", "loadc 1", "mul", "add", "load"]
        self.assertEqual(result, desired)

    def test_struct_access(self):
        c_code = "x.b"
        environment = {"x": EnvEntry(13, Struct(("a", Basic()), ("b", Basic())))}
        result = generate_expression_code(c_code, environment)
        desired = ["loadc 13", "loadc 1", "add", "load"]
        self.assertEqual(result, desired)

    def test_pointer_struct_access(self):
        c_code = "x -> b"
        environment = {
            "x": EnvEntry(13, Pointer(Struct(("a", Basic()), ("b", Basic()))))
        }
        result = generate_expression_code(c_code, environment)
        desired = ["loadc 13", "load", "loadc 1", "add", "load"]
        self.assertEqual(result, desired)

    def test_complex_access(self):
        c_code = "pt->b->a[i+1]"
        structs = {}
        structs["foo"] = Struct(
            ("a", Array(Basic(), 7)), ("b", Pointer(LazyStruct(lambda: structs["foo"])))
        )
        environment = {"i": basic_addr(1), "pt": EnvEntry(3, Pointer(structs["foo"]))}
        result = generate_expression_code(c_code, environment)
        desired = [
            "loadc 3",
            "load",
            "loadc 7",
            "add",
            "load",
            "loadc 0",
            "add",
            "loadc 1",
            "load",
            "loadc 1",
            "add",
            "loadc 1",
            "mul",
            "add",
            "load",
        ]
        self.assertEqual(result, desired)
