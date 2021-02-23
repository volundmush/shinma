from . attributes import AttributeCategory
from typing import Any, Dict
from . import GameObjectException


class ContentsKind:
    __slots__ = ["handler", "name", "objects", "reverse"]

    def __init__(self, handler, name):
        self.handler = handler
        self.name = name
        self.objects = dict()
        self.reverse = set()

    def get(self, objid: str, name: str):
        if (cat := self.objects.get(objid, None)):
            return cat.get(name)
        return None

    def set(self, objid: str, name: str, value: Any):
        if value is None:
            raise GameObjectException("Attributes cannot be set to None.")
        if (cat := self.objects.get(objid, None)):
            return cat.set(name, value)
        else:
            cat = AttributeCategory(self, name)
            self.objects[objid] = cat
            return cat.set(name, value)

    def delete(self, objid: str, name: str = None):
        if (cat := self.objects.get(objid, None)):
            if name is None:
                cat = self.objects.pop(objid, None)
                return cat.all()
            else:
                return cat.delete(name)

    def clear(self, objid: str = None):
        if not objid:
            for k, v in self.objects.items():
                try:
                    obj = self.handler.obj.manager.get(k)
                    obj.locations[self.name].remove(self.handler.obj.objid)
                except Exception as e:
                    pass
            self.objects.clear()
        else:
            if (cat := self.objects.get(objid, None)):
                return cat.clear()

    def load_objid(self, objid: str, attr: Dict[str, Any]):
        if not (cat := self.objects.get(objid, None)):
            cat = AttributeCategory(self, objid)
            self.objects[objid] = cat
        for k, v in attr.items():
            cat.set(k, v)

    def dump(self):
        return {k: dump for k, v in self.objects.items() if (dump := v.dump())}


class ContentsHandler:
    __slots__ = ["obj", "contents", "reverse"]

    def __init__(self, obj):
        self.obj = obj
        self.contents = dict()
        self.reverse = set()

    def dump(self):
        return {k: dump for k, v in self.contents.items() if (dump := v.dump())}

    def get_kind(self, kind: str):
        if not (con := self.contents.get(kind, None)):
            con = ContentsKind(self, kind)
            self.contents[kind] = con
        return con

    def set(self, kind: str, objid: str, name: str, value: Any):
        if value is None:
            raise GameObjectException("Attributes cannot be set to None.")
        con = self.get_kind(kind)
        return con.set(objid, name, value)

    def delete(self, kind: str, objid: str, name: str = None):
        if not (con := self.contents.get(kind, None)):
            return
        return con.delete(objid, name)

    def get(self, kind: str, objid: str, name: str):
        if not (con := self.contents.get(kind, None)):
            return None
        return con.get(objid, name)

    def all(self, kind: str = None, objid: str = None):
        if not kind:
            return self.contents.keys()
        if not (con := self.contents.get(kind, None)):
            return dict()
        return con.all(objid)

    def has(self, kind: str, objid: str = None, name: str = None):
        con = self.get_kind(kind)
        if not objid:
            return bool(len(con.objects))
        if not (obj := con.objects.get(objid, None)):
            return False
        if name:
            return obj.has(name)
        else:
            return bool(len(obj.attributes))

    def clear(self, kind: str = None):
        if not kind:
            for k in self.contents.keys():
                self.clear(k)
        else:
            if (con := self.contents.pop(kind, None)):
                con.clear()

    def load_contents(self, kind: str, objid: str, attr: Dict[str, Any]):
        if not (con := self.contents.get(kind, None)):
            con = ContentsKind(self, kind)
            self.contents[kind] = con
        con.load_objid(objid, attr)
