# this is largely adapted from PennMUSH's ansi.h and related files.

class AnsiMarkup:
    BEEP_CHAR = '\a'
    ESC_CHAR = '\x1B'
    ANSI_RAW_NORMAL = '\x1B[0m'

    TAG_START = '\002'
    TAG_END = '\003'
    MARKUP_START = TAG_START
    MARKUP_END = TAG_END

    ANSI_HILITE = MARKUP_START + 'ch' + MARKUP_END
    ANSI_INVERSE = MARKUP_START + 'ci' + MARKUP_END
    ANSI_BLINK = MARKUP_START + 'cf' + MARKUP_END
    ANSI_UNDERSCORE = MARKUP_START = 'cu' + MARKUP_END

    ANSI_INV_BLINK = MARKUP_START + 'cfi' + MARKUP_END
    ANSI_INV_HILITE = MARKUP_START + "chi" + MARKUP_END
    ANSI_BLINK_HILITE = MARKUP_START + "cfh" + MARKUP_END
    ANSI_INV_BLINK_HILITE = MARKUP_START + "cifh" + MARKUP_END

    # Foreground Colors

    ANSI_PLAIN = MARKUP_START + "n" + MARKUP_END
    ANSI_BLACK = MARKUP_START + "cx" + MARKUP_END
    ANSI_RED = MARKUP_START + "cr" + MARKUP_END
    ANSI_GREEN = MARKUP_START + "cg" + MARKUP_END
    ANSI_YELLOW = MARKUP_START + "cy" + MARKUP_END
    ANSI_BLUE = MARKUP_START + "cb" + MARKUP_END
    ANSI_MAGENTA = MARKUP_START + "cm" + MARKUP_END
    ANSI_CYAN = MARKUP_START + "cc" + MARKUP_END
    ANSI_WHITE = MARKUP_START + "cw" + MARKUP_END

    ANSI_HIBLACK = MARKUP_START + "chx" + MARKUP_END
    ANSI_HIRED = MARKUP_START + "chr" + MARKUP_END
    ANSI_HIGREEN = MARKUP_START + "chg" + MARKUP_END
    ANSI_HIYELLOW = MARKUP_START + "chy" + MARKUP_END
    ANSI_HIBLUE = MARKUP_START + "chb" + MARKUP_END
    ANSI_HIMAGENTA = MARKUP_START + "chm" + MARKUP_END
    ANSI_HICYAN = MARKUP_START + "chc" + MARKUP_END
    ANSI_HIWHITE = MARKUP_START + "chw" + MARKUP_END

    # Background Colors

    ANSI_BBLACK = MARKUP_START + "cX" + MARKUP_END
    ANSI_BRED = MARKUP_START + "cR" + MARKUP_END
    ANSI_BGREEN = MARKUP_START + "cG" + MARKUP_END
    ANSI_BYELLOW = MARKUP_START + "cY" + MARKUP_END
    ANSI_BBLUE = MARKUP_START + "cB" + MARKUP_END
    ANSI_BMAGENTA = MARKUP_START + "cM" + MARKUP_END
    ANSI_BCYAN = MARKUP_START + "cC" + MARKUP_END
    ANSI_BWHITE = MARKUP_START + "cW" + MARKUP_END

    ANSI_END = MARKUP_START + "c/" + MARKUP_END
    ANSI_ENDALL = MARKUP_START + "c/a" + MARKUP_END

    ANSI_NORMAL = ANSI_ENDALL

    ANSI_FORMAT_NONE = 0
    ANSI_FORMAT_HILITE = 1
    ANSI_FORMAT_16COLOR = 2
    ANSI_FORMAT_XTERM256 = 3
    ANSI_FORMAT_HTML = 4

    MARKUP_COLOR = 'c'
    MARKUP_COLOR_STR = "c"
    MARKUP_HTML = 'p'
    MARKUP_HTML_STR = "p"
    MARKUP_OLDANSI = 'o'
    MARKUP_OLDANSI_STR = "o"

    MARKUP_WS = 'w'
    MARKUP_WS_ALT = 'W'
    MARKUP_WS_ALT_END = 'M'


class Markup:

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


class AnsiString:

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
                if s == AnsiMarkup.TAG_START:
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
                    mark = Markup(pa, index, False, tag)
                    index = mark
                    mstack.append(mark)
                continue
            if state == 3:
                # we are inside an opening tag, gathering text. continue until TAG_END.
                if s == AnsiMarkup.TAG_END:
                    state = 0
                else:
                    mstack[-1].start_text += s
                continue
            if state == 4:
                # we are inside a closing tag, gathering text. continue until TAG_END.
                if s == AnsiMarkup.TAG_END:
                    state = 0
                    mark = mstack.pop()
                    index = mark.parent
                else:
                    mstack[-1].end_text += s
                continue

    @classmethod
    def from_ansi(cls, src: str, mxp=False):
        pass