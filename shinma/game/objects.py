from collections import defaultdict


class Tag:
    __slots__ = ["name", "description", "objects"]

    def __init__(self, name):
        self.name = name
        self.description = None
        self.objects = set()


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
    __slots__ = ["parent", "categories"]

    def __init__(self, parent):
        self.parent = parent
        self.categories = dict()


class RelationKind:
    __slots__ = ["attributes", "reverse"]

    def __init__(self):
        self.attributes = AttributeHandler(self)
        self.reverse = set()


class RelationHandler:
    __slots__ = ["parent", "target", "kinds"]

    def __init__(self, parent, target):
        self.parent = parent
        self.kinds = dict()


class ACLEntry:
    __slots__ = ["target", "mode", "allow", "deny"]

    def __init__(self, target, mode, allow, deny):
        self.target = target
        self.mode = mode
        self.allow = allow
        self.deny = deny


class ACLHandler:
    """
    This should be sub-classed to
    """
    __slots__ = ["parent", "entries", "entries_sorted", "reverse"]

    def __init__(self, parent):
        self.parent = parent
        self.entries = defaultdict(dict)
        self.entries_sorted = list()
        self.reverse = set()


class GamePrototype:
    __slots__ = ["module", "name", "keywords", "objid_prefix", "namespace", "attributes", "relations",
                 "prototypes", "inventories", "acl", "acl_class", "objects", "tags", "cmdsets"]

    def __init__(self, module, name: str):
        self.module = module
        self.name = name
        self.keywords = set()
        self.objid_prefix = ""
        self.namespace = None
        self.attributes = AttributeHandler(self)
        self.inventories = dict()
        self.relations = dict()
        self.prototypes = list()
        self.acl = dict()
        self.acl_class = None
        self.objects = set()
        self.tags = set()
        self.cmdsets = set()

    def __str__(self):
        return self.name


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


class GameObject:
    __slots__ = ["module", "name", "keywords", "objid", "namespace", "attributes", "relations", "prototypes",
                 "acl", "location", "inventories", "date_created", "date_modified", "views", "controllers", "cmdsets"]

    def __init__(self, module, name: str, objid: str):
        self.module = module  # if this is none, the GameObject is unique to this game instance. Such as: Accounts
        self.name = name
        self.keywords = set()
        self.objid = objid
        self.namespace = None
        self.attributes = AttributeHandler(self)
        self.relations = dict()
        self.prototypes = list()
        self.acl = None
        self.location = GameLocation(self)
        self.inventories = dict()
        self.date_created = None
        self.date_modified = None
        self.cmdsets = set()

        # These two are special and only used for GameObjects which are being controlled by players.
        self.views = set()
        self.controllers = set()

    def __str__(self):
        return self.objid