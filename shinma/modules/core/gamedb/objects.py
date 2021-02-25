from collections import defaultdict

from . attributes import AttributeHandler
from . relations import RelationsHandler
from . exception import GameObjectException


class GameObject:
    core = None
    __slots__ = ["name", "objid", "tags", "attributes", "relations", "reverse", "initial_data"]

    def __init__(self, objid: str, name: str, initial_data=None):
        self.name = name
        self.objid = objid
        self.attributes = AttributeHandler(self)
        self.relations = RelationsHandler(self)
        self.reverse = defaultdict(set)
        self.tags = dict()
        if initial_data is not None:
            self.initial_data = initial_data
        else:
            self.initial_data = dict()

    def __str__(self):
        return self.objid

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.objid} - {self.name}>"

    def load_initial(self):
        # laod tags - but don't set reverse on the Tag object just yet.
        for tagname in self.initial_data.get("tags", []):
            tag = self.core.get_tag(tagname)
            self.tags[tagname] = tag

        for k, v in self.initial_data.get("attributes", dict()).items():
            self.attributes.load_category(k, v)

    def load_relations(self):
        for k, v in self.initial_data.get("reverse", dict()):
            self.reverse[k] = self.reverse[k].union(v.keys())
            try:
                mapped = dict()
                for objid, attr in v.items():
                    mapped[self.core.get(objid)] = attr
            except GameObjectException as e:
                raise GameObjectException(f"Error while loading {self.objid} Reverse : {e}")
            for obj, attr in mapped.items():
                obj.relations.load_relations(k, self, attr)

        for tag in self.tags.values():
            tag.objects.add(self)

    def dump_gameobject(self):
        return ({
            "name": self.name,
            "attributes": self.attributes.dump(),
            "reverse": self.dump_reverse(),
            "tags": self.tags.keys()
        }, self.initial_data)

    def dump_reverse(self):
        out = defaultdict(dict)
        for k, v in self.reverse.items():
            for obj in v:
                out[k][obj.objid] = obj.contents[k].objects[self.objid].dump()
        return out

    def delete(self):
        for tag in self.tags.values():
            tag.objects.remove(self)
        for k, v in self.reverse.items():
            for obj in v:
                obj.contents[k].delete(self.objid)
