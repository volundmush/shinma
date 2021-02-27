# this is largely adapted from PennMUSH's ansi.h and related files.
import random
import re
import html
from typing import List


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

    ANSI_BEGIN = '\x1B['
    ANSI_FINISH = 'm'
    CBIT_HILITE = 1
    CBIT_INVERT = 2
    CBIT_FLASH = 4
    CBIT_UNDERSCORE = 8

    COL_NORMAL = 0
    COL_HILITE = 1
    COL_UNDERSCORE = 4
    COL_FLASH = 5
    COL_INVERT = 7

    COL_BLACK = 30
    COL_RED = 31
    COL_GREEN = 32
    COL_YELLOW = 33
    COL_BLUE = 34
    COL_MAGENTA = 35
    COL_CYAN = 36
    COL_WHITE = 37

    CS_HEX = 0
    CS_16 = 1
    CS_256 = 2
    CS_256HEX = 3
    CS_RGB = 4
    CS_NAME = 5
    CS_AUTO = 6


STATES = {
    '#': "hex",
    '<': "rgb",
    '+': "name"
}


def separate_codes(codes: str):

    def retrieve_section(state: str, current: str):
        """
        This returns a single section - either letters or a new-style.
        """
        if state == "old":
            idx_plus = current.find('+')
            idx_hash = current.find('#')
            idx_than = current.find('<')
            idx_bg = current.find('/')
            found_all = [f for f in (idx_plus, idx_hash, idx_than, idx_bg) if f >= 0]
            # it cannot actually be 0 here
            found = min(found_all) if found_all else -1
            if found > 0:
                before, delim, after = current.partition(current[found])
                before = ''.join(before.split())  # squishes any unnecessary whitespace in letters
                return True, before, delim + after
            else:
                # there is NOTHING special ahead... devour and compress it all, return empty string
                return True, ''.join(current.split()), ''
        elif state == "new":
            # it's very possible that we were passed an empty string...
            if not current:
                return True, '', ''
            mode = STATES[current[0]]
            if mode in ('hex', 'name'):
                idx_bg = current.find('/')
                idx_ws = current.find(' ')
                found_all = [f for f in (idx_bg, idx_ws) if f >= 0]
                found = min(found_all) if found_all else -1
                if found >= 0:
                    before, delim, after = current.partition(current[found])
                    return True, before, delim + after
                else:
                    return True, current, ''
            elif mode == 'rgb':
                # rgb must finish with a >
                idx_than = current.find('>')
                if idx_than >= 0:
                    return True, current[:idx_than+1], current[idx_than+1:]
                else:
                    return False, current, ''

    def get_section(state: str, current: str):
        if state == "old":
            return retrieve_section(state, current)
        elif state == "fg":
            return retrieve_section("new", current)
        elif state == "bg":
            if current[1:]:
                return retrieve_section("new", current[1:])
            else:
                return True, '/' + '', ''

    start_codes = codes
    # this trick eliminates all excessive whitespace
    codes = ' '.join(codes.split())

    while len(codes):
        if codes[0] in ('+', '#', '<', '/'):
            state = "bg" if codes[0] == '/' else 'fg'
            ok, section, remaining = get_section(state, codes)
            if not ok:
                raise ValueError(f"#-1 INVALID ANSI DEFINITION: {section+remaining}")
            codes = remaining
            if section:
                yield (state, section)
        elif codes.isspace():
            # just ignore spaces in the middle of nowhere out here.
            codes = codes[1:]
        else:
            ok, section, remaining = get_section("old", codes)
            if not ok:
                raise ValueError(f"#-1 INVALID ANSI DEFINITION: {section+remaining}")
            codes = remaining
            if section:
                yield ("letters", section)


