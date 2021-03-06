# this is largely adapted from PennMUSH's ansi.h and related files.
import random
import re
import html
import copy
from typing import List
from . colors import COLORS, FG_DOWNGRADE, BG_DOWNGRADE
from colored.hex import HEX


class AnsiException(Exception):
    pass


class AnsiMarkup:
    BEEP_CHAR = '\a'
    ESC_CHAR = '\x1B'
    ANSI_START = ESC_CHAR + '['
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

    CS_NONE = 0
    CS_HEX = 1
    CS_16 = 2
    CS_256 = 3
    CS_RGBHEX = 4
    CS_RGB = 5
    CS_NAME = 6
    CS_XNAME = 7


STATES = {
    '#': "hex",
    '<': "rgb",
    '+': "name"
}

NEW_MATCH = {
    AnsiMarkup.CS_HEX: re.compile(r"^#(?P<data>[0-9A-F]{6})$", flags=re.IGNORECASE),
    AnsiMarkup.CS_RGBHEX: re.compile(r"^<#(?P<data>[0-9A-F]{6})>$", flags=re.IGNORECASE),
    AnsiMarkup.CS_RGB: re.compile(r"^<(?P<red>[0-9]{1,3}) +(?P<green>[0-9]{1,3}) +(?P<blue>[0-9]{1,3})>$"),
    AnsiMarkup.CS_NAME: re.compile(r"^\+(?P<name>\w+)\b", flags=re.IGNORECASE)
}

ANSI_SECTION_MATCH = {
    "letters": re.compile(r"^(?P<data>[a-z ]+)\b", flags=re.IGNORECASE),
    "numbers": re.compile(r"^(?P<data>\d+)\b"),
    "rgb": re.compile(r"^<(?P<red>\d{1,3})\s+(?P<green>\d{1,3})\s+(?P<blue>\d{1,3})>(\b)?"),
    "hex1": re.compile(r"^#(?P<data>[0-9A-F]{6})\b", flags=re.IGNORECASE),
    "hex2": re.compile(r"^<#(?P<data>[0-9A-F]{6})>(\b)?", flags=re.IGNORECASE),
    "name": re.compile(r"^\+(?P<data>\w+)\b", flags=re.IGNORECASE)
}

CHAR_MAP = {
    'f': AnsiMarkup.CBIT_FLASH,
    'h': AnsiMarkup.CBIT_HILITE,
    'i': AnsiMarkup.CBIT_INVERT,
    'u': AnsiMarkup.CBIT_UNDERSCORE
}

CBIT_MAP = {
    AnsiMarkup.CBIT_HILITE: '1',
    AnsiMarkup.CBIT_UNDERSCORE: '4',
    AnsiMarkup.CBIT_INVERT: '7',
    AnsiMarkup.CBIT_FLASH: '5'
}

BASE_COLOR_MAP = {
    'd': -1,
    'x': 30,
    'r': 31,
    'g': 32,
    'y': 33,
    'b': 34,
    'm': 35,
    'c': 36,
    'w': 37
}


