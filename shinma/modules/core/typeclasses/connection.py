from . base import BaseTypeClass, Msg


class ConnectionTypeClass(BaseTypeClass):
    typeclass_name = "connection"
    prefix = "connection"
    initial_data = {
        "tags": ["connection"],
        "locations": {"contents": {"WelcomeScreen": {"here": True}}}
    }

    def __init__(self, obj):
        super().__init__(obj)
        self.connection = None
        self.account = None
        self.playview = None


    def receive_msg(self, message: Msg):
        if self.connection:
            self.connection.msg(message.data)

    def receive_relayed_msg(self, message: Msg):
        self.receive_msg(message)

    def get_account(self):
        return self._get_obj("_core", "account", "account")

    def get_playview(self):
        return self._get_obj("_core", "playview", "playview")

    def get_cmd_groups(self):
        return [self.core.cmdgroups["connection"]]

    def get_next_cmd_object(self, obj_chain):
        return self.get_account()
