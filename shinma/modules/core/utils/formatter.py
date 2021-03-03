from ..mush.ansi import AnsiString
from ..utils.evtable import EvTable
import math


class BaseFormatter:

    def render(self, formatter, obj):
        """
        All formatters must implement render.

        Args:
            obj (TypedObject): A TypedObject / GameObject. This will generally be a connection.

        Returns:
            output (AnsiString): The formatted text, as an AnsiString.
        """
        return AnsiString('')

    def data(self, formatter, obj):
        """
        All formatters must implement data.
        This function returns data that will be sent over OOB to the client.

        Args:
            formatter:
            obj:

        Returns:

        """
        return None


class BaseHeader(BaseFormatter):
    mode = "header"

    def __init__(self, text='', fill_character=None, edge_character=None, color=True):
        if isinstance(text, AnsiString):
            self.text = text.clean
        else:
            self.text = text
        if self.text is None:
            self.text = ''
        self.fill_character = fill_character
        self.edge_character = edge_character
        self.color = color

    def render(self, formatter, obj):
        colors = dict()
        colors["border"] = obj.options.get("border_color")
        colors["headertext"] = obj.options.get(f"{self.mode}_text_color")
        colors["headerstar"] = obj.options.get(f"{self.mode}_star_color")

        width = obj.get_width()
        if self.edge_character:
            width -= 2

        header_text = self.text
        if self.text:
            if self.color:
                header_text = AnsiString.from_args(colors['headertext'], self.text)
            if self.mode == "header":
                col_star = AnsiString.from_args(colors['headerstar'], '*')
                begin_center = AnsiString.from_args(colors['border'], '<') + col_star
                end_center = col_star + AnsiString.from_args(colors['border'], '>')
                center_string = begin_center + header_text + end_center
            else:
                center_string = " " + AnsiString.from_args(colors['headertext'], header_text) + " "
        else:
            center_string = ""

        fill_character = obj.options.get("%s_fill" % self.mode)

        remain_fill = width - len(center_string)
        if remain_fill % 2 == 0:
            right_width = remain_fill / 2
            left_width = remain_fill / 2
        else:
            right_width = math.floor(remain_fill / 2)
            left_width = math.ceil(remain_fill / 2)
        right_fill = AnsiString.from_args(colors["border"], fill_character * int(right_width))
        left_fill = AnsiString.from_args(colors["border"], fill_character * int(left_width))

        if self.edge_character:
            edge_fill = AnsiString.from_args(colors["border"], self.edge_character)
            main_string = center_string
            final_send = (
                    edge_fill + left_fill + main_string + right_fill + edge_fill
            )
        else:
            final_send = left_fill + center_string + right_fill

        return final_send


class Header(BaseHeader):
    mode = "header"


class Subheader(BaseHeader):
    mode = "subheader"


class Separator(BaseHeader):
    mode = "separator"


class Footer(BaseHeader):
    mode = "footer"


class Text(BaseFormatter):
    """
    Just a line of text to display. Nothing fancy about this one!
    """
    
    def __init__(self, text):
        self.text = text
        
    def render(self, formatter, obj):
        return self.text


class OOB(BaseFormatter):
    pass


class Table(BaseFormatter):

    def __init__(self, *args, **kwargs):
        """
        Create an EvTable styled by user preferences.

        Args:
            *args (str or AnsiString): Column headers. If not colored explicitly, these will get colors
                from user options.

        Kwargs:
            any (str, int or dict): EvTable options, including, optionally a `table` dict
                detailing the contents of the table.
        """
        self.args = args
        self.kwargs = kwargs
        self.rows = list()
        self.h_line_char = self.kwargs.pop("header_line_char", "~")
        self.c_char = self.kwargs.pop("corner_char", "+")
        self.b_left_char = self.kwargs.pop("border_left_char", "|")
        self.b_right_char = self.kwargs.pop("border_right_char", "|")
        self.b_bottom_char = self.kwargs.pop("border_bottom_char", "-")
        self.b_top_char = self.kwargs.pop("border_top_char", "-")

    def add_row(self, *args):
        self.rows.append(args)

    def render(self, formatter, obj):
        border_color = obj.options.get("border_color")
        column_color = obj.options.get("column_names_color")

        header_line_char = AnsiString.from_args(border_color, self.h_line_char)
        corner_char = AnsiString.from_args(border_color, self.c_char)
        border_left_char = AnsiString.from_args(border_color, self.b_left_char)
        border_right_char = AnsiString.from_args(border_color, self.b_right_char)
        border_bottom_char = AnsiString.from_args(border_color, self.b_bottom_char)
        border_top_char = AnsiString.from_args(border_color, self.b_top_char)

        width = obj.get_width()

        table = EvTable(
            *self.args,
            header_line_char=header_line_char,
            corner_char=corner_char,
            border_left_char=border_left_char,
            border_right_char=border_right_char,
            border_top_char=border_top_char,
            **self.kwargs,
            maxwidth=width
        )
        for row in self.rows:
            table.add_row(*row)

        # TODO: Some kind of formatting for widths?

        return table.to_ansistring()


class FormatList:
    __slots__ = ["source", "messages", "relay_chain", "kwargs"]

    def __init__(self, source, **kwargs):
        self.source = source
        self.messages = list()
        self.relay_chain = list()
        self.kwargs = kwargs

    def relay(self, obj):
        c = self.__class__(self.source)
        c.relay_chain = list(self.relay_chain)
        c.messages = list(self.messages)
        c.relay_chain.append(obj)
        return c

    def send(self, obj):
        """
        Render the messages in this FormatList for obj.
        """
        text = AnsiString('\n').join([m.render(self, obj) for m in self.messages])
        out = dict()
        c = obj.connection
        if text:
            out['text'] = text.render(ansi=c.ansi, xterm256=c.xterm256, mxp=c.mxp)
        c.msg(out)

    def add(self, fmt: BaseFormatter):
        self.messages.append(fmt)

    def data(self, obj):
        return None