class AnsiData:
    def __init__(self):
        self.bits = 0
        self.off_bits = 0
        self.fg_text = ''
        self.bg_text = ''
        self.fg_mode = None
        self.bg_mode = None
        self.bg_clear = False
        self.fg_clear = False
        self.bg_data = None
        self.fg_data = None
        self.fg_codes = ''
        self.bg_codes = ''
        self.reset = False

    def do_reset(self):
        self.bits = 0
        self.off_bits = 0
        self.fg_text = ''
        self.bg_text = ''
        self.fg_mode = None
        self.bg_mode = None
        self.bg_clear = False
        self.fg_clear = False
        self.bg_data = None
        self.fg_data = None
        self.fg_codes = ''
        self.bg_codes = ''
        self.reset = True

    def styles(self, bits: int):
        return [v for k, v in CBIT_MAP.items() if bits & k]

    def apply_ansi_rule(self, rule_tuple):
        mode, g, data, original = rule_tuple
        if mode == "letters":
            for c in data:
                if c == 'n':
                    # ANSI reset
                    self.do_reset()
                    continue

                self.reset = False
                if (bit := CHAR_MAP.get(c, None)):
                    self.bits |= bit
                    self.off_bits &= ~bit
                elif (bit := CHAR_MAP.get(c.lower(), None)):
                    self.off_bits |= bit
                    self.bits &= ~bit
                elif (code := BASE_COLOR_MAP.get(c, None)):
                    self.fg_text = c
                    if code == -1:
                        self.fg_clear = True
                        self.fg_data = None
                        self.fg_mode = mode
                    else:
                        self.bg_clear = False
                        self.fg_data = code
                        self.fg_mode = mode
                elif (code := BASE_COLOR_MAP.get(c.lower(), None)):
                    self.bg_text = c.lower()
                    if code == -1:
                        self.bg_data = None
                        self.bg_clear = True
                        self.bg_mode = None
                    else:
                        self.bg_data = code + 10
                        self.bg_clear = False
                        self.bg_mode = mode
                else:
                    pass  # I dunno what we got passed, but it ain't relevant.
            return

        if g == "fg":
            self.fg_mode = mode
            self.fg_data = data
            self.fg_text = original
            self.fg_clear = False
        elif g == "bg":
            self.bg_mode = mode
            self.bg_data = data
            self.bg_text = original
            self.bg_clear = False

    def render(self, xterm256: bool = True, downgrade: bool = True):
        """
        This method returns the ANSI escape sequence representing this object.
        Use it to 'just start printing ansi' in this object's style.

        Args:
            xterm256 (bool): Whether xterm is enabled. If not, Xterm colors may be downgraded to 16-color.
            downgrade (bool): if not xterm256, whether to downgrade or just ignore colors.

        Returns:
            ansi (str): A raw string containing ANSI escape codes. It might be empty.
        """
        if self.reset:
            return AnsiMarkup.ANSI_RAW_NORMAL

        reset = False
        codes = list()
        out_bits = self.bits

        if self.fg_clear or self.bg_clear:
            reset = True
            # a 'd' letter sets fg clear. Colors can only be replaced, so to 'clear' colors we must ANSI reset.

        if reset:
            codes.append('0')
        # retrieve any codes for invert, hilite, underscore, etc, and append.

        fg_codes = ''
        xterm_fg = None
        if not self.fg_clear:
            # if fg_clear, fg_mode should be None...
            if self.fg_mode == 'letters':
                fg_codes = str(self.fg_data)
            elif self.fg_mode == "numbers":
                xterm_fg = self.fg_data
            elif self.fg_mode in ("rgb", "hex1", "hex2"):
                xterm_fg = int(HEX(self.fg_data))
            elif self.fg_mode == "name":
                if (found := COLORS.get(self.fg_data, None)):
                    xterm_fg = found['xterm']
        
        if xterm_fg is not None:
            if xterm256:
                fg_codes = f"38;5;{xterm_fg}"
            else:
                if downgrade:
                    hilite, code = FG_DOWNGRADE[xterm_fg]
                    if hilite:
                        out_bits |= AnsiMarkup.CBIT_HILITE
                    fg_codes = str(code)

        bg_codes = ''
        xterm_bg = None
        if not self.bg_clear:
            # if bg_clear, bg_mode should be None...
            if self.bg_mode == 'letters':
                bg_codes = str(self.bg_data)
            elif self.bg_mode == "numbers":
                xterm_bg = self.bg_data
            elif self.bg_mode in ("rgb", "hex1", "hex2"):
                xterm_bg = int(HEX(self.bg_data))
            elif self.bg_mode == "name":
                if (found := COLORS.get(self.bg_data, None)):
                    xterm_bg = found['xterm']

        if xterm_bg is not None:
            if xterm256:
                bg_codes = f"48;5;{xterm_bg}"
            else:
                if downgrade:
                    hilite, code = BG_DOWNGRADE[xterm_bg]
                    if hilite:
                        out_bits |= AnsiMarkup.CBIT_HILITE
                    bg_codes = str(code)

        # all codes that need to be added are now decided.
        if out_bits:
            codes.extend(self.styles(out_bits))
        if fg_codes:
            codes.append(fg_codes)
        if bg_codes:
            codes.append(bg_codes)
        final_codes = ';'.join(codes)
        if final_codes:
            return f"{AnsiMarkup.ANSI_START}{final_codes}m"
        else:
            return ''

    def transition(self, to, xterm256: bool = True, downgrade: bool = True):
        """
        This method returns an ANSI escape sequence representing the transition of the ANSI state of itself,
        to the ANSI state of 'to'.

        Args:
            to (AnsiData): The object being transitioned to.
            xterm256 (bool): Whether xterm is enabled. If not, Xterm colors may be downgraded to 16-color.
            downgrade (bool): if not xterm256, whether to downgrade or just ignore colors.

        Returns:
            ansi (str): A raw string containing ANSI escape codes. It might be empty.
        """
        # Whether an ANSI Reset will be necessary. Many things might force this necessity.
        reset = False

        if self.bits & to.off_bits:
            # Hilite, Invert, underscore, strikethrough, etc, cannot be simply 'turned off' - the ANSI state must be
            # cleanly reset instead.
            reset = True
        remaining = self.bits ^ to.off_bits

        out_bits = to.bits | remaining

        # codes contains a temporary list of the ANSI codes which will be joined by ; eventually.
        # this is a list of strings.
        codes = list()

        if to.fg_clear or to.bg_clear:
            reset = True
            # a 'd' letter sets fg clear. Colors can only be replaced, so to 'clear' colors we must ANSI reset.

        if reset:
            codes.append('0')
        # retrieve any codes for invert, hilite, underscore, etc, and append.

        # Past this point, we can only apply color codes.
        fg_codes = ''
        xterm_fg = None
        # if fg_clear, fg_mode should be None...
        if not to.fg_clear:
            # if fg_clear, fg_mode should be None...
            if to.fg_mode == 'letters':
                fg_codes = str(to.fg_data)
            elif to.fg_mode == "numbers":
                xterm_fg = to.fg_data
            elif to.fg_mode in ("rgb", "hex1", "hex2"):
                xterm_fg = int(HEX(to.fg_data))
            elif to.fg_mode == "name":
                if (found := COLORS.get(to.fg_data, None)):
                    xterm_fg = found['xterm']

        if xterm_fg is not None:
            if xterm256:
                fg_codes = f"38;5;{xterm_fg}"
            else:
                if downgrade:
                    hilite, code = FG_DOWNGRADE[xterm_fg]
                    if hilite:
                        out_bits |= AnsiMarkup.CBIT_HILITE
                    fg_codes = str(code)

        bg_codes = ''
        xterm_bg = None
        if not to.bg_clear:
            # if bg_clear, bg_mode should be None...
            if to.bg_mode == 'letters':
                bg_codes = str(to.bg_data)
            elif to.bg_mode == "numbers":
                xterm_bg = to.bg_data
            elif to.bg_mode in ("rgb", "hex1", "hex2"):
                xterm_bg = int(HEX(to.bg_data))
            elif to.bg_mode == "name":
                if (found := COLORS.get(to.bg_data, None)):
                    xterm_bg = found['xterm']

        if xterm_bg is not None:
            if xterm256:
                bg_codes = f"48;5;{xterm_bg}"
            else:
                if downgrade:
                    hilite, code = BG_DOWNGRADE[xterm_bg]
                    if hilite:
                        out_bits |= AnsiMarkup.CBIT_HILITE
                    bg_codes = str(code)

        # all codes that need to be added are now decided.
        if out_bits:
            codes.extend(to.styles(out_bits))
        if fg_codes:
            codes.append(fg_codes)
        if bg_codes:
            codes.append(bg_codes)
        final_codes = ';'.join(codes)
        if final_codes:
            return f"{AnsiMarkup.ANSI_START}{final_codes}m"
        else:
            return ''


