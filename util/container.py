class Container(tuple):
    def __new__(cls, *tokens):
        return super(Container, cls).__new__(cls, tokens)

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(repr(item) for item in self)})"
