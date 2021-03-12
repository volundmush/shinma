import weakref
from . attributes import AttributeHandler
from . exception import GameObjectException


class GameObject:
    core = None
    __slots__ = ["name", "objid", "tags", "attributes", "initial_data", "aliases", "asset", 'relations', 'identity']

    def __init__(self, objid: str, name: str, initial_data=None, asset: bool = False):
        self.name = name
        self.aliases = list()
        self.objid = objid
        self.attributes = AttributeHandler(self)
        self.tags = dict()
        self.asset = asset
        self.relations = weakref.WeakValueDictionary()
        self.identity = None
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
            tag.objects.add(self)

        for k, v in self.initial_data.get("attributes", dict()).items():
            self.attributes.load_category(k, v)

    def dump_gameobject(self):
        return ({
            "name": self.name,
            "attributes": self.attributes.dump(),
            "tags": self.tags.keys()
        }, self.initial_data)

    def delete(self):
        for tag in self.tags.values():
            tag.objects.remove(self)
