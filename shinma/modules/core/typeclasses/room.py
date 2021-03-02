from . base import BaseTypeClass


class RoomTypeClass(BaseTypeClass):
    typeclass_name = "CoreRoom"
    prefix = "room"
    class_initial_data = {
        "tags": ["room"]
    }

