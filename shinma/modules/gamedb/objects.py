from . attributes import AttributeHandler
from . contents import ContentsHandler
from collections import defaultdict
from . import GameObjectException


class ScriptHandler:

    def __init__(self, obj):
        self.obj = obj
        self.scripts = dict()

    def dispatch_event(self, event: str, *args, **kwargs):
        return [v.on_object_event(self.obj, event, *args, **kwargs) for k, v in self.scripts.items()]

    def setup(self):
        final = set()
        for proto in self.obj.prototypes:
            final = final.union(proto.scripts)
        self.scripts = {s.name: s for s in final}
        for s in final:
            s.objects.add(self.obj)


class GameObject:
    __slots__ = ["manager", "name", "objid", "tags", "attributes", "relations", "locations", "contents", "initial_data"]

    def __init__(self, manager, objid: str, name: str, initial_data=None):
        self.manager = manager
        self.name = name
        self.objid = objid
        self.attributes = AttributeHandler(self)
        self.contents = ContentsHandler(self)
        self.locations = defaultdict(set)
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
            tag = self.manager.get_tag(tagname)
            self.tags[tagname] = tag

        for k, v in self.initial_data.get("attributes", dict()).items():
            self.attributes.load_category(k, v)

    def load_relations(self):
        for k, v in self.initial_data.get("locations", dict()):
            self.locations[k] = self.locations[k].union(v.keys())
            for objid, attr in v.items():
                try:
                    obj = self.manager.get(objid)
                    obj.contents.load_contents(k, self.objid, attr)
                except GameObjectException as e:
                    raise GameObjectException(f"Error while loading {self.objid} Locations {objid}: {e}")

        for tag in self.tags.values():
            tag.objects.add(self)

    def dump(self):
        return ({
            "name": self.name,
            "attributes": self.attributes.dump(),
            "locations": self.dump_locations(),
            "tags": self.tags.keys()
        }, self.initial_data)

    def dump_locations(self):
        out = defaultdict(dict)
        for k, v in self.locations.items():
            for obj in v:
                out[k][obj.objid] = obj.contents[k].objects[self.objid].dump()
        return out

    def delete(self):
        for tag in self.tags.values():
            tag.objects.remove(self)
        for k, v in self.locations.items():
            for obj in v:
                obj.contents[k].delete(self.objid)