class Markup:

    def __init__(self, pansi, parent, standalone: bool, code: str, counter: int):
        self.pansi = pansi
        self.counter = counter
        self.children = list()
        self.parent = parent
        if self.parent:
            self.parent.children.append(self)
        self.standalone = standalone
        self.code = code
        self.start_text = ""
        self.end_text = ""
        self.ansi = None
        self.html_start = None
        self.html_end = None
        self.bits = 0
        self.off_bits = 0
        self.fg = ''
        self.bg = ''
        self.fg_new = False
        self.bg_new = False

    def enter(self):
        return f"{AnsiMarkup.TAG_START}{self.code}{self.start_text}{AnsiMarkup.TAG_END}"

    def exit(self):
        return f"{AnsiMarkup.TAG_START}{self.code}/{self.end_text}{AnsiMarkup.TAG_END}"

    def ancestors(self):
        out = list()
        if self.parent:
            parent = self.parent
            out.append(parent)
            while (parent := parent.parent):
                out.append(parent)
        return list(reversed(out))

    def __repr__(self):
        return f"<Markup {self.counter}: {self.code} - {self.start_text}>"

    def setup(self):
        if self.code == 'c':
            self.setup_ansi()
        elif self.code == 'p':
            self.setup_html()

    def setup_ansi(self):
        for mode, code in separate_codes(self.start_text):
            if mode == "letters":
                for c in code:
                    if c == 'n':
                        # ANSI reset
                        self.bits = 0
                        self.off_bits = ~0
                        self.fg = 'n'
                        self.bg = ''
                        self.fg_new = False
                        self.bg_new = False
                    elif c == 'f':
                        self.bits |= AnsiMarkup.CBIT_FLASH
                        self.off_bits &= ~AnsiMarkup.CBIT_FLASH
                    elif c == 'h':
                        self.bits |= AnsiMarkup.CBIT_HILITE
                        self.off_bits &= ~AnsiMarkup.CBIT_HILITE
                    elif c == 'i':
                        self.bits |= AnsiMarkup.CBIT_INVERT
                        self.off_bits &= ~AnsiMarkup.CBIT_INVERT
                    elif c == 'u':
                        self.bits |= AnsiMarkup.CBIT_UNDERSCORE
                        self.off_bits &= ~AnsiMarkup.CBIT_UNDERSCORE
                    elif c == 'F':
                        self.off_bits |= AnsiMarkup.CBIT_FLASH
                        self.bits &= ~AnsiMarkup.CBIT_FLASH
                    elif c == 'H':
                        self.off_bits |= AnsiMarkup.CBIT_HILITE
                        self.bits &= ~AnsiMarkup.CBIT_HILITE
                    elif c == 'I':
                        self.off_bits |= AnsiMarkup.CBIT_INVERT
                        self.bits &= ~AnsiMarkup.CBIT_INVERT
                    elif c == 'U':
                        self.off_bits |= AnsiMarkup.CBIT_UNDERSCORE
                        self.bits &= ~AnsiMarkup.CBIT_UNDERSCORE
                    elif c in ('b', 'c', 'g', 'm', 'r', 'w', 'x', 'y', 'd'):
                        self.fg = c
                        self.fg_new = False
                    elif c in ('B', 'C', 'G', 'M', 'R', 'W', 'X', 'Y', 'D'):
                        self.bg = c
                        self.bg_new = False
                    else:
                        pass  # I dunno what we got passed, but it ain't relevant.

            elif mode == "fg":
                self.fg_new = True
                self.fg = code
            elif mode == "bg":
                self.bg_new = True
                self.bg = code


    def setup_html(self):
        self.html_start = f"<{self.start_text}>"
        tag, extra = self.start_text.split(' ', 1)
        self.html_end = f"</{tag}>"


