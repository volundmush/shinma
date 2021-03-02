import re
import sys
import time
import traceback
from . base import Command, MushCommand, CommandException, PythonCommandMatcher
from ..mush.ansi import AnsiString
from shinma.utils import partial_match
from ..typeclasses.account import CRYPT_CON
from ..mush.importer import Importer


class _LoginCommand(Command):
    re_quoted = re.compile(r'"(?P<name>.+)"(: +(?P<password>.+)?)?', flags=re.IGNORECASE)
    re_unquoted = re.compile(r'^(?P<name>\S+)(?: +(?P<password>.+)?)?', flags=re.IGNORECASE)

    def parse_login(self, error):
        mdict = self.match_obj.groupdict()
        if not mdict["args"]:
            raise CommandException(error)

        result = self.re_quoted.fullmatch(mdict["args"])
        if not result:
            result = self.re_unquoted.fullmatch(mdict["args"])
        rdict = result.groupdict()
        if not (rdict["name"] and rdict["password"]):
            raise CommandException(error)
        return rdict["name"], rdict["password"]


class ConnectCommand(_LoginCommand):
    name = "connect"
    re_match = re.compile(r"^(?P<cmd>connect)(?: +(?P<args>.+))?", flags=re.IGNORECASE)
    usage = "Usage: " + AnsiString.from_args("hw", "connect <username> <password>") + " or " + AnsiString.from_args("hw", 'connect "<user name>" password')

    def execute(self):
        name, password = self.parse_login(self.usage)
        account, error = self.core.search_tag("account", name, exact=True)
        if error:
            raise CommandException("Sorry, that was an incorrect username or password. (account search failed)")
        if not account:
            raise CommandException("Sorry, that was an incorrect username or password. (account not found)")
        if not account.verify_password(password):
            raise CommandException("Sorry, that was an incorrect username or password. (hash failed)")
        self.enactor.login(account)
        self.core.selectscreen(self.enactor)


class CreateCommand(_LoginCommand):
    name = "create"
    re_match = re.compile(r"^(?P<cmd>create)(?: +(?P<args>.+)?)?", flags=re.IGNORECASE)
    usage = "Usage: " + AnsiString.from_args("hw", 'create <username> <password>') + ' or ' + AnsiString.from_args("hw", 'create "<user name>" <password>')

    def execute(self):
        name, password = self.parse_login(self.usage)
        pass_hash = CRYPT_CON.hash(password)
        account, error = self.core.mapped_typeclasses["account"].create(name=name)
        if error:
            raise CommandException(error)
        account.set_password(pass_hash, nohash=True)
        # just ignoring password for now.
        cmd = f'connect "{account.name}" <password>' if ' ' in account.name else f'connect {account.name} <password>'
        self.msg(text="Account created! You can login with " + AnsiString.from_args('hw', cmd))


class WelcomeScreenCommand(_LoginCommand):
    name = "look"
    re_match = re.compile(r"^(?P<cmd>look)(?: +(?P<args>.+)?)?", flags=re.IGNORECASE)

    def execute(self):
        self.core.welcomescreen(self.enactor)


class HelpCommand(_LoginCommand):
    name = "help"
    re_match = re.compile(r"^(?P<cmd>help)(?: +(?P<args>.+)?)?", flags=re.IGNORECASE)

    def execute(self):
        self.msg(text="Pretend I'm showing some help here.")


class CharCreateCommand(Command):
    name = "charcreate"
    re_match = re.compile(r"^(?P<cmd>charcreate)(?: +(?P<args>.+)?)?", flags=re.IGNORECASE)

    def execute(self):
        mdict = self.match_obj.groupdict()
        if not (name := mdict.get("args", None)):
            raise CommandException("Must enter a name for the character!")
        char, error = self.core.mapped_typeclasses["mobile"].create(name=name)
        if error:
            raise CommandException(error)
        acc = self.enactor.get_account()
        acc.relations.set("account_characters", char, "present", True)
        self.msg(text=AnsiString(f"Character '{char.name}' created! Use ") + AnsiString.from_args("hw", f"charselect {char.name}") + " to join the game!")


class CharSelectCommand(Command):
    name = "charselect"
    re_match = re.compile(r"^(?P<cmd>charselect)(?: +(?P<args>.+)?)?", flags=re.IGNORECASE)

    def execute(self):
        mdict = self.match_obj.groupdict()
        acc = self.enactor.get_account()
        chars = acc.relations.all('account_characters')
        if not (args := mdict.get("args", None)):
            names = ', '.join([obj.name for obj in chars])
            self.msg(text=f"You have the following characters: {names}")
            return
        if not (found := partial_match(args, chars, key=lambda x: x.name)):
            self.msg(text=f"Sorry, no character found named: {args}")
            return
        pview, errors = found.get_or_create_playview()
        if errors:
            raise CommandException(errors)
        self.enactor.join(pview)

        if (pview := found.get_playview()):
            self.enactor.join(pview)
        else:
            pview, errors = self.core.mapped_typeclasses["playview"].create(objid=f"playview_{found.objid}")
            pview.set_character(found)


