from shinma.core import ShinmaModule
from . objects import GameObject
from . tags import Tag


class GameObjectException(Exception):
    pass


class Module(ShinmaModule):
    name = "gamedb"
    version = "0.0.1"
    object_class = GameObject
    tag_class = Tag
    except_class = GameObjectException

    def __init__(self, engine, *args, **kwargs):
        super().__init__(engine, *args, **kwargs)
        self.objects = dict()
        self.object_defs = dict()
        self.tags = dict()
        self.preload_complete = False

    def preload_object(self, objid: str, name: str, data):
        if self.preload_complete:
            raise GameObjectException("Cannot Preload objects after preload complete")
        if objid in self.objects:
            raise GameObjectException(f"GameObjectManager already has objid: {objid}")
        self.objects[objid] = self.object_class(self, objid, name, initial_data=data)

    def process_preload(self):
        if self.preload_complete:
            raise GameObjectException("GameObjectManager is already preloaded.")
        for k, v in self.objects.items():
            v.load_initial()
        for k, v in self.objects.items():
            v.load_relations()
        self.preload_complete = True

    def get_tag(self, name: str):
        if (tag := self.tags.get(name, None)):
            return tag
        tag = self.tag_class(self, name)
        self.tags[name] = tag
        return tag

    def get(self, objid: str):
        if not (obj := self.objects.get(objid, None)):
            raise GameObjectException(f"objid {objid} does not exist.")
        return obj

    def delete(self, objid: str):
        obj = self.get(objid)
        obj.delete()
        del self.objects[objid]

    def create_object(self, objid: str, name: str, initial_data=None):
        if not self.preload_complete:
            raise GameObjectException(f"Preloading is not yet complete.")
        if objid in self.objects:
            raise GameObjectException(f"Objid {objid} is already in use!")
        gobj = GameObject(self, objid, name, initial_data)
        self.objects[objid] = gobj
        return gobj

    def dump(self):
        return {k: v.dump() for k, v in self.objects.items()}
