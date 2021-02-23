from . base import BaseTypeClass, Msg


class ExitTypeClass(BaseTypeClass):
    typeclass_name = "exit"
    prefix = "exit"
    initial_data = {
        "tags": "exit"
    }