def separate_codes(codes: str):
    codes = ' '.join(codes.split())

    while len(codes):
        if codes[0] in ('/', '!'):
            codes = codes[1:]
            if not len(codes):
                # if there's nothing after a / then we just break.
                break
            if codes[0].isspace():
                codes = codes[1:]
                # if a space immediately follows a / , then it is treated as no color.
                # it will be ignored.
                continue
            elif codes[0] in ('/', '!'):
                continue
            else:
                matched = False
                for k, v in ANSI_SECTION_MATCH.items():
                    if k == "letters":
                        # Letters are not allowed immediately following a /
                        continue
                    if (match := v.match(codes)):
                        codes = codes[match.end():]
                        matched = True
                        if k == "numbers":
                            data = match.groupdict()["data"]
                            number = abs(int(data))
                            if number > 255:
                                raise AnsiException(match.group(0))
                            yield (k, "bg", number, match.group(0))
                            break
                        if k == "name":
                            yield (k, "bg", match.groupdict()["data"].lower(), match.group(0))
                            break
                        elif k in ("hex1", "hex2"):
                            yield (k, "bg", '#' + match.groupdict()["data"].upper(), match.group(0))
                            break
                        elif k == "rgb":
                            data = match.groupdict()
                            hex = f"#{int(data['red']):2X}{int(data['green']):2X}{int(data['blue']):2X}"
                            yield (k, "bg", hex, match.group(0))
                            break
                if not matched:
                    raise AnsiException(codes)

        elif codes[0].isspace():
            codes = codes[1:]
            continue
        else:
            matched = False
            for k, v in ANSI_SECTION_MATCH.items():
                if (match := v.match(codes)):
                    codes = codes[match.end():]
                    matched = True
                    if k == "letters":
                        # letters are the one exception to most rules:
                        # they can be either fg or BG.
                        yield (k, None, match.groupdict()["data"], match.group(0))
                        break
                    if k == "name":
                        yield (k, "fg", match.groupdict()["data"].lower(), match.group(0))
                        break
                    if k == "numbers":
                        data = match.groupdict()["data"]
                        number = abs(int(data))
                        if number > 255:
                            raise AnsiException(match.group(0))
                        yield (k, "fg", number, match.group(0))
                        break
                    elif k in ("hex1", "hex2"):
                        yield (k, "fg", '#' + match.groupdict()["data"], match.group(0))
                        break
                    elif k == "rgb":
                        data = match.groupdict()
                        hexcodes = f"#{int(data['red']):2X}{int(data['green']):2X}{int(data['blue']):2X}"
                        yield (k, "fg", hexcodes, match.group(0))
                        break

            if not matched:
                raise AnsiException(codes)


