from .. import MushError
from ..ansi import AnsiString


class BaseFunction:
    name = None
    aliases = set()
    min_args = None
    max_args = None
    even_args = False
    odd_args = False
    eval_args = True

    def __init__(self, entry, remaining):
        self.entry = entry
        self.output = ''
        self.start = remaining
        self.remaining = remaining
        self.args = list()
        self.args_eval = dict()
        self.error = False

    def separate_args(self):
        escaped = False
        paren_depth = 0
        square_depth = 0
        curly_depth = 0

        while True:
            found_comma = None
            found_end = None

            for i, c in enumerate(self.remaining):
                if escaped:
                    escaped = False
                elif c == "\\":
                    escaped = True
                elif c == "{":
                    curly_depth += 1
                elif c == "}" and curly_depth > 0:
                    curly_depth -= 1
                elif c == "[":
                    square_depth += 1
                elif c == "]" and square_depth > 0:
                    square_depth -= 1
                elif c == "(":
                    paren_depth += 1
                elif c == ")" and paren_depth > 0:
                    paren_depth -= 1
                elif c == ')' and paren_depth == 0:
                    found_end = i
                    break
                elif c == ',' and paren_depth == 0 and square_depth == 0 and curly_depth == 0:
                    found_comma = i
                    break
                else:
                    pass

            if found_end:
                self.remaining = self.remaining[found_end+1:]
                break
            elif found_comma:
                before = self.remaining[:found_comma]
                after = self.remaining[found_comma+1:]
                self.remaining = after
                yield before
            else:
                yield self.remaining
                break

    def scan_arguments(self):
        """
        Scans through self.remaining for MUSH arguments and populates self.args.
        This must then set self.remaining to the text that the MushEvaluator will resume with.

        The default behavior is to evaluate every argument.
        """
        raw_args = [arg for arg in self.separate_args()]

        if self.min_args is not None and self.max_args is not None and self.min_args == self.max_args and len(raw_args) != self.min_args:
            self.output = AnsiString(
                f"#-1 FUNCTION {self.name.upper()} EXPECTS EXACTLY {self.min_args} ARGUMENTS BUT GOT {len(raw_args)}")
            self.error = True
            return False

        if self.min_args is not None and self.min_args > len(raw_args):
            if self.max_args is not None:
                self.output = AnsiString(f"#-1 FUNCTION {self.name.upper()} EXPECTS BETWEEN {self.min_args} AND {self.max_args} ARGUMENTS BUT GOT {len(raw_args)}")
            else:
                self.output = AnsiString(
                    f"#-1 FUNCTION {self.name.upper()} EXPECTS AT LEAST {self.min_args} ARGUMENTS BUT GOT {len(raw_args)}")
            self.error = True
            return False

        if self.max_args is not None and self.max_args < len(raw_args):
            if self.min_args is not None:
                self.output = AnsiString(
                    f"#-1 FUNCTION {self.name.upper()} EXPECTS BETWEEN {self.min_args} AND {self.max_args} ARGUMENTS BUT GOT {len(raw_args)}")
            else:
                self.output = AnsiString(
                    f"#-1 FUNCTION {self.name.upper()} EXPECTS AT MOST {self.max_args} ARGUMENTS BUT GOT {len(raw_args)}")
            self.error = True
            return False
        if self.even_args and len(raw_args) % 2 != 0:
            self.output = AnsiString(f"#-1 FUNCTION {self.name.upper()} EXPECTS EVEN NUMBER OF ARGUMENTS BUT GOT {len(raw_args)}")
            self.error = True
            return False

        if self.odd_args and len(raw_args) % 2 != 1:
            self.output = AnsiString(
                f"#-1 FUNCTION {self.name.upper()} EXPECTS ODD NUMBER OF ARGUMENTS BUT GOT {len(raw_args)}")
            self.error = True
            return False

        self.args = raw_args
        return True

    def execute(self):
        if not (outcome := self.separate_args()):
            return False
        if self.eval_args:
            for i, arg in enumerate(self.args):
                self.args_eval[i] = self.context.evaluate(arg)
        outcome = self.do_execute()
        if outcome is None:
            return True
        return outcome

    def do_execute(self):
        self.output = AnsiString(f"#-1 FUNCTION ({self.name}) IS NOT IMPLEMENTED")
        self.error = True
        return False