class SelectScreenCommand(Command):
    name = "look"
    re_match = re.compile(r"^(?P<cmd>look)(?: +(?P<args>.+)?)?", flags=re.IGNORECASE)

    def execute(self):
        self.core.selectscreen(self.enactor)


class ThinkCommand(MushCommand):
    name = "think"
    aliases = ['th', 'thi', 'thin']

    def execute(self):
        if self.args:
            result, remaining, stopped = self.entry.evaluate(self.remaining)
            if result:
                self.msg(text=result)


class ImportCommand(Command):
    name = "@import"
    re_match = re.compile(r"^(?P<cmd>@import)(?: +(?P<args>.+)?)?", flags=re.IGNORECASE)
    options = ['start', 'rooms', 'exits', 'accounts', 'players']

    def execute(self):
        mdict = self.match_obj.groupdict()
        args = mdict.get("args", None)
        if not args:
            raise CommandException("@import requires arguments!")

        if not (op := partial_match(args, self.options)):
            raise CommandException(f"Invalid operation for @import. supports: {self.options}")

        op_map = {
            'start': self.op_start,
            'rooms': self.op_rooms,
            'exits': self.op_exits,
            'accounts': self.op_accounts,
            'players': self.op_players
        }
        if op != 'start' and not hasattr(self.enactor, 'penn'):
            raise CommandException("@import database is not loaded. use @import start")
        op_map[op]()

    def op_start(self):
        if hasattr(self.enactor, 'penn'):
            raise CommandException("@import already loaded database.")
        Importer(self.enactor, 'outdb')
        self.msg("Database loaded and ready to Import!")

    def op_rooms(self):
        out = self.enactor.penn.import_rooms()
        self.msg(f"Imported {len(out)} Rooms!")

    def op_exits(self):
        out = self.enactor.penn.import_exits()
        self.msg(f"Imported {len(out)} Exits!")

    def op_accounts(self):
        out = self.enactor.penn.import_accounts()
        self.msg(f"Imported {len(out)} Accounts!")

    def op_players(self):
        out = self.enactor.penn.import_characters()
        self.msg(f"Imported {len(out)} Players!")


class PyCommand(Command):
    name = '@py'
    re_match = re.compile(r"^(?P<cmd>@py)(?: +(?P<args>.+)?)?", flags=re.IGNORECASE)

    def execute(self):
        mdict = self.match_obj.groupdict()
        args = mdict.get("args", None)
        if not args:
            raise CommandException("@py requires arguments!")

        available_vars = {
            'self': self.enactor,
            "shinma": self.enactor.core.engine,
            "core": self.enactor.core
        }

        self.msg(text=f">>> {args}")

        try:
            # reroute standard output to game client console
            old_stdout = sys.stdout
            old_stderr = sys.stderr

            class FakeStd:
                def __init__(self, caller):
                    self.caller = caller

                def write(self, string):
                    self.caller.msg(text=string.rsplit("\n", 1)[0])

            fake_std = FakeStd(self.enactor)
            sys.stdout = fake_std
            sys.stderr = fake_std

            mode = "eval"
            try:
                pycode_compiled = compile(args, "", mode)
            except Exception:
                mode = "exec"
                pycode_compiled = compile(args, "", mode)

            measure_time = True
            duration = ""
            if measure_time:
                t0 = time.time()
                ret = eval(pycode_compiled, {}, available_vars)
                t1 = time.time()
                duration = " (runtime ~ %.4f ms)" % ((t1 - t0) * 1000)
                self.enactor.msg(text=duration)
            else:
                ret = eval(pycode_compiled, {}, available_vars)

        except Exception:
            errlist = traceback.format_exc().split("\n")
            if len(errlist) > 4:
                errlist = errlist[4:]
            ret = "\n".join("%s" % line for line in errlist if line)
        finally:
            # return to old stdout
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        if ret is None:
            return
        elif isinstance(ret, tuple):
            # we must convert here to allow msg to pass it (a tuple is confused
            # with a outputfunc structure)
            ret = str(ret)

        self.enactor.msg(text=ret)


class LoginCommandMatcher(PythonCommandMatcher):

    def access(self, enactor):
        return enactor.get_account() is None

    def at_cmdmatcher_creation(self):
        self.add(CreateCommand)
        self.add(ConnectCommand)
        self.add(HelpCommand)
        self.add(WelcomeScreenCommand)


class SelectCommandMatcher(PythonCommandMatcher):

    def access(self, enactor):
        return enactor.get_account() is not None

    def at_cmdmatcher_creation(self):
        self.add(CharSelectCommand)
        self.add(CharCreateCommand)
        self.add(SelectScreenCommand)
        self.add(ThinkCommand)


class ConnectionCommandMatcher(PythonCommandMatcher):

    def at_cmdmatcher_creation(self):
        self.add(PyCommand)
        self.add(ImportCommand)