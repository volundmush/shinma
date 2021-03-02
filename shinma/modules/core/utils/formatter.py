from ..mush.ansi import AnsiString


class BaseFormatter:
    pass


class BaseHeader(BaseFormatter):
    pass


class Header(BaseHeader):
    pass


class Subheader(BaseHeader):
    pass


class Separator(BaseHeader):
    pass


class Text(BaseFormatter):
    pass


class OOB(BaseFormatter):
    pass


class FormatList:
    __slots__ = ["source", "messages", "relay_chain"]

    def __init__(self, source):
        self.source = source
        self.messages = list()
        self.relay_chain = list()

    def relay(self, obj):
        c = self.__class__(self.source)
        c.relay_chain = list(self.relay_chain)
        c.relay_chain.append(obj)
        return c