import re
from . base import Command, CommandException
from ...net.ansi import ANSIString


class _LoginCommand(Command):
    re_quoted = re.compile(r'"(?P<name>.+)"(: +(?P<password>.+)?)?', flags=re.IGNORECASE)
    re_unquoted = re.compile(r'^(?P<name>\S+)(?: +(?P<password>.+)?)?', flags=re.IGNORECASE)

    @classmethod
    def access(cls, enactor):
        # enactor should be a Connection here...
        return enactor.get_account() is None

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

    def execute(self):
        name, password = self.parse_login(ANSIString('Usage: |wconnect <username> <password>|n or |wconnect "<user name>" password|n'))
        account, error = self.game.search_namespace("account", name, exact=True)
        if error:
            raise CommandException(error)
        if not account:
            raise CommandException("Sorry, that was an incorrect username or password.")
        session, error = self.enactor.netobj.authenticate(account, password)
        if error:
            raise CommandException(error)
        self.enactor.netobj.login(session)


class CreateCommand(_LoginCommand):
    name = "create"
    re_match = re.compile(r"^(?P<cmd>create)(?: +(?P<args>.+)?)?", flags=re.IGNORECASE)

    def execute(self):
        name, password = self.parse_login(ANSIString('Usage: |wcreate <username> <password>|n or |wcreate "<user name>" password|n'))
        account, error = self.game.spawn_object(self.app.settings.PROTOTYPES["account"], name=name)
        if error:
            raise CommandException(error)
        # just ignoring password for now.
        cmd = f'connect "{account.name}" <password>' if ' ' in account.name else f'connect {account.name} <password>'
        self.msg(text=f"Account created! You can login with |w{cmd}|n")


class HelpCommand(_LoginCommand):
    name = "help"
    re_match = re.compile(r"^(?P<cmd>help)(?: +(?P<args>.+)?)?", flags=re.IGNORECASE)

    def execute(self):
        self.msg(text="Pretend I'm showing some help here.")


class _AuthCommand(Command):

    @classmethod
    def access(cls, enactor):
        return enactor.get_account() is not None


class CharCreateCommand(_AuthCommand):
    name = "charcreate"
    re_match = re.compile(r"^(?P<cmd>charcreate)(?: +(?P<args>.+)?)?", flags=re.IGNORECASE)

    def do_execute(self):
        mdict = self.match_obj.groupdict()
        if not (name := mdict.get("args", None)):
            raise CommandException("Must enter a name for the character!")
        char, error = self.game.spawn_object(self.app.settings.PROTOTYPES["character"], name=name)
        if error:
            raise CommandException(error)
        sess = self.enactor.netobj.session
        char.relations.create(sess.account, "character_of")
        self.msg(text=ANSIString("Character '{char.name}' created! Use |wcharselect {char.name}|n to join the game!"))


class CharSelectCommand(_AuthCommand):
    name = "charselect"
    re_match = re.compile(r"^(?P<cmd>charselect)(?: +(?P<args>.+)?)?", flags=re.IGNORECASE)

    def do_execute(self):
        self.msg(text="Not yet implemented...")
