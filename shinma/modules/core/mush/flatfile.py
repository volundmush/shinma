from collections import defaultdict


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

    def __repr__(self):
        return f'{self.__class__.__name__}: ({self.depth}) {self.name} "{self.value}"'


def parse_flatlines(generator: callable):
    for line in generator:
        yield FlatLine(line)
    else:
        return


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
        return


class Flag:
    def __init__(self, name):
        self.name = name
        self.letter = ""
        self.type = ""
        self.perms = ""
        self.negate_perms = ""
        self.aliases = set()

    def set_line(self, line: FlatLine):
        pass


class Attribute:
    def __init__(self, name):
        self.name = name
        self.flags = ""
        self.creator = ""
        self.data = ""
        self.aliases = set()

    def set_line(self, line: FlatLine):
        pass


class ObjAttribute:
    def __init__(self, name):
        self.name = name
        self.value = ""
        self.owner = -1
        self.flags = set()
        self.derefs = 46

    def set_line(self, line: FlatLine):
        pass


class ObjLock:
    def __init__(self, name):
        self.name = name
        self.creator = -1
        self.flags = set()
        self.derefs = -1
        self.key = ""

    def set_line(self, line: FlatLine):
        pass


class DbObject:
    def __init__(self, dbref: int):
        self.dbref = dbref
        self.name = ""
        self.location = -1
        self.contents = -1
        self.exits = -1
        self.next = -1
        self.parent = -1
        self.owner = -1
        self.zone = -1
        self.pennies = 0
        self.type = -1
        self.flags = set()
        self.powers = set()
        self.warnings = set()
        self.created = -1
        self.modified = -1
        self.attributes = dict()
        self.locks = dict()

    @classmethod
    def from_lines(cls, dbref, lines):
        obj = cls(dbref)


class PennDB:

    def __init__(self):
        self.bitflags = 0
        self.dbversion = 0
        self.savetime = ""
        self.flags = dict()
        self.powers = dict()
        self.objects = dict()
        self.attributes = dict()

    @classmethod
    def from_outdb(cls, path: str):
        db = cls()
        flag_cur = None
        attr_cur = None
        section = "header"

        header_section = list()
        obj_storage = defaultdict(list)
        cur_obj = -1

        for i, line in enumerate(parse_flatlines(parse_flatfile(path))):
            print(f"Processing line {i}: {line}")

            if section == "header":
                if line.text.startswith(("+V-")):
                    header_section.append(line)
                elif line.text.startswith("dbversion"):
                    header_section.append(line)
                elif line.text.startswith("savedtime"):
                    header_section.append(line)
                elif line.text.startswith("+FLAGS"):
                    section = "flags"

            if section == "flags":
                if line.depth == 0:
                    if line.name == "flagcount":
                        flags_left = int(line.value)
                    if line.name == "flagaliascount":
                        if flag_cur:
                            db.flags[flag_cur.name] = flag_cur
                        flag_alias_left = int(line.value)
                        section = "flagaliases"
                        flag_cur = None
                if line.depth == 1 and line.name == "name":
                    if flag_cur:
                        db.flags[flag_cur.name] = flag_cur
                    flag_cur = Flag(line.value)
                if line.depth == 2:
                    flag_cur.set_line(line)

            if section == "flagaliases":
                if line.depth == 1 and line.name == "name":
                    flag_cur = db.flags.get(line.name, None)
                if line.depth == 2 and line.name == "alias" and flag_cur:
                    flag_cur.set_line(line)
                if line.depth == 0 and line.text.startswith("+POWER"):
                    section = "powers"
                    flag_cur = None

            if section == "powers":
                if line.depth == 0:
                    if line.name == "flagcount":
                        powers_left = int(line.value)
                    if line.name == "flagaliascount":
                        if flag_cur:
                            db.powers[flag_cur.name] = flag_cur
                        power_alias_left = int(line.value)
                        section = "poweraliases"
                        flag_cur = None
                if line.depth == 1 and line.name == "name":
                    if flag_cur:
                        db.powers[flag_cur.name] = flag_cur
                    flag_cur = Flag(line.value)
                if line.depth == 2:
                    flag_cur.set_line(line)

            if section == "poweraliases":
                if line.depth == 1 and line.name == "name":
                    flag_cur = db.powers.get(line.name, None)
                if line.depth == 2 and line.name == "alias" and flag_cur:
                    flag_cur.set_line(line)
                if line.depth == 0 and line.text.startswith("+ATTRIBUTES"):
                    section = "attributes"
                    flag_cur = None

            if section == "attributes":
                if line.depth == 0:
                    if line.name == "attrcount":
                        attr_left = int(line.value)
                    if line.name == "attraliascount":
                        if attr_cur:
                            db.attributes[attr_cur.name] = attr_cur
                        attr_alias_left = int(line.value)
                        section = "attraliases"
                if line.depth == 1 and line.name == "name":
                    if attr_cur:
                        db.attributes[attr_cur.name] = attr_cur
                    attr = Attribute(line.value)
                    attr_cur = attr
                if line.depth == 2:
                    attr_cur.set_line(line)

            if section == "attraliases":
                if line.depth == 1 and line.name == "name":
                    flag_cur = db.powers.get(line.name, None)
                if line.depth == 2 and line.name == "alias" and flag_cur:
                    flag_cur.set_line(line)
                if line.depth == 0 and line.text.startswith("~"):
                    section = "objects"
                    attr_cur = None

            if section == "objects":
                if line.depth == 0 and line.header == "!":
                    cur_obj = line.value
                elif line.depth == 0 and line.text.startswith("**END OF DUMP"):
                    break
                else:
                    obj_storage[cur_obj].append(line)

        for k, v in obj_storage.items():
            db.objects[k] = DbObject.from_lines(k, v)

        return db