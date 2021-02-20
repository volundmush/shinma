class GamePrototypeDef:
    __slots__ = ["module", "name", "keywords", "objid_prefix", "namespaces", "attributes", "relations",
                 "inventories", "acl", "acl_class", "objects", "tags", "cmdgroups", "scripts",
                 "saved_locations"]

    def __init__(self, module, name: str):
        self.module = module
        self.name = name
        self.keywords = set()
        self.objid_prefix = ""
        self.namespaces = set()
        self.attributes = dict()
        self.inventories = dict()
        self.relations = dict()
        self.saved_locations = dict()
        self.acl = dict()
        self.acl_class = None
        self.objects = set()
        self.tags = set()
        self.cmdgroups = dict()
        self.scripts = set()

    def __str__(self):
        return self.name


class GamePrototype:
    __slots__ = ["module", "name", "keywords", "objid_prefix", "namespaces", "attributes", "relations",
                 "prototypes", "inventories", "acl", "acl_class", "objects", "tags", "cmdgroups", "scripts",
                 "saved_locations"]

    def __init__(self, module, name: str):
        self.module = module
        self.name = name
        self.keywords = set()
        self.objid_prefix = ""
        self.namespaces = set()
        self.attributes = dict()
        self.inventories = dict()
        self.relations = dict()
        self.prototypes = list()
        self.saved_locations = dict()
        self.acl = dict()
        self.acl_class = None
        self.objects = set()
        self.tags = set()
        self.cmdgroups = dict()
        self.scripts = set()

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"