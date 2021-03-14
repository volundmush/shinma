from . base import BaseTypeClass
from ..utils.styling import StyleHandler
import time


class ConnectionTypeClass(BaseTypeClass):
    typeclass_name = "CoreConnection"
    typeclass_family = 'connection'
    prefix = "connection"
    class_initial_data = {
        "tags": ["connection"],
    }
    command_families = ["connection"]
    base_style = None

    __slots__ = ['connection']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection = None

    def init_attributes(self):
        self.attributes.set('core', 'last_cmd', time.time())

    def time_connected(self):
        return time.time() - self.attributes.get('core', 'datetime_created')

    def time_idle(self):
        return time.time() - self.attributes.get('core', 'last_cmd')

    def receive_msg(self, message):
        if self.connection:
            message.send(self)

    def get_next_cmd_object(self, obj_chain):
        return self.relations.get('account', None)

    def login(self, account):
        a = account.connections.all()
        account.connections.add(self)
        if not account.attributes.get('core', 'last_login'):
            self.core.engine.dispatch_module_event('core_account_at_first_login', account=account, connection=self)
        account.attributes.set('core', 'last_login', time.time())
        if not a:
            self.core.engine.dispatch_module_event('core_account_at_cold_login', account=account, connection=self)
        self.core.engine.dispatch_module_event('core_account_at_login', account=account, connection=self)

    def logout(self):
        if (account := self.relations.get('account', None)):
            account.connections.remove(self)
            self.core.engine.dispatch_module_event('core_account_at_logout', account=account, connection=self)
            if not (account.connections.all()):
                self.core.engine.dispatch_module_event('core_account_at_complete_logout', account=account, connection=self)

    def get_width(self):
        if self.connection:
            return self.connection.width
        return 78

    @property
    def style(self):
        if (acc := self.relations.get('account', None)):
            return acc.style
        else:
            if (st := self.base_style):
                return st
            else:
                self.__class__.base_style = StyleHandler(self.__class__, save=False)
                return self.base_style

    def join(self, playview):
        playview.connections.add(self)
        playview.at_connection_join(self)

    def leave(self):
        if (play := self.relations.get('playview', None)):
            play.connections.remove(self)
            play.at_connection_leave(self)
            if not play.connections.all():
                play.at_last_connection_leave(self)

    def close_connection(self, reason: str = 'quit'):
        self.logout()
        self.leave()
        self.core.delete(self)
        self.core.engine.dispatch_module_event('net_connection_kick', id=self.objid, reason=reason)

    def get_slevel(self):
        if (acc := self.relations.get('account', None)):
            return acc.get_slevel()
        else:
            return super().get_slevel()