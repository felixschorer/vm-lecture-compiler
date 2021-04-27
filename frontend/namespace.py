from typing import Dict

from pyparsing import Forward, ParserElement


class Namespace:
    parser_elements: Dict[str, ParserElement] = dict()

    def __getattr__(self, name: str):
        if name not in self.parser_elements:
            self.parser_elements[name] = Forward()
        return self.parser_elements[name]

    def __setattr__(self, name: str, parser_element: ParserElement):
        getattr(self, name) << parser_element