def test_separate(codes: str):
    for code in separate_codes(codes):
        print(code)


class Markup:

    def __init__(self, ansi_string, parent, standalone: bool, code: str, counter: int):
        self.ansi_string = ansi_string
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

    def enter(self):
        """
        This is called by AnsiString's .encoded() method to print out Penn-stype markup for serializing.

        Returns:
            markup (str)
        """
        return f"{AnsiMarkup.TAG_START}{self.code}{self.start_text}{AnsiMarkup.TAG_END}"

    def exit(self):
        """
        This is called by AnsiString's .encoded() method to print out Penn-stype markup for serializing.

        Returns:
            markup (str)
        """
        return f"{AnsiMarkup.TAG_START}{self.code}/{self.end_text}{AnsiMarkup.TAG_END}"

    def ancestors(self, reversed=False):
        """
        Retrieve all ancestors and return it as a list, ordered from outside-to-in.

        Returns:
            ancestors (List[Markup])
        """
        out = list()
        if self.parent:
            parent = self.parent
            out.append(parent)
            while (parent := parent.parent):
                out.append(parent)
        if reversed:
            out.reverse()
        return out

    def __repr__(self):
        return f"<Markup {self.counter}: {self.code} - {self.start_text}>"

    def setup(self):
        if self.code == 'c':
            self.setup_ansi()
        elif self.code == 'p':
            self.setup_html()

    def inherit_or_create_ansi(self):
        for a in self.ancestors():
            if a.ansi:
                return copy.copy(a.ansi)
        return AnsiData()

    def setup_ansi(self):
        self.ansi = self.inherit_or_create_ansi()
        for rule in separate_codes(self.start_text):
            self.ansi.apply_ansi_rule(rule)

    def setup_html(self):
        self.html_start = AnsiMarkup.ANSI_START + '4z' + f"<{self.start_text}>"
        tag, extra = self.start_text.split(' ', 1)
        self.html_end = AnsiMarkup.ANSI_START + '4z' + f"</{tag}>"

    def enter_html(self):
        return self.html_start

    def exit_html(self):
        return self.html_end


