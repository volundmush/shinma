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

    def __init__(self, objid: str, name: str, initial_data=None):
        super().__init__(objid, name, initial_data)
        self.connection = None

    def receive_msg(self, message):
        if self.connection:
            message.send(self)

    def get_next_cmd_object(self, obj_chain):
        return self.relations.get('account')

    def login(self, account):
        self.relations.set('account', account)
        account.reverse.add('connections', self)
        account.at_login(self)

    def logout(self):
        if (account := self.relations.get('account')):
            account.remove_connection(self)
            account.at_logout(self)

    def get_width(self):
        if self.connection:
            return self.connection.width
        return 78

    @property
    def style(self):
        if (acc := self.relations.get('account')):
            return acc.style
        else:
            if (st := self.base_style):
                return st
            else:
                self.__class__.base_style = StyleHandler(self.__class__, save=False)
                return self.base_style

    def join(self, playview, created: bool = False):
        playview.reverse.add('connections', self)
        self.attributes.set('core', 'playview', playview.objid)
        self.relations.set('playview', playview)
        if created:
            playview.at_playview_creation(self)
        playview.at_connection_join(self)
