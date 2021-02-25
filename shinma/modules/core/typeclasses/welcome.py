from . base import BaseTypeClass, Msg


class WelcomeScreenTypeClass(BaseTypeClass):
    typeclass_name = "welcomescreen"
    prefix = "welcomescreen"
    class_initial_data = {
        "tags": ["welcomescreen"]
    }