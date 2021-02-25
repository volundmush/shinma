from collections import defaultdict
from shinma.utils import import_from_module
from . gamedb import Module as GameDBModule
from . cmdqueue import QueueEntry, CmdQueue
from . commands import connection as LoginCmds
from . utils.welcome import render_welcome_screen
from . utils.selectscreen import render_select_screen

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


class Module(GameDBModule):
    name = "core"
    version = "0.0.1"
    requirements = {
        "net": {"min": "0.0.1"},
    }

    def __init__(self, engine, *args, **kwargs):
        super().__init__(engine, *args, **kwargs)
        engine.subscribe_event("net_client_connected", self.net_client_connected)
        engine.subscribe_event("net_client_command", self.net_client_command)
        engine.subscribe_event("net_client_gmcp", self.net_client_gmcp)
        engine.subscribe_event("net_client_disconnected", self.net_client_disconnected)
        engine.subscribe_event("net_client_reconfigured", self.net_client_reconfigured)
        engine.subscribe_event("core_load_typeclasses", self.core_typeclasses)
        engine.subscribe_event("core_load_cmdfamilies", self.core_cmdfamilies)
        self.cmdqueue = CmdQueue(self)
        self.cmdfamilies = dict()
        self.typeclasses = dict()
        self.mapped_typeclasses = dict()
        self.welcomescreen = None
        self.selectscreen = None

    def core_typeclasses(self, event, *args, **kwargs):
        typeclasses = kwargs["typeclasses"]
        from .typeclasses.connection import ConnectionTypeClass
        typeclasses["CoreConnection"] = ConnectionTypeClass
        from .typeclasses.account import AccountTypeClass
        typeclasses["CoreAccount"] = AccountTypeClass
        from .typeclasses.playview import PlayViewTypeClass
        typeclasses["CorePlayView"] = PlayViewTypeClass
        from .typeclasses.room import RoomTypeClass
        typeclasses["CoreRoom"] = RoomTypeClass
        from .typeclasses.exit import ExitTypeClass
        typeclasses["CoreExit"] = ExitTypeClass
        from . typeclasses.mobile import MobileTypeClass
        typeclasses['CoreMobile'] = MobileTypeClass

    def init_settings(self, settings):
        settings.CORE_TYPECLASS_MAP = {
            "connection": "CoreConnection",
            "account": "CoreAccount",
            "playview": "CorePlayView",
            "room": "CoreRoom",
            "exit": "CoreExit",
            "mobile": "CoreMobile"
        }
        settings.CORE_WELCOMESCREEN = render_welcome_screen
        settings.CORE_SELECTSCREEN = render_select_screen


    def search_tag(self, tagname, text, exact=False):
        tag = self.get_tag(tagname)
        return tag.search(text, exact)

    def load_typeclasses(self):
        typeclasses = dict()
        self.engine.dispatch_module_event("core_load_typeclasses", typeclasses=typeclasses)

        for k, v in typeclasses.items():
            if isinstance(v, str):
                typeclass = import_from_module(v)
                typeclass.core = self
                self.typeclasses[k] = typeclass
            else:
                v.core = self
                self.typeclasses[k] = v

        for k, v in self.engine.settings.CORE_TYPECLASS_MAP.items():
            self.mapped_typeclasses[k] = self.typeclasses[v]

    def core_cmdfamilies(self, event, *args, **kwargs):
        cmdfamilies = kwargs["cmdfamilies"]
        cmdfamilies["connection"]["core_login"] = LoginCmds.LoginCommandMatcher("core_login")
        cmdfamilies["connection"]["core_select"] = LoginCmds.SelectCommandMatcher("core_select")


    def load_cmdfamilies(self):
        cmdfamilies = defaultdict(dict)
        self.engine.dispatch_module_event("core_load_cmdfamilies", cmdfamilies=cmdfamilies)

        for k, v in cmdfamilies.items():
            for grp in v.values():
                grp.core = self
            self.cmdfamilies[k] = sorted(v.values(), key=lambda g: getattr(g, "priority", 0))

    def setup(self):
        self.load_typeclasses()
        self.load_cmdfamilies()

        self.welcomescreen = self.engine.settings.CORE_WELCOMESCREEN
        if isinstance(self.welcomescreen, str):
            self.welcomescreen = import_from_module(self.welcomescreen)


        self.selectscreen = self.engine.settings.CORE_SELECTSCREEN
        if isinstance(self.selectscreen, str):
            self.selectscreen = import_from_module(self.selectscreen)


    def net_client_connected(self, event, *args, **kwargs):
        if not (typeclass := self.mapped_typeclasses.get("connection", None)):
            # Should do some kind of error handling here, and kick the connection that we can't support.
            return
        conn = kwargs['connection']
        created = False
        if not (obj := self.objects.get(conn.name, None)):
            obj, err = typeclass.create(objid=conn.name, name=conn.name)
            if err:
                # Handle error, kick client, blahblah.
                return
            created = True
        obj.connection = conn
        if created:
            self.welcomescreen(obj)

    def net_client_command(self, event, *args, **kwargs):
        conn = kwargs["connection"]
        entry = QueueEntry(enactor=conn.name, executor=conn.name, caller=conn.name, actions=[kwargs["text"]])
        self.cmdqueue.push(entry)

    def net_client_gmcp(self, event, *args, **kwargs):
        pass

    def net_client_disconnected(self, event, *args, **kwargs):
        pass

    def net_client_reconfigured(self, event, *args, **kwargs):
        pass

    async def start(self):
        await self.cmdqueue.start()