class AnsiString(str):
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
        if isinstance(src, AnsiString):
            self.source = src.source
            self.clean = src.clean
            self.markup = list(src.markup)
            self.markup_idx_map = list(src.markup_idx_map)
        elif src:
            if AnsiMarkup.TAG_START in src:
                self.decode(src)
            else:
                if src:
                    self.clean = src
                    for c in list(src):
                        self.markup_idx_map.append((None, c))

    def __len__(self):
        return len(self.clean)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.clean == other
        if isinstance(other, AnsiString):
            return self.clean == other.clean
        return False

    def __getitem__(self, item):
        if isinstance(item, int):
            sliced = list()
            sliced.append(self.markup_idx_map[item])
        else:
            sliced = self.markup_idx_map[item]
        out = self.clone()
        out.markup_idx_map = sliced
        out.regen_clean()
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
        output = self

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

    def truthy(self):
        if not self.clean:
            return False
        if self.clean.startswith('#-'):
            return False
        if self.clean.strip() in ('0', '-0'):
            return False
        return True

    def __bool__(self):
        return bool(self.clean)

    def __mul__(self, other):
        if not isinstance(other, int):
            return self
        if other == 0:
            return AnsiString()
        n = self.clone()
        if other == 1:
            return n
        if other > 1:
            for _ in range(other-1):
                n.markup_idx_map.extend(self.markup_idx_map)
            n.regen_clean()
        return n

    def __rmul__(self, other):
        if not isinstance(other, int):
            return self
        return self * other

    def __add__(self, other):
        if not len(other):
            return self.clone()
        if not isinstance(other, AnsiString):
            other = AnsiString(other)
        n = self.clone()
        n.markup_idx_map.extend(other.markup_idx_map)
        n.regen_clean()
        return n

    def __iadd__(self, other):
        if not len(other):
            return self
        if isinstance(other, AnsiString):
            self.markup_idx_map.extend(other.markup_idx_map)
            self.regen_clean()
            return self
        elif isinstance(other, str):
            self.markup_idx_map.extend([(None, c) for c in list(other)])
            self.clean += other
            return self

    def __radd__(self, other):
        return AnsiString(other) + self

    def __repr__(self):
        return f"<AnsiString({repr(self.encoded())})>"

    def regen_clean(self):
        if self.markup_idx_map:
            self.clean = ''.join([t[1] for t in self.markup_idx_map])
        else:
            self.clean = ''

    def clone(self):
        other = self.__class__()
        other.clean = self.clean
        other.markup = list(self.markup)
        other.markup_idx_map = list(self.markup_idx_map)
        return other

    @classmethod
    def from_tuples(cls, tuples):
        other = cls()
        other.markup_idx_map.extend(tuples)
        other.regen_clean()
        return other

    def split(self, sep: str = ' ', maxsplit: int = None):
        tuples = list()
        if maxsplit is None or maxsplit == 0:
            limit = -1
        else:
            limit = maxsplit
        count = 0
        cur = list()
        for i, t in enumerate(self.markup_idx_map):
            if t[1] == sep:
                if cur:
                    tuples.append(cur)
                    count += 1
                    cur = list()
                    if limit == count:
                        cur.extend(self.markup_idx_map[i:])
                        break
            else:
                cur.append(t)
        if cur:
            tuples.append(cur)
        return [AnsiString.from_tuples(tup) for tup in tuples]

    def join(self, iterable):
        out_lists = list()
        separator = self.markup_idx_map
        for i, oth in enumerate(iterable):
            if oth:
                if isinstance(oth, AnsiString):
                    out_lists.append(oth.markup_idx_map)
                elif isinstance(oth, str):
                    out_lists.append([(None, c) for c in list(oth)])

        total = len(out_lists)
        out_tuples = list()
        for i, l in enumerate(out_lists):
            out_tuples.extend(l)
            if i+1 < total:
                out_tuples.extend(separator)
        return AnsiString.from_tuples(out_tuples)

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

    def strip(self, chars: str = ' '):
        out_map = list(self.markup_idx_map)
        for i, e in enumerate(out_map):
            if e[1] != chars:
                out_map = out_map[i:]
                break
        out_map.reverse()
        for i, e in enumerate(out_map):
            if e[1] != chars:
                out_map = out_map[i:]
                break
        out_map.reverse()
        out = self.clone()
        out.markup_idx_map = out_map
        out.regen_clean()
        return out

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

        for m in self.markup:
            m.setup()

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
        code = code.strip()
        if code:
            try:
                if isinstance(text, AnsiString):
                    text = text.encoded()
                return cls(f"{AnsiMarkup.TAG_START}c{code}{AnsiMarkup.TAG_END}{text}{AnsiMarkup.TAG_START}c/{AnsiMarkup.TAG_END}")
            except AnsiException as e:
                return cls(f"#-1 INVALID ANSI DEFINITION: {e}")
        else:
            return AnsiString(text)

    @classmethod
    def from_html(cls, tag: str, text: str, **kwargs):
        attrs = ' '.join([f'{k}="{v}"' for k, v in kwargs.items()])
        return cls(f"{AnsiMarkup.TAG_START}p{tag} {attrs}{AnsiMarkup.TAG_END}{text}{AnsiMarkup.TAG_START}p/{tag} {attrs}{AnsiMarkup.TAG_END}")

    @classmethod
    def send_menu(cls, text: str, commands=None):
        if commands is None:
            commands = []
        hints = '|'.join(a[1] for a in commands)
        cmds = '|'.join(a[0] for a in commands)
        return cls.from_html(tag='SEND', text=text, hint=hints, href=cmds)

    def plain(self):
        return self.clean

    def render(self, ansi: bool = False, xterm256: bool = False, mxp: bool = False, downgrade: bool = True):
        """
        Does all the hard work of turning this AnsiString into ANSI fit for display over telnet.

        Args:
            ansi (bool): Whether ANSI is supported. Will not output ANSI if not.
            xterm256 (bool): Whether to support xterm256 colors. This will force ANSI on if true.
            mxp (bool): Support Pueblo/MXP HTML-over-telnet rendering.
            downgrade (bool): If the client supports ansi but not xterm256, this allows a downgrade to 16-color
                codes by nearest match. It can be ugly so be careful.

        Returns:
            ansi-encoded string (str)

        """
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

        tag_stack = list()
        ansi_stack = list()
        mxp_stack = list()
        cur = None
        out = ""
        cur_ansi = None
        cur_mxp = None

        for m, c in tuples:
            if m:
                if cur:
                    # We are inside of a markup!
                    if m is cur:
                        # still inside same markup. just append the character
                        out += c
                    else:
                        # we are moving to something that is NOT the same markup, but is not None.
                        if m.parent is cur:
                            # we moved into a child. No need to terminate MXP yet.
                            if m.code == 'p' and mxp:
                                out += m.enter_html()
                                mxp_stack.append(m)
                            elif m.code == 'c' and ansi:
                                ansi_stack.append(m)
                                out += m.ansi.transition(cur_ansi, xterm256=xterm256, downgrade=downgrade)
                            tag_stack.append(m)
                        else:
                            # We left a tag and are moving into another kind of tag. It might be a parent, an ancestor,
                            # or completely unrelated. Let's find out which, first!
                            ancestors = cur.ancestors(reversed=True)
                            idx = None

                            if m in tag_stack:
                                # We need to close out of the ancestors we no longer have. A slice accomplishes that.
                                tags_we_left = ancestors[tag_stack.index(m):]
                                ansi_we_left = [t for t in tags_we_left if t.code == 'c']
                                mxp_we_left = [t for t in tags_we_left if t.code == 'p']
                                for i in range(len(tags_we_left)-1):
                                    tag_stack.pop(-1)

                                # now that we know what to leave, let's leave them.
                                if len(ansi_we_left) == len(ansi_stack):
                                    # we left all ANSI.
                                    cur_ansi = None
                                    ansi_stack.clear()
                                    out += AnsiMarkup.ANSI_RAW_NORMAL
                                else:
                                    # we left almost all ANSI...
                                    for i in range(len(ansi_we_left) - 1):
                                        ansi_stack.pop(-1)
                                    cur_ansi = ansi_stack[-1]
                                    out += AnsiMarkup.ANSI_RAW_NORMAL
                                    out += cur_ansi.ansi.render(xterm256=xterm256, downgrade=downgrade)

                                if len(mxp_we_left) == len(mxp_stack):
                                    # we left all MXP.
                                    cur_mxp = None
                                    mxp_stack.clear()
                                else:
                                    for i in range(len(mxp_we_left) - 1):
                                        mxp_stack.pop(-1)
                                    cur_mxp = mxp_stack[-1]
                                for mx in reversed(mxp_we_left):
                                    out += mx.exit_html()

                            else:
                                # it's not an ancestor at all, so close out of everything and rebuild.
                                if ansi_stack:
                                    out += AnsiMarkup.ANSI_RAW_NORMAL
                                    ansi_stack.clear()
                                    cur_ansi = None
                                if mxp_stack:
                                    for mx in reversed(mxp_stack):
                                        out += mx.exit_html()
                                    mxp_stack.clear()
                                    cur_mxp = None
                                tag_stack.clear()

                                # Now to enter the new tag...

                                for ancestor in m.ancestors(reversed=True):
                                    if ancestor.code == 'p' and mxp:
                                        mxp_stack.append(ancestor)
                                    elif ancestor.code == 'c' and ansi:
                                        ansi_stack.append(ancestor)

                                if m.code == 'p' and mxp:
                                    mxp_stack.append(m)
                                elif m.code == 'c' and ansi:
                                    ansi_stack.append(m)

                                for an in mxp_stack:
                                    out += an.enter_html()
                                    cur_mxp = an

                                if ansi_stack:
                                    cur_ansi = ansi_stack[-1]
                                    out += cur_ansi.ansi.render(xterm256=xterm256, downgrade=downgrade)

                        out += c
                        cur = m
                else:
                    # We are not inside of a markup tag. Well, that changes now.
                    cur = m
                    for ancestor in m.ancestors(reversed=True):
                        if ancestor.code == 'p' and mxp:
                            mxp_stack.append(ancestor)
                        elif ancestor.code == 'c' and ansi:
                            ansi_stack.append(ancestor)

                    if cur.code == 'p' and mxp:
                        mxp_stack.append(cur)
                    elif cur.code == 'c' and ansi:
                        ansi_stack.append(cur)

                    for an in mxp_stack:
                        out += an.enter_html()
                        cur_mxp = an

                    if ansi_stack:
                        cur_ansi = ansi_stack[-1]
                        out += cur_ansi.ansi.render(xterm256=xterm256, downgrade=downgrade)

                    out += c
            else:
                # we are moving into a None markup...
                if cur:
                    if ansi_stack:
                        out += AnsiMarkup.ANSI_RAW_NORMAL
                        ansi_stack.clear()
                        cur_ansi = None

                    if mxp_stack:
                        for mx in reversed(mxp_stack):
                            out += mx.exit_html()
                        mxp_stack.clear()
                        cur_mxp = None

                    cur = None
                    out += c
                else:
                    # from no markup to no markup. Just append the character.
                    out += c

        # Finalize and exit all remaining tags.
        if ansi_stack:
            out += AnsiMarkup.ANSI_RAW_NORMAL

        if mxp_stack:
            for mx in reversed(mxp_stack):
                out += mx.exit_html()

        return out

    def encoded(self):
        cur = None
        out = ""
        for m, c in self.markup_idx_map:
            if m:
                if cur:
                    # We are inside of a markup!
                    if m is cur:
                        # still inside same markup.
                        out += c
                    elif m.parent is cur:
                        # we moved into a child.
                        cur = m
                        out += m.enter()
                        out += c
                    elif cur.parent is m:
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
                            # this is not an ancestor. Exit all ancestors and cur.
                            out += cur.exit()
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
                    for ancestor in reversed(cur.ancestors()):
                        out += ancestor.exit()
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
