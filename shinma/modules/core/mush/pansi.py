import shinma.modules.pymush.softcode.markup as m


class PennMarkup:

    def __init__(self, pansi, parent, standalone: bool, code: str):
        self.pansi = pansi
        self.children = list()
        self.parent = parent
        if self.parent:
            self.parent.children.append(self)
        self.standalone = standalone
        self.code = code
        self.start_text = ""
        self.end_text = ""


class PennAnsiString:

    def __init__(self):
        self.source = ""
        self.clean = ""
        self.markup = list()
        self.markup_idx_map = list()

    @classmethod
    def from_markup(cls, src: str):
        pa = cls()
        pa.source = src
        pa.clean = ""
        pa.markup.clear()
        pa.markup_idx_map.clear()

        state, index = 0, None
        mstack = list()
        tag = ""

        for s in src:
            if state == 0:
                if s == m.TAG_START:
                    state = 1
                else:
                    pa.clean += s
                    pa.markup_idx_map.append(index)
                continue
            if state == 1:
                # Encountered a TAG START...
                tag = s
                state = 2
                continue
            if state == 2:
                # we are just inside a tag. if it begins with / this is a closing. else, opening.
                if s == "/":
                    state = 4
                else:
                    state = 3
                    mark = PennMarkup(pa, index, False, tag)
                    index = mark
                    mstack.append(mark)
                continue
            if state == 3:
                # we are inside an opening tag, gathering text. continue until TAG_END.
                if s == m.TAG_END:
                    state = 0
                else:
                    mstack[-1].start_text += s
                continue
            if state == 4:
                # we are inside a closing tag, gathering text. continue until TAG_END.
                if s == m.TAG_END:
                    state = 0
                    mark = mstack.pop()
                    index = mark.parent
                else:
                    mstack[-1].end_text += s
                continue

    @classmethod
    def from_ansi(cls, src: str, mxp=False):
        pass