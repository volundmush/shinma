from . base import BaseTypeClass


class ExitTypeClass(BaseTypeClass):
    typeclass_name = "CoreExit"
    prefix = "exit"
    class_initial_data = {
        "tags": ["exit"]
    }