from . base import BaseTypeClass, Msg


class MobileTypeClass(BaseTypeClass):
    typeclass_name = "CoreMobile"
    prefix = "mobile"
    class_initial_data = {
        "tags": ["mobile"]
    }
