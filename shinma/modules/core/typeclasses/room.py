from . base import BaseTypeClass, Msg


class RoomTypeClass(BaseTypeClass):
    typeclass_name = "CoreRoom"
    prefix = "room"
    class_initial_data = {
        "tags": ["room"]
    }