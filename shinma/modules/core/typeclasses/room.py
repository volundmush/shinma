from . base import BaseTypeClass, Msg


class RoomTypeClass(BaseTypeClass):
    typeclass_name = "room"
    prefix = "room"
    initial_data = {
        "tags": "room"
    }