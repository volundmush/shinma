import re
from . base import BaseCommand, CoreModuleException


class _LoginCommand(BaseCommand):
    re_quoted = re.compile(r'"(?P<name>.+)"(: +(?P<password>.+)?)?', flags=re.IGNORECASE)
    re_unquoted = re.compile(r'^(?P<name>\S+)(?: +(?P<password>.+)?)?', flags=re.IGNORECASE)

    @classmethod
    def access(cls, enactor):
        if enactor.netobj:
            if not enactor.netobj.session:
                return True
        return False

    def parse_login(self, error):
        mdict = self.match_obj.groupdict()
        if not mdict["args"]:
            raise CoreModuleException(error)

        result = self.re_quoted.fullmatch(mdict["args"])
        if not result:
            result = self.re_unquoted.fullmatch(mdict["args"])
        rdict = result.groupdict()
        if not (rdict["name"] and rdict["password"]):
            raise CoreModuleException(error)
        return rdict["name"], rdict["password"]


class ConnectCommand(_LoginCommand):
    re_match = re.compile(r"^(?P<cmd>connect)(?: +(?P<args>.+))?", flags=re.IGNORECASE)

    def do_execute(self):
        name, password = self.parse_login('Usage: |wconnect <username> <password>|n or |wconnect "<user name>" password|n')
        account = self.game.find_account(name)
        if not account:
            raise CoreModuleException("Sorry, that was an incorrect username or password.")
        if (sess := self.enactor.netobj.authenticate(account, password)):
            self.enactor.netobj.login(sess)
        else:
            raise CoreModuleException("Sorry, that was an incorrect username or password.")


class CreateCommand(_LoginCommand):
    re_match = re.compile(r"^(?P<cmd>create)(?: +(?P<args>.+)?)?", flags=re.IGNORECASE)

    def do_execute(self):
        name, password = self.parse_login('Usage: |create <username> <password>|n or |wcreate "<user name>" password|n')
        account, error = self.game.create_account(name, password)
        if error:
            raise CoreModuleException(error)
        cmd = f'connect "{account.name}" <password>' if ' ' in account.name else f'connect {account.name} <password>'
        self.msg(text=f"Account created! You can login with |w{cmd}|n")


class HelpCommand(_LoginCommand):

    def execute(self):
        self.msg(text="Pretend I'm showing some help here.")


class _AuthCommand(BaseCommand):

    @classmethod
    def access(cls, enactor):
        if enactor.netobj:
            if enactor.netobj.session and not enactor.netobj.playview:
                return True
        return False


class CharCreateCommand(_AuthCommand):
    re_match = re.compile(r"^(?P<cmd>charcreate)(?: +(?P<args>.+)?)?", flags=re.IGNORECASE)

    def do_execute(self):
        mdict = self.match_obj.groupdict()
        if not (name := mdict.get("args", None)):
            raise CoreModuleException("Must enter a name for the character!")
        char, error = self.game.spawn_object(self.app.settings.PROTOTYPES["character"], name=name)
        if error:
            raise CoreModuleException(error)
        sess = self.enactor.netobj.session
        char.create_relation(sess.account, "character_of")
        self.msg(text="Character '{char.name}' created! Use |wcharselect {char.name}|n to join the game!")

