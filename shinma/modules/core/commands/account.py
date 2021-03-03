import re
import sys
import time
import traceback
from . base import MushCommand, CommandException, PythonCommandMatcher
from ..mush.ansi import AnsiString
from shinma.utils import partial_match
from ..utils import formatter as fmt


class ACreateCommand(MushCommand):
    """
    Creates an Account.
    """
    name = '@acreate'
    aliases = []

    def execute(self):
        name = self.gather_arg()
        password = self.gather_arg(noeval=True)


class ExamineCommand(MushCommand):
    name = '@examine'
    aliases = ['@ex', '@exa', '@exam', '@exami', '@examin']


class ListCommand(MushCommand):
    name = '@list'
    aliases = ['@li', '@lis']

    def execute(self):
        mode = self.gather_arg()
        if not mode:
            raise CommandException("What mode are we listing in?")
        options = {
            'accounts': self.list_accounts
        }

        if not (choice := options.get(partial_match(mode, options.keys()), None)):
            raise CommandException(f"That is not a valid choice. Choices are: {options.keys()}")
        choice()

    def list_accounts(self):

        if not (accounts := self.enactor.core.get_tag('account').all()):
            raise CommandException("There are no accounts to list.")
        out = fmt.FormatList(self.enactor)
        out.add(fmt.Header("Accounts"))
        table = fmt.Table()
        for acc in accounts:
            table.add_row(acc.objid)
        out.add(table)
        out.add(fmt.Footer())
        self.enactor.send(out)


class SLevelCommand(MushCommand):
    """
    Sets Supervisor Level, for granting/removing admin access.
    """
    name = '@slevel'
    aliases = ['@sle', '@slev', '@sleve']


class StyleCommand(MushCommand):
    name = '@style'
    aliases = ['@sty', '@styl']


class AccountCommandMatcher(PythonCommandMatcher):

    def access(self, enactor):
        return True

    def at_cmdmatcher_creation(self):
        self.add(ACreateCommand)
        self.add(SLevelCommand)
        self.add(ExamineCommand)
        self.add(ListCommand)