from . base import BaseTypeClass
from .. mush.ansi import AnsiString
from ..utils.styling import StyleHandler


class ConnectionTypeClass(BaseTypeClass):
    typeclass_name = "CoreConnection"
    typeclass_family = 'connection'
    prefix = "connection"
    class_initial_data = {
        "tags": ["connection"],
        "locations": {"contents": {"WelcomeScreen": {"here": True}}}
    }
    command_families = ["connection"]
    base_style = None

    __slots__ = ['connection']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection = None

    def receive_msg(self, message):
        if self.connection:
            message.send(self)

    def get_next_cmd_object(self, obj_chain):
        return self.relations.get('connection_account')

    def login(self, account):
        self.relations.set('connection_account', account)
        account.at_login(self)

    def logout(self):
        if (account := self.relations.get('connection_account')):
            account.remove_connection(self)
            account.at_logout(self)

    def get_width(self):
        if self.connection:
            return self.connection.width
        return 78

    @property
    def style(self):
        if (acc := self.relations.get('connection_account')):
            return acc.style
        else:
            if (st := self.base_style):
                return st
            else:
                self.__class__.base_style = StyleHandler(self.__class__, save=False)
                return self.base_style

    def join(self, playview, created: bool = False):
        self.relations.set('connection_playview', playview)
        if created:
            playview.at_playview_creation(self)
        playview.at_connection_join(self)
