from . base import BaseTypeClass, Msg


class AccountTypeClass(BaseTypeClass):
    typeclass_name = "account"
    prefix = "account"
    initial_data = {
        "tags": ["account"]
    }

    def get_next_cmd_object(self, obj_chain):
        if (conn := obj_chain.get("connection")):
            return conn.get_playview()

    def listeners(self):
        # the listeners of an Account should be all Connections which are
        # logged-in to it at the moment.

        # This shouldn't be used much, though...
        return list()