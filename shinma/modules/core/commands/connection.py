import re
from . base import Command, CommandException, PythonCommandMatcher
from ...net.ansi import ANSIString
from shinma.utils import partial_match


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

    def execute(self):
        name, password = self.parse_login(ANSIString('Usage: |wconnect <username> <password>|n or |wconnect "<user name>" password|n'))
        account, error = self.core.search_tag("account", name, exact=True)
        if error:
            raise CommandException(error)
        if not account:
            raise CommandException("Sorry, that was an incorrect username or password.")
        self.enactor.login(account)
        self.core.selectscreen(self.enactor)


class CreateCommand(_LoginCommand):
    name = "create"
    re_match = re.compile(r"^(?P<cmd>create)(?: +(?P<args>.+)?)?", flags=re.IGNORECASE)

    def execute(self):
        name, password = self.parse_login(ANSIString('Usage: |wcreate <username> <password>|n or |wcreate "<user name>" password|n'))
        account, error = self.core.mapped_typeclasses["account"].create(name=name)
        if error:
            raise CommandException(error)
        # just ignoring password for now.
        cmd = f'connect "{account.name}" <password>' if ' ' in account.name else f'connect {account.name} <password>'
        self.msg(text=f"Account created! You can login with |w{cmd}|n")


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
        self.msg(text=ANSIString(f"Character '{char.name}' created! Use |wcharselect {char.name}|n to join the game!"))


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
