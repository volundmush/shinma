from . base import BaseTypeClass, Msg


class ExitTypeClass(BaseTypeClass):
    typeclass_name = "CoreExit"
    prefix = "exit"
    class_initial_data = {
        "tags": ["exit"]
    }