from . base import BaseTypeClass, Msg


class MobileTypeClass(BaseTypeClass):
    typeclass_name = "mobile"
    prefix = "mobile"
    initial_data = {
        "tags": "mobile"
    }
