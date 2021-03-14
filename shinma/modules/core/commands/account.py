import re
import sys
import time
import traceback
from . base import MushCommand, CommandException, PythonCommandMatcher, Command
from ..mush.ansi import AnsiString
from shinma.utils import partial_match
from ..utils import formatter as fmt
from ..utils.text import duration_format, red_yellow_green, percent_cap


class ACreateCommand(MushCommand):
    """
    Creates an Account.
    """
    name = '@acreate'
    aliases = []
    help_category = 'Administration'

    def execute(self):
        name = self.gather_arg()
        password = self.gather_arg(noeval=True)

    @classmethod
    def access(cls, enactor):
        return enactor.get_slevel() >= 8


class BanCommand(MushCommand):
    """
    Bans an Account.

    Usage:
        @ban <name>=<duration>

    If <duration> is 0, it will clear a ban.
    """
    name = '@ban'
    aliases = ['@ba']
    help_category = 'Account Management'

    def execute(self):
        name = self.gather_arg()
        duration = self.gather_arg()

    @classmethod
    def access(cls, enactor):
        return enactor.get_slevel() >= 8


class ExamineCommand(MushCommand):
    name = '@examine'
    aliases = ['@ex', '@exa', '@exam', '@exami', '@examin']
    help_category = 'Building'


class ListCommand(MushCommand):
    name = '@list'
    aliases = ['@li', '@lis']
    help_category = 'Administration'

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
            table.add_row(acc.objid, acc.name, ', '.join(x.name for x in acc.characters.all()))
        out.add(table)
        out.add(fmt.Footer())
        self.enactor.send(out)

    def list_districts(self):
        def line(dist, o, depth=0):
            l = fmt.Text(' ' * depth + f"?? {dist.objid:<15} {dist.name:<30} {len(dist.rooms.all())}")
            o.add(l)
            for d in dist.districts.all():
                line(d, o, depth=depth+1)

        if not (districts := self.enactor.core.get_tag('district').all()):
            raise CommandException("There are no districts to list.")
        # filter down to just root districts.
        if not (districts := [d for d in districts if not d.relations.get('parent')]):
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
    help_category = 'Administration'

    @classmethod
    def access(cls, enactor):
        return enactor.get_slevel() >= 6


class StyleCommand(MushCommand):
    name = '@style'
    aliases = ['@sty', '@styl']
    help_category = 'Preferences'


class DumpCommand(MushCommand):
    name = '@dump'
    aliases = []
    help_category = 'System'

    @classmethod
    def access(cls, enactor):
        return enactor.get_slevel() >= 9

    def execute(self):
        self.enactor.core.dump()
        self.enactor.msg(text="Dump complete!")


class NameCommand(MushCommand):
    name = '@name'
    aliases = ['@na', '@nam']
    help_category = 'Building'

    def execute(self):
        target = self.gather_arg()
        new_name = self.gather_arg()


class UptimeCommand(MushCommand):
    name = '@uptime'
    aliases = ['@up', '@upt', '@upti', '@uptim']
    help_category = 'System'


class WhoCommand(Command):
    name = '@who'
    re_match = re.compile(r"^(?P<cmd>@who)(?: +(?P<args>.+)?)?", flags=re.IGNORECASE)
    help_category = 'System'

    def execute(self):
        mdict = self.match_obj.groupdict()
        args = mdict.get('args', 'accounts')
        if args is None:
            args = 'accounts'
        options = {
            'accounts': self.who_accounts,
            'connections': self.who_connections,
            'characters': self.who_characters
        }

        if not (op := partial_match(args, options.keys())):
            raise CommandException("Need to provide option: accounts, connections, or characters")

        options[op]()

    def who_accounts(self):
        t = self.core.get_tag('connection')
        if not (accounts := list(set([acc for c in t.objects if (acc := c.relations.get('account', None))]))):
            raise CommandException("No accounts online to display.")
        accounts.sort(key=lambda x: x.name)
        out = fmt.FormatList(self.enactor)
        out.add(fmt.Header("@who: Accounts"))
        t1 = fmt.Table('Name', ('Idle', 7), ('Conn', 7))
        for acc in accounts:
            idle = int(acc.time_idle())
            idle_ryg = percent_cap(idle, 3600)
            conn = int(acc.time_connected())
            t1.add_row(acc.name, AnsiString.from_args(red_yellow_green(idle_ryg), duration_format(idle, width=4)), AnsiString.from_args('hg', duration_format(conn, width=4)))
        out.add(t1)
        out.add(fmt.Footer())
        self.enactor.send(out)

    def who_connections(self):
        t = self.core.get_tag('connection')
        if not (connections := list(t.objects)):
            raise CommandException("No connections online to display.")
        connections.sort(key=lambda x: x.time_idle())
        out = fmt.FormatList(self.enactor)
        out.add(fmt.Header("@who: Connections"))
        t1 = fmt.Table('ObjId', ('Idle', 7), ('Conn', 7))
        for c in connections:
            idle = int(c.time_idle())
            idle_ryg = percent_cap(idle, 3600)
            conn = int(c.time_connected())
            t1.add_row(c.name, AnsiString.from_args(red_yellow_green(idle_ryg), duration_format(idle, width=4)),
                       AnsiString.from_args('hg', duration_format(conn, width=4)))
        out.add(t1)
        out.add(fmt.Footer())
        self.enactor.send(out)

    def who_characters(self):
        t = self.core.get_tag('playview')
        if not (playviews := [p for p in t.objects if p.connections.all()]):
            raise CommandException("No Characters online to display.")
        playviews.sort(key=lambda x: x.time_idle())
        out = fmt.FormatList(self.enactor)
        out.add(fmt.Header("@who: Characters"))
        t1 = fmt.Table('Name', ('Idle', 7), ('Conn', 7))
        for p in playviews:
            c = p.relations.get('character', None)
            idle = int(p.time_idle())
            idle_ryg = percent_cap(idle, 3600)
            conn = int(p.time_connected())
            t1.add_row(c.name, AnsiString.from_args(red_yellow_green(idle_ryg), duration_format(idle, width=4)),
                       AnsiString.from_args('hg', duration_format(conn, width=4)))
        out.add(t1)
        out.add(fmt.Footer())
        self.enactor.send(out)


class AccountCommandMatcher(PythonCommandMatcher):

    def access(self, enactor):
        return True

    def at_cmdmatcher_creation(self):
        self.add(ACreateCommand)
        self.add(SLevelCommand)
        self.add(ExamineCommand)
        self.add(ListCommand)
        self.add(DumpCommand)
        self.add(StyleCommand)
        self.add(WhoCommand)
