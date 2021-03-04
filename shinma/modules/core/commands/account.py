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
            'accounts': self.list_accounts,
            'districts': self.list_districts
        }

        if not (choice := options.get(partial_match(mode.clean, options.keys()), None)):
            raise CommandException(f"That is not a valid choice. Choices are: {options.keys()}")
        choice()

    def list_accounts(self):
        if not (accounts := self.enactor.core.get_tag('account').all()):
            raise CommandException("There are no accounts to list.")
        out = fmt.FormatList(self.enactor)
        out.add(fmt.Header("Accounts"))
        table = fmt.Table("Objid", "Name", "Characters")
        for acc in accounts:
            table.add_row(acc.objid, acc.name, ', '.join(x.name for x in acc.reverse.all('characters')))
        out.add(table)
        out.add(fmt.Footer())
        self.enactor.send(out)

    def list_districts(self):
        def line(dist, o, depth=0):
            l = fmt.Text(' ' * depth + f"?? {dist.objid:<15} {dist.name:<30} {len(dist.reverse.all('rooms'))}")
            o.add(l)
            for d in dist.reverse.all('districts'):
                line(d, o, depth=depth+1)

        if not (districts := self.enactor.core.get_tag('district').all()):
            raise CommandException("There are no districts to list.")
        # filter down to just root districts.
        if not (districts := [d for d in districts if not d.relations.get('parent_district')]):
            # not sure HOW this could ever happen, but just in case...
            raise CommandException("There are no districts to list. This probably shouldn't happen - contact devs")
        out = fmt.FormatList(self.enactor)
        out.add(fmt.Header("Districts"))
        for d in districts:
            line(d, out, depth=0)
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