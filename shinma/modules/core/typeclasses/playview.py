from . base import BaseTypeClass, Msg


class PlayViewTypeClass(BaseTypeClass):
    typeclass_name = "playview"
    prefix = "playview"
    initial_data = {
        "tags": "playview"
    }

    def get_puppet(self):
        pass

    def get_character(self):
        pass

    def get_next_cmd_object(self, obj_chain):
        return self.get_puppet()

    def get_connections(self):
        return list()

    def listeners(self):
        return self.get_connections()