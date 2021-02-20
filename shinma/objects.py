from collections import defaultdict
from typing import Union, List, Dict
from asyncio import Queue
from shinma.prototypes import GamePrototype


class Tag:
    __slots__ = ["name", "description", "objects", "prototypes"]

    def __init__(self, name):
        self.name = name
        self.description = None
        self.objects = set()
        self.prototypes = set()


class Namespace:
    __slots__ = ["name", "abbreviation", "priority", "objects", "prototypes"]

    def __init__(self, name, abbreviation, priority: int = 0):
        self.name = name
        self.abbreviation = abbreviation
        self.priority = priority
        self.objects = set()
        self.prototypes = set()

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





class GameInventory:
    __slots__ = ["name", "parent", "contents", "octree"]

    def __init__(self, parent, name):
        self.name = name
        self.parent = parent
        self.contents = set()
        self.octree = None


class GameLocation:
    __slots__ = ["parent", "target", "inventory", "x", "y", "z", "reverse"]

    def __init__(self, parent):
        self.parent = parent
        self.target = None
        self.inventory = None
        self.x = 0
        self.y = 0
        self.z = 0
        self.reverse = defaultdict(set)


class Msg:
    __slots__ = ["source", "data", "relay_chain"]

    def __init__(self, source, **kwargs):
        self.source = source
        self.data = kwargs
        self.relay_chain = list()

    def relay(self, obj):
        c = self.__class__(self.source, **self.data)
        c.relay_chain = list(self.relay_chain)
        c.relay_chain.append(obj)
        return c


class GameObjectDef:
    __slots__ = ["module", "name", "keywords", "objid", "namespace", "attributes", "relations", "prototypes",
                 "acl", "location", "service", "inventories", "date_created",
                 "date_modified", "views", "cmdgroups", "scripts", "saved_locations"]

    def __init__(self, module, name: str, objid: str, prototypes: List[str]):
        self.module = module  # if this is none, the GameObject is unique to this game instance. Such as: Accounts
        self.name = name
        self.keywords = set()
        self.objid = objid
        self.namespace = None
        self.attributes = dict()
        self.relations = dict()
        self.prototypes = prototypes
        self.acl = None
        self.location = None
        self.saved_locations = dict()
        self.inventories = dict()
        self.date_created = None
        self.date_modified = None
        self.cmdgroups = dict()
        self.service = None
        self.scripts = set()

    def __str__(self):
        return self.objid


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


class Attribute:
    __slots__ = ["parent", "value"]

    def __init__(self, parent):
        self.parent = parent
        self.value = None


class AttributeCategory:
    __slots__ = ["parent", "attributes", "cached"]

    def __init__(self, parent):
        self.parent = parent
        self.attributes = dict()


class AttributeHandler:
    __slots__ = ["obj", "categories"]

    def __init__(self, obj):
        self.obj = obj
        self.categories = dict()

    def setup(self):
        pass


class Relation:
    __slots__ = ["attributes", "reverse", "has", "gameobj"]

    def __init__(self, gameobj):
        self.gameobj = gameobj
        self.has = False
        self.attributes = AttributeHandler(self)
        self.reverse = set()


class RelationHandler:
    __slots__ = ["obj", "relations"]

    def __init__(self, obj):
        self.obj = obj
        self.relations = dict()

    def setup(self):
        pass


class ACLEntry:
    __slots__ = ["target", "mode", "allow", "deny"]

    def __init__(self, target, mode, allow, deny):
        self.target = target
        self.mode = mode
        self.allow = allow
        self.deny = deny


class LocationHandler:

    def __init__(self, obj):
        self.obj = obj

    def setup(self):
        pass


class ContentsHandler:

    def __init__(self, obj):
        self.obj = obj

    def setup(self):
        pass


class CmdHandler:

    def __init__(self, obj):
        self.obj = obj
        self.queue = Queue()
        self.registered = False
        self.group_cache = None

    def execute_pending_commmand(self):
        if self.queue.empty():
            self.app.services["game"].pending_cmds.remove(self.obj)
            self.registered = False
            return
        text = self.queue.get_nowait()
        if text:
            self.execute_cmd(text)

    def execute_cmd(self, text):
        try:
            found = None
            for grp in self.get_cmd_groups():
                if (cmd := grp.match(self.obj, text)):
                    found = cmd
                    break
            if found:
                found.at_pre_execute()
                found.execute()
                found.at_post_execute()
            else:
                if self.obj.next_cmd_object:
                    self.obj.next_cmd_object.cmd.execute_cmd(text)
                else:
                    self.obj.msg(Msg(self.obj, text=f"Huh? Command '{text}' not recognized."))
        except Exception as e:
            print(f"something foofy: {e}")

    def get_cmd_groups(self):
        if self.group_cache is None:
            final = dict()
            for proto in self.obj.prototypes:
                final.update(proto.cmdgroups)
            self.group_cache = final
        return self.group_cache.values()

    def receive(self, text):
        self.queue.put_nowait(text)
        if not self.registered:
            self.app.services["game"].pending_cmds.add(self.obj)
            self.registered = True

    def setup(self):
        self.get_cmd_groups()


class ACLHandler:
    """
    This should be sub-classed to
    """
    __slots__ = ["obj", "entries", "entries_sorted", "reverse"]

    def __init__(self, obj):
        self.obj = obj
        self.entries = defaultdict(dict)
        self.entries_sorted = list()
        self.reverse = set()

    def setup(self):
        pass


class GameObject:
    __slots__ = ["game", "module", "name", "keywords", "objid", "namespace", "attributes", "relations", "prototypes",
                 "acl", "location", "service", "contents", "date_created", "next_cmd_object",
                 "date_modified", "views", "listeners", "netobj", "cmd", "scripts", "saved_locations"]

    def __init__(self, game, module, name: str, objid: str, prototypes: List[GamePrototype]):
        self.game = game
        self.module = module  # if this is none, the GameObject is unique to this game instance. Such as: Accounts
        self.name = name
        self.keywords = set()
        self.objid = objid
        self.namespace = None
        self.attributes = self.app.classes["game"]["attributehandler"](self)
        self.relations = self.app.classes["game"]["relationhandler"](self)
        self.prototypes = prototypes
        acl_class = self.app.classes["game"]["aclhandler"]
        for proto in prototypes:
            if proto.acl_class:
                acl_class = proto.acl_class
        self.acl = acl_class(self)
        self.location = self.app.classes["game"]["locationhandler"](self)
        self.contents = self.app.classes["game"]["contentshandler"](self)
        self.date_created = None
        self.date_modified = None
        self.cmd = self.app.classes["game"]["cmdhandler"](self)
        self.scripts = self.app.classes["game"]["scripthandler"](self)


    def __str__(self):
        return self.objid

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.objid} - {self.name}>"

    def setup(self):
        """
        This method is responsible for assembling all of the object's properties/traits/etc, without
        polluting the traits of any other object. It may raise a GameServiceException if setup should
        be aborted.
        """
        self.attributes.setup()
        self.relations.setup()
        self.location.setup()
        self.contents.setup()
        self.cmd.setup()
        self.scripts.setup()

        return (self, None)

    def setup_reverse(self):
        pass

    def msg(self, msg: Msg):
        for c in self.listeners:
            c.msg(msg.relay(self))

    def send(self, **kwargs):
        self.msg(Msg(source=self, **kwargs))


