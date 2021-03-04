from . base import BaseTypeClass
from shinma.utils import lazy_property


class RoomTypeClass(BaseTypeClass):
    typeclass_name = "CoreRoom"
    typeclass_family = 'room'
    prefix = "room"
    class_initial_data = {
        "tags": ["room"]
    }
