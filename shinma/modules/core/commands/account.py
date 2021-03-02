import re
import sys
import time
import traceback
from . base import Command, CommandException, PythonCommandMatcher
from ..mush.ansi import AnsiString
from shinma.utils import partial_match


class AccountCommand(Command):
    name = '@account'
    re_match = re.compile(r"(?si)^(?P<cmd>@account>\w+)(?P<switches>(/(\w+)?)+)?(?::(?P<mode>\S+)?)?(?:\s+(?P<args>(?P<lhs>[^=]+)(?:=(?P<rhs>.*))?)?)?", flags=re.IGNORECASE)