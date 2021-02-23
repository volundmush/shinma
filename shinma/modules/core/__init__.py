from shinma.core import ShinmaModule
from shinma.utils import import_from_module
from . cmdqueue import QueueEntry, CmdQueue
from . commands.base import CommandGroup
from . commands import connection as LoginCmds


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


class Module(ShinmaModule):
    name = "core"
    version = "0.0.1"
    requirements = {
        "net": {"min": "0.0.1"},
        "gamedb": {"min": "0.0.1"}
    }

    def __init__(self, engine, *args, **kwargs):
        super().__init__(engine, *args, **kwargs)
        engine.subscribe_event("net_client_connected", self.net_client_connected)
        engine.subscribe_event("net_client_command", self.net_client_command)
        engine.subscribe_event("net_client_gmcp", self.net_client_gmcp)
        engine.subscribe_event("net_client_disconnected", self.net_client_disconnected)
        engine.subscribe_event("net_client_reconfigured", self.net_client_reconfigured)
        self.cmdqueue = CmdQueue(self)
        self.cmdgroups = dict()
        self.typeclasses = dict()
        self.objects = dict()
        self.objmanager = None

    def init_settings(self, settings):
        settings.CORE_TYPECLASSES = dict()
        from . typeclasses.connection import ConnectionTypeClass
        settings.CORE_TYPECLASSES["connection"] = ConnectionTypeClass
        from . typeclasses.account import AccountTypeClass
        settings.CORE_TYPECLASSES["account"] = AccountTypeClass
        from . typeclasses.playview import PlayViewTypeClass
        settings.CORE_TYPECLASSES["playview"] = PlayViewTypeClass
        from . typeclasses.room import RoomTypeClass
        settings.CORE_TYPECLASSES["room"] = RoomTypeClass
        from . typeclasses.exit import ExitTypeClass
        settings.CORE_TYPECLASSES["exit"] = ExitTypeClass
        from . typeclasses.welcome import WelcomeScreenTypeClass
        settings.CORE_TYPECLASSES["welcomescreen"] = WelcomeScreenTypeClass

    def setup(self):
        for k, v in self.engine.settings.CORE_TYPECLASSES.items():
            if isinstance(v, str):
                self.typeclasses[k] = import_from_module(v)
            else:
                self.typeclasses[k] = v
        for k, v in self.typeclasses.items():
            v.core = self

        g1 = CommandGroup("connection")
        g1.add(LoginCmds.CreateCommand)
        g1.add(LoginCmds.ConnectCommand)
        g1.add(LoginCmds.HelpCommand)
        g1.add(LoginCmds.CharCreateCommand)
        g1.add(LoginCmds.CharSelectCommand)
        self.cmdgroups[g1.name] = g1

        self.objmanager = self.engine.modules["gamedb"]
        self.objmanager.process_preload()


    def net_client_connected(self, event, *args, **kwargs):
        if not (typeclass := self.typeclasses.get("connection", None)):
            # Should do some kind of error handling here, and kick the connection that we can't support.
            return
        conn = kwargs['connection']
        if not (obj := self.ojects.get(conn.name, None)):
            obj, err = typeclass.create(objid=conn.name, name=conn.name)
            if err:
                # Handle error, kick client, blahblah.
                return
        obj.connection = conn

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