class AnsiString:
    re_format = re.compile(
        r"(?i)(?P<just>(?P<fill>.)?(?P<align>\<|\>|\=|\^))?(?P<sign>\+|\-| )?(?P<alt>\#)?"
        r"(?P<zero>0)?(?P<width>\d+)?(?P<grouping>\_|\,)?(?:\.(?P<precision>\d+))?"
        r"(?P<type>b|c|d|e|E|f|F|g|G|n|o|s|x|X|%)?"
    )

    def __init__(self, src: str = None):
        self.source = ""
        self.clean = ""
        self.markup = list()
        self.markup_idx_map = list()
        if src:
            self.decode(src)

    def __len__(self):
        return len(self.clean)

    def __getitem__(self, item):
        out = self.clone()
        out.markup_idx_map = self.markup_idx_map.__getitem__(item)
        out.clean = out.clean.__getitem__(item)
        if len(out.clean) == 0:
            out.markup_idx_map = list()
        elif len(out.clean) == 1:
            out.markup_idx_map = [out.markup_idx_map]
        return out

    def __str__(self):
        return self.encoded()

    def __format__(self, format_spec):
        """
        This magic method covers ANSIString's behavior within a str.format() or f-string.

        Current features supported: fill, align, width.

        Args:
            format_spec (str): The format specification passed by f-string or str.format(). This is a string such as
                "0<30" which would mean "left justify to 30, filling with zeros". The full specification can be found
                at https://docs.python.org/3/library/string.html#formatspec

        Returns:
            ansi_str (str): The formatted ANSIString's .raw() form, for display.
        """
        # This calls the compiled regex stored on ANSIString's class to analyze the format spec.
        # It returns a dictionary.
        format_data = self.re_format.match(format_spec).groupdict()
        align = format_data.get("align", "<")
        fill = format_data.get("fill", " ")

        # Need to coerce width into an integer. We can be certain that it's numeric thanks to regex.
        width = format_data.get("width", None)
        if width is None:
            width = len(self.clean)
        else:
            width = int(width)
        output = None

        if width >= len(self.clean):
            if align == "<":
                output = self.ljust(width, fill)
            elif align == ">":
                output = self.rjust(width, fill)
            elif align == "^":
                output = self.center(width, fill)
            elif align == "=":
                pass
        else:
            output = self[0:width]

        # Return the raw string with ANSI markup, ready to be displayed.
        return output.encoded()

    def __bool__(self):
        if not self.clean:
            return False
        if self.clean.startswith('#-'):
            return False
        if self.clean.strip() in ('0', '-0'):
            return False
        return True

    def __add__(self, other):
        if isinstance(other, AnsiString):
            n = self.clone()
            n.markup_idx_map.extend(other.markup_idx_map)
            n.regen_clean()
            return n
        elif isinstance(other, str):
            if not self.clean:
                return AnsiString(other)
            else:
                n = self.clone()
                for i, char in enumerate(other):
                    n.markup_idx_map.append((None, char))
                    n.regen_clean()
                    return n

    def __iadd__(self, other):
        if isinstance(other, AnsiString):
            self.markup_idx_map.extend(other.markup_idx_map)
            self.regen_clean()
            return self
        elif isinstance(other, str):
            for i, char in enumerate(other):
                self.markup_idx_map.append((None, char))
            self.clean += other
            return self

    def regen_clean(self):
        self.clean = ''.join(t[1] for t in self.markup_idx_map)

    def clone(self):
        other = self.__class__()
        other.clean = self.clean
        other.markup = list(self.markup)
        other.markup_idx_map = list(self.markup_idx_map)
        return other

    def capitalize(self):
        other = self.clone()
        other.clean = other.clean.capitalize()
        new_markup = list()
        for i, m in enumerate(other.markup_idx_map):
            new_markup.append((m[0], other.clean[i]))
        other.markup_idx_map = new_markup
        return other

    def count(self, *args, **kwargs):
        return self.clean.count(*args, **kwargs)

    def encode(self, *args, **kwargs):
        return self.clean.encode(*args, **kwargs)

    def startswith(self, *args, **kwargs):
        return self.clean.startswith(*args, **kwargs)

    def endswith(self, *args, **kwargs):
        return self.clean.endswith(*args, **kwargs)

    def center(self, width, fillchar=' '):
        return self.__class__(self.clean.center(width, fillchar).replace(self.clean, self.encoded()))

    def find(self, *args, **kwargs):
        return self.clean.find(*args, **kwargs)

    def index(self, *args, **kwargs):
        return self.clean.index(*args, **kwargs)

    def isalnum(self):
        return self.clean.isalnum()

    def isalpha(self):
        return self.clean.isalpha()

    def isdecimal(self):
        return self.clean.isdecimal()

    def isdigit(self):
        return self.clean.isdigit()

    def isidentifier(self):
        return self.clean.isidentifier()

    def islower(self):
        return self.clean.islower()

    def isnumeric(self):
        return self.clean.isnumeric()

    def isprintable(self):
        return self.clean.isprintable()

    def isspace(self):
        return self.clean.isspace()

    def istitle(self):
        return self.clean.istitle()

    def isupper(self):
        return self.clean.isupper()

    def join(self, iter):
        return self.__class__(self.encoded().join(iter))

    def ljust(self, width, fillchar=' '):
        return self.__class__(self.clean.ljust(width, fillchar).replace(self.clean, self.encoded()))

    def rjust(self, width, fillchar=' '):
        return self.__class__(self.clean.ljust(width, fillchar).replace(self.clean, self.encoded()))

    def lstrip(self, chars: str = None):
        lstripped = self.clean.lstrip(chars)
        strip_count = len(self.clean) - len(lstripped)
        other = self.__class__()
        other.markup = list(self.markup)
        other.markup_idx_map = self.markup_idx_map[strip_count:]
        other.clean = lstripped
        other.source = other.encoded()
        return other

    def replace(self, old: str, new: str, count=None):
        if not (indexes := self.find_all(old)):
            return self.clone()
        if count and count > 0:
            indexes = indexes[:count]
        old_len = len(old)
        new_len = len(new)
        other = self.clone()

        for idx in reversed(indexes):
            final_markup = self.markup_idx_map[idx + old_len][0]
            diff = abs(old_len - new_len)
            replace_chars = min(new_len, old_len)
            # First, replace any characters that overlap.
            for i in range(replace_chars):
                other.markup_idx_map[idx + i] = (self.markup_idx_map[idx + i][0], new[i])
            if old_len == new_len:
                pass  # the nicest case. nothing else needs doing.
            elif old_len > new_len:
                # slightly complex. pop off remaining characters.
                for i in range(diff):
                    deleted = other.markup_idx_map.pop(idx + new_len)
                    print(f"Popped off {deleted}")
            elif new_len > old_len:
                # slightly complex. insert new characters.
                for i in range(diff):
                    other.markup_idx_map.insert(idx + old_len + i, (final_markup, new[old_len + i]))

        if count is not None:
            other.clean = self.clean.replace(old, new, count)
        else:
            other.clean = self.clean.replace(old, new)
        return other

    def find_all(self, sub: str):
        indexes = list()
        start = 0
        while True:
            start = self.clean.find(sub, start)
            if start == -1:
                return indexes
            indexes.append(start)
            start += len(sub)

    def decode(self, src: str):
        self.source = src
        self.clean = ""
        self.markup.clear()
        self.markup_idx_map.clear()

        state, index = 0, None
        mstack = list()
        tag = ""
        counter = -1

        for s in src:
            if state == 0:
                if s == AnsiMarkup.TAG_START:
                    state = 1
                else:
                    self.clean += s
                    self.markup_idx_map.append((index, s))
            elif state == 1:
                # Encountered a TAG START...
                tag = s
                state = 2
            elif state == 2:
                # we are just inside a tag. if it begins with / this is a closing. else, opening.
                if s == "/":
                    state = 4
                else:
                    state = 3
                    counter += 1
                    mark = Markup(self, index, False, tag, counter)
                    self.markup.append(mark)
                    if index:
                        index.setup()
                    index = mark
                    mark.start_text += s
                    mstack.append(mark)
            elif state == 3:
                # we are inside an opening tag, gathering text. continue until TAG_END.
                if s == AnsiMarkup.TAG_END:
                    state = 0
                else:
                    mstack[-1].start_text += s
            elif state == 4:
                # we are inside a closing tag, gathering text. continue until TAG_END.
                if s == AnsiMarkup.TAG_END:
                    state = 0
                    mark = mstack.pop()
                    index = mark.parent
                else:
                    mstack[-1].end_text += s

    def scramble(self):
        other = self.clone()
        random.shuffle(other.markup_idx_map)
        other.clean = ''.join([s[1] for s in other.markup_idx_map])
        return other

    @classmethod
    def from_markup(cls, src: str):
        pa = cls()
        pa.decode(src)
        return pa

    @classmethod
    def from_ansi(cls, src: str, mxp=False):
        pass

    @classmethod
    def from_args(cls, code: str, text: str):
        try:
            return cls(f"{AnsiMarkup.TAG_START}c{code}{AnsiMarkup.TAG_END}{text}{AnsiMarkup.TAG_START}c/{AnsiMarkup.TAG_END}")
        except ValueError as e:
            return cls(f"#-1 INVALID ANSI DEFINITION: {e}")

    def plain(self):
        return self.clean

    def render(self, ansi=False, xterm256=False, mxp=False):
        if xterm256:
            ansi = True
        if not (ansi or xterm256 or mxp):
            return self.clean
        if mxp and not ansi:
            # this is unusual, but okay. Easy to do!
            return html.escape(self.clean)
        # well at this point it appears we are going to be returning ANSI.
        tuples = self.markup_idx_map
        if mxp:
            tuples = [(t[0], html.escape(t[1])) for t in tuples]

        cur = None
        out = ""
        for m, c in tuples:
            if m:
                if cur:
                    # We are inside of a markup!
                    if m == cur:
                        # still inside same markup.
                        out += c
                    elif m.parent == cur:
                        # we moved into a child.
                        cur = m
                        out += m.enter()
                        out += c
                    elif cur.parent == m:
                        # we left a child and re-entered its parent
                        out += cur.exit()
                        out += c
                        cur = m
                    else:
                        # we are moving from one tag to another, but it is not a direct parent or child.
                        # we need to figure out if it's related at all and take proper measures.
                        ancestors = cur.ancestors()
                        try:
                            idx = ancestors.index(m)
                            # this is an ancestor if we have an index. Otherwise, it will raise ValueError.
                            # We need to close out of the ancestors we have left. A slice accomplishes that.
                            for ancestor in reversed(ancestors[idx:]):
                                out += ancestor.exit()

                        except ValueError:
                            # this is not an ancestor. Exit all ancestors.
                            for ancestor in reversed(ancestors):
                                out += ancestor.exit()

                        # now we enter the new tag.
                        cur = m
                        for ancestor in m.ancestors():
                            out += ancestor.enter()
                        out += m.enter()
                        out += c
                else:
                    # We are not inside of a markup tag. Well, that changes now.
                    cur = m
                    for ancestor in m.ancestors():
                        out += ancestor.enter()
                    out += m.enter()
                    out += c
            else:
                # we are moving into a None markup...
                if cur:
                    # exit current markup.
                    out += cur.exit()
                    out += c
                    cur = m
                else:
                    # from no markup to no markup. Just append the character.
                    out += c

        if cur:
            out += cur.exit()
            for ancestor in reversed(cur.ancestors()):
                out += ancestor.exit()

        return out

    def encoded(self):
        if not self.markup:
            return self.clean
        cur = None
        out = ""
        for m, c in self.markup_idx_map:
            if m:
                if cur:
                    # We are inside of a markup!
                    if m == cur:
                        # still inside same markup.
                        out += c
                    elif m.parent == cur:
                        # we moved into a child.
                        cur = m
                        out += m.enter()
                        out += c
                    elif cur.parent == m:
                        # we left a child and re-entered its parent
                        out += cur.exit()
                        out += c
                        cur = m
                    else:
                        # we are moving from one tag to another, but it is not a direct parent or child.
                        # we need to figure out if it's related at all and take proper measures.
                        ancestors = cur.ancestors()
                        try:
                            idx = ancestors.index(m)
                            # this is an ancestor if we have an index. Otherwise, it will raise ValueError.
                            # We need to close out of the ancestors we have left. A slice accomplishes that.
                            for ancestor in reversed(ancestors[idx:]):
                                out += ancestor.exit()

                        except ValueError:
                            # this is not an ancestor. Exit all ancestors.
                            for ancestor in reversed(ancestors):
                                out += ancestor.exit()

                        # now we enter the new tag.
                        cur = m
                        for ancestor in m.ancestors():
                            out += ancestor.enter()
                        out += m.enter()
                        out += c
                else:
                    # We are not inside of a markup tag. Well, that changes now.
                    cur = m
                    for ancestor in m.ancestors():
                        out += ancestor.enter()
                    out += m.enter()
                    out += c
            else:
                # we are moving into a None markup...
                if cur:
                    # exit current markup.
                    out += cur.exit()
                    out += c
                    cur = m
                else:
                    # from no markup to no markup. Just append the character.
                    out += c

        if cur:
            out += cur.exit()
            for ancestor in reversed(cur.ancestors()):
                out += ancestor.exit()

        return out
