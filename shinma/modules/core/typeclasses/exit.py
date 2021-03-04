from . base import BaseTypeClass


class ExitTypeClass(BaseTypeClass):
    typeclass_name = "CoreExit"
    typeclass_family = 'exit'
    prefix = "exit"
    class_initial_data = {
        "tags": ["exit"]
    }