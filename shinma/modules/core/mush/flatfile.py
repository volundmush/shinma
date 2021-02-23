class FlatLine:

    def __init__(self, text: str):
        self.text = text
        self.header = text[0] in ('+', '~', '!', '*')
        self.name = None
        self.value = None
        self.valtype = None
        self.depth = 0
        if self.header:
            if text.startswith("!"):
                self.value = int(text[1:])
                self.valtype = "dbref"
        else:
            self.depth = len(text) - len(text.lstrip(' '))
            name, value = text.lstrip(' ').split(" ", 1)
            self.name = name
            if value.startswith('"'):
                self.value = value[1:-1]
                self.valtype = "text"
            elif value.startswith("#"):
                self.value = int(value[1:])
                self.valtype = "dbref"
            else:
                self.value = int(value)
                self.valtype = "number"


def parse_flatlines(generator: callable):
    while line := next(generator):
        yield FlatLine(line)
    else:
        yield None


def parse_flatfile(path: str, chunk_size: int = 50):
    """
    Opens up a PennMUSH flatfile and parses it generator-style so that escaped values with newlines are treated as single lines.

    This totally ignores any \r it sees but considers a \n a newline.

    Args:
        path (path-like): the file to open.
        chunk_size (int): bytes-at-a-time to read the file

    Returns:
        generator of parsed lines.
    """
    f = open(path, encoding="latin_1")
    scratch = ""
    escaped = False
    quoted = False

    while buffer := f.read(chunk_size):
        for c in buffer:
            # just ignore any CR's we see. We only care about LF.
            if c == "\r":
                continue

            if quoted:
                if escaped:
                    escaped = False
                    scratch += c
                else:
                    if c == '"':
                        quoted = False
                        scratch += c
                    elif c == "\\":
                        escaped = True
                    else:
                        scratch += c
            else:
                if c == '"':
                    quoted = True
                    scratch += c
                elif c == "\n":
                    yield scratch
                    scratch = ""
                else:
                    scratch += c
    else:
        yield None