from typing import Any, Dict
from . attributes import AttributeCategory
from . exception import GameObjectException


class RelationsKind:
    __slots__ = ["handler", "name", "objects", "reverse"]

    def __init__(self, handler, name):
        self.handler = handler
        self.name = name
        self.objects = dict()
        self.reverse = set()

    def get(self, obj: str, name: str):
        if (cat := self.objects.get(obj, None)):
            return cat.get(name)
        return None

    def set(self, obj: str, name: str, value: Any):
        if value is None:
            raise GameObjectException("Attributes cannot be set to None.")
        if (cat := self.objects.get(obj, None)):
            return cat.set(name, value)
        else:
            cat = AttributeCategory(self, name)
            self.objects[obj] = cat
            return cat.set(name, value)

    def delete(self, obj: str, name: str = None):
        if (cat := self.objects.get(obj, None)):
            if name is None:
                cat = self.objects.pop(obj, None)
                return cat.all()
            else:
                return cat.delete(name)

    def clear(self, obj: str = None):
        if not obj:
            for k, v in self.objects.items():
                try:
                    obj.reverse[self.name].remove(self.handler.obj.objid)
                except Exception as e:
                    pass
            self.objects.clear()
        else:
            if (cat := self.objects.get(obj, None)):
                return cat.clear()

    def load_objid(self, obj: str, attr: Dict[str, Any]):
        if not (cat := self.objects.get(obj, None)):
            cat = AttributeCategory(self, obj)
            self.objects[obj] = cat
        for k, v in attr.items():
            cat.set(k, v)

    def dump(self):
        return {k.objid: dump for k, v in self.objects.items() if (dump := v.dump())}

    def all(self, obj=None):
        if not obj:
            return self.objects.keys()
        if not (cat := self.objects.get(obj, None)):
            return []
        return cat.all()


class RelationsHandler:
    __slots__ = ["obj", "relations", "reverse"]

    def __init__(self, obj):
        self.obj = obj
        self.relations = dict()
        self.reverse = set()

    def dump(self):
        return {k: dump for k, v in self.relations.items() if (dump := v.dump())}

    def get_kind(self, kind: str):
        if not (con := self.relations.get(kind, None)):
            con = RelationsKind(self, kind)
            self.relations[kind] = con
        return con

    def set(self, kind: str, obj: str, name: str, value: Any):
        if value is None:
            raise GameObjectException("Attributes cannot be set to None.")
        con = self.get_kind(kind)
        return con.set(obj, name, value)

    def delete(self, kind: str, objid: str, name: str = None):
        if not (con := self.relations.get(kind, None)):
            return
        return con.delete(objid, name)

    def get(self, kind: str, objid: str, name: str):
        if not (con := self.relations.get(kind, None)):
            return None
        return con.get(objid, name)

    def all(self, kind: str = None, objid: str = None):
        if not kind:
            return self.relations.keys()
        if not (con := self.relations.get(kind, None)):
            return dict()
        return con.all(objid)

    def has(self, kind: str, obj: str = None, name: str = None):
        con = self.get_kind(kind)
        if not obj:
            return bool(len(con.objects))
        if not (obj := con.objects.get(obj, None)):
            return False
        if name:
            return obj.has(name)
        else:
            return bool(len(obj.attributes))

    def clear(self, kind: str = None):
        if not kind:
            for k in self.relations.keys():
                self.clear(k)
        else:
            if (con := self.relations.pop(kind, None)):
                con.clear()

    def load_relations(self, kind: str, obj: str, attr: Dict[str, Any]):
        if not (con := self.relations.get(kind, None)):
            con = RelationsKind(self, kind)
            self.relations[kind] = con
        con.load_objid(obj, attr)
