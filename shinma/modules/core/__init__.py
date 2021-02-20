from shinma.engine import GameModule
from shinma.objects import Tag, Namespace, GameObjectDef
from shinma.prototypes import GamePrototypeDef

from . scripts import CoreConnectionScript
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
    "cmdgroups": {"login": "CoreLogin", "auth": "CoreAuthed"},
    "scripts": ["CoreConnectionScript"]
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
    version = "0.0.1"
    requirements = {
        "net": {"min": "0.0.1"}
    }

    def load_tags(self):
        for t in TAGS:
            self.game.register_tag(t, Tag(t))

    def load_namespaces(self):
        for k, v in NAMESPACES.items():
            self.game.register_namespace(k, Namespace(k, v["abbreviation"], v["priority"]))

    def load_prototypes(self):
        for k, v in PROTOTYPES.items():
            proto = GamePrototypeDef(self, k)
            for t in v.get("tags", list()):
                proto.tags.add(t)
            if "namespace" in v:
                proto.namespaces.add(v["namespace"])
            if "objid_prefix" in v:
                proto.objid_prefix = v["objid_prefix"]
            if "cmdgroups" in v:
                proto.cmdgroups.update(v["cmdgroups"])
            if "scripts" in v:
                proto.scripts = v["scripts"]
            self.game.register_prototype(k, proto)

    def load_scripts(self):
        self.game.register_script("CoreConnectionScript", CoreConnectionScript)
