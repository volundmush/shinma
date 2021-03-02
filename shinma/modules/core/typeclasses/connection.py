from . base import BaseTypeClass
from .. mush.ansi import AnsiString


class ConnectionTypeClass(BaseTypeClass):
    typeclass_name = "CoreConnection"
    prefix = "connection"
    class_initial_data = {
        "tags": ["connection"],
        "locations": {"contents": {"WelcomeScreen": {"here": True}}}
    }
    command_families = ["connection"]

    __slots__ = ['connection']

    def __init__(self, objid: str, name: str, initial_data=None):
        super().__init__(objid, name, initial_data)
        self.connection = None

    def receive_msg(self, message):
        if self.connection:
            out = dict()

            if text := message.render(self):
                out['text'] = text.render(ansi=self.connection.ansi, xterm256=self.connection.xterm256,
                                              mxp=self.connection.mxp)
            if data := message.data(self):
                out['data'] = data

            if out:
                self.connection.msg(out)

    def receive_relayed_msg(self, message):
        self.receive_msg(message)

    def get_account(self):
        if (all := self.reverse["account_connections"]):
            return list(all)[0]

    def get_playview(self):
        if (all := self.reverse["playview_connections"]):
            return list(all)[0]

    def get_next_cmd_object(self, obj_chain):
        return self.get_account()

    def login(self, account):
        account.add_connection(self)
        account.at_login(self)

    def logout(self):
        if (account := self.get_account()):
            account.remove_connection(self)
            account.at_logout(self)

    def get_width(self):
        if self.connection:
            return self.connection.width
        return 78
