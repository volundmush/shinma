class GamePrototypeDef:
    __slots__ = ["module", "name", "keywords", "objid_prefix", "namespaces", "attributes", "relations",
                 "objects", "tags", "cmdgroups", "scripts",]

    def __init__(self, module, name: str):
        self.module = module
        self.name = name
        self.keywords = set()
        self.objid_prefix = ""
        self.namespaces = set()
        self.attributes = dict()
        self.relations = dict()
        self.objects = set()
        self.tags = set()
        self.scripts = set()

    def __str__(self):
        return self.name


class GamePrototype:
    __slots__ = ["module", "name", "objid_prefix", "namespaces", "attributes", "relations",
                 "prototypes", "objects", "tags", "scripts"]

    def __init__(self, module, name: str):
        self.module = module
        self.name = name
        self.objid_prefix = ""
        self.namespaces = set()
        self.attributes = dict()
        self.relations = dict()
        self.prototypes = list()
        self.objects = set()
        self.tags = set()
        self.scripts = set()

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"