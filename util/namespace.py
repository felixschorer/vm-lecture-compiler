from pyparsing import Forward, ParserElement


class Namespace:
    def __init__(self):
        # need to call __setattr__ on super to avoid infinite loop
        super(Namespace, self).__setattr__("parser_elements", dict())

    def __getattr__(self, name: str) -> ParserElement:
        if name not in self.parser_elements:
            self.parser_elements[name] = Forward()
        return self.parser_elements[name]

    def __setattr__(self, name: str, parser_element: ParserElement):
        getattr(self, name) << parser_element
