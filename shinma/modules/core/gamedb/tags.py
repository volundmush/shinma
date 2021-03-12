import weakref


class Tag:
    __slots__ = ["manager", "name", "objects"]

    def __init__(self, manager, name):
        self.manager = manager
        self.name = name
        self.objects = weakref.WeakSet()

    def search(self, name, exact=False):
        upper = name.upper()
        if exact:
            for obj in self.objects:
                if obj.name.upper() == upper:
                    return obj, None
        else:
            if results := {obj for obj in self.objects if obj.name.upper().startswith(upper)}:
                return results, None
        return None, "Nothing found."

    def all(self):
        return set(self.objects)
