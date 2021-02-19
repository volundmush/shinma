from shinma.game.service import GameModule
from shinma.game.objects import Tag, Namespace, GamePrototypeDef, GameObjectDef
from shinma.game.commands import CommandGroup
from . commands import connection

TAGS = ("account", "connection", "session", "playview")

NAMESPACES = {
  "account": {
    "abbreviation": "acc",
    "priority": 10
  },
  "character": {
    "abbreviation": "char",
    "priority": 30
  },
  "faction": {
    "abbreviation": "fac",
    "priority": 20
  },
  "special": {
    "abbreviation": "sp",
    "priority": 0
  }
}

PROTOTYPES = {
  "CoreSpecial": {
    "namespace": "special",
    "objid_prefix": "special"
  },
  "CoreAccount": {
    "objid_prefix": "account",
    "namespace": "account",
    "tags": ["account"]
  },
  "CoreConnection": {
    "objid_prefix": "connection",
    "tags": ["connection"],
    "commandgroups": ["CoreLogin", "CoreAuthed"]
  },
  "CoreSession": {
    "objid_prefix": "session",
    "tags": ["session"]
  },
  "CorePlayView": {
    "objid_prefix": "playview",
    "tags": ["playview"]
  }
}


OBJECTS = {
  "CoreEveryone": {
    "name": "Everyone",
    "prototypes": "CoreSpecial",
    "acl_class": "CoreAclEveryone"
  },
  "CoreSystem": {
    "name": "System",
    "prototypes": "CoreSpecial",
    "acl_class": "CoreAclSystem"
  },
  "CoreOwner": {
    "name": "Owner",
    "prototypes": "CoreSpecial",
    "acl_class": "CoreAclOwner"
  }
}


class Module(GameModule):
    name = "core"

    def load_tags(self):
        for t in TAGS:
            self.game.register_tag(t, Tag(t))

    def load_namespaces(self):
        for k, v in NAMESPACES.items():
            self.game.register_namespace(k, Namespace(k, v["abbreviation"], v["priority"]))

    def load_commandgroups(self):
        g1 = CommandGroup("CoreLogin")
        g1.add(connection.HelpCommand)
        g1.add(connection.CreateCommand)
        g1.add(connection.ConnectCommand)
        self.game.register_commandgroup(g1.name, g1)

        g2 = CommandGroup("CoreAuthed")
        self.game.register_commandgroup(g2.name, g2)

    def load_prototypes(self):
        for k, v in PROTOTYPES.items():
            proto = GamePrototypeDef(self, k)
            for t in v.get("tags", list()):
                proto.tags.add(t)
            if "namespace" in v:
                proto.namespaces.add(v["namespace"])
            if "objid_prefix" in v:
                proto.objid_prefix = v["objid_prefix"]
            self.game.register_prototype(k, proto)
