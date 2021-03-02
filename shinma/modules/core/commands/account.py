import re
import sys
import time
import traceback
from . base import MushCommand, CommandException, PythonCommandMatcher
from ..mush.ansi import AnsiString
from shinma.utils import partial_match


class AccountCommand(MushCommand):
    name = '@account'
    aliases = ['@acc']
