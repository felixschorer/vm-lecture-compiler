from pyparsing import ParserElement


def parse_action_for(parser_element: ParserElement):
    def decorator(func):
        def parse_action(_s, _loc, tokens):
            return func(*tokens)

        parser_element.setParseAction(parse_action)
        return func

    return decorator
