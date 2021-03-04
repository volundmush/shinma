from collections import defaultdict
from shinma.utils import import_from_module
from . gamedb import Module as GameDBModule
from . cmdqueue import QueueEntry, CmdQueue
from . commands import connection as LoginCmds, account as AccountCmds, mobile as MobileCmds
from . utils.welcome import render_welcome_screen
from . utils.selectscreen import render_select_screen


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
        engine.subscribe_event("core_load_functions", self.core_functions)
        engine.subscribe_event("core_load_styles", self.core_styles)
        engine.subscribe_event("core_load_options", self.core_options)
        self.cmdqueue = CmdQueue(self)
        self.cmdfamilies = dict()
        self.typeclasses = dict()
        self.mapped_typeclasses = dict()
        self.welcomescreen = None
        self.selectscreen = None
        self.functions = dict()
        self.option_classes = dict()
        self.styles = dict()

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
        from .typeclasses.district import DistrictTypeClass
        typeclasses["CoreDistrict"] = DistrictTypeClass

    def init_settings(self, settings):
        settings.CORE_TYPECLASS_MAP = {
            "connection": "CoreConnection",
            "account": "CoreAccount",
            "playview": "CorePlayView",
            "room": "CoreRoom",
            "exit": "CoreExit",
            "mobile": "CoreMobile",
            "district": "CoreDistrict"
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
        cmdfamilies["connection"]["core_connection"] = LoginCmds.ConnectionCommandMatcher("core_connection")
        cmdfamilies['account']['core_account'] = AccountCmds.AccountCommandMatcher("core_account")
        cmdfamilies['mobile']['core_mobile'] = MobileCmds.MobileCommandMatcher('core_mobile')

    def load_cmdfamilies(self):
        cmdfamilies = defaultdict(dict)
        self.engine.dispatch_module_event("core_load_cmdfamilies", cmdfamilies=cmdfamilies)

        for k, v in cmdfamilies.items():
            for grp in v.values():
                grp.core = self
            self.cmdfamilies[k] = sorted(v.values(), key=lambda g: getattr(g, "priority", 0))

    def load_functions(self):
        functions = dict()
        self.engine.dispatch_module_event("core_load_functions", functions=functions)

        for k, v in functions.items():
            self.functions[k.lower()] = v

    def core_functions(self, event, *args, **kwargs):
        functions = kwargs["functions"]
        from . mush.functions.string import STRING_FUNCTIONS
        for func in STRING_FUNCTIONS:
            functions[func.name] = func

    def core_styles(self, event, *args, **kwargs):
        styles = kwargs["styles"]
        system = styles.get('system', dict())
        system_default = {
            "border_color": ("Headers, footers, table borders, etc.", "Color", "m"),
            "header_star_color": ("* inside Header lines.", "Color", "hm"),
            "header_text_color": ("Text inside Header lines.", "Color", "hw"),
            "header_fill": ("Fill for Header lines.", "Text", "="),
            "subheader_fill": ("Fill for SubHeader lines.", "Text", "="),
            "subheader_text_color": ("Text inside SubHeader lines.", "Color", "hw"),
            "separator_star_color": ("* inside Separator lines.", "Color", "n"),
            "separator_text_color": ("Text inside Separator lines.", "Color", "w"),
            "separator_fill": ("Fill for Separator Lines.", "Text", "-"),
            "footer_star_color": ("* inside Footer lines.", "Color", "n"),
            "footer_text_color": ("Text inside Footer Lines.", "Color", "n"),
            "footer_fill": ("Fill for Footer Lines.", "Text", "="),
            "column_names_color": ("Table column header text.", "Color", "g"),
            "help_category_color": ("Help category names.", "Color", "n"),
            "help_entry_color": ("Help entry names.", "Color", "n"),
            "timezone": ("Timezone for dates. @tz for a list.", "Timezone", "UTC"),
        }
        system.update(system_default)
        styles['system'] = system


    def load_styles(self):
        styles = dict()
        self.engine.dispatch_module_event("core_load_styles", styles=styles)
        self.styles = styles

    def load_options(self):
        options = dict()
        self.engine.dispatch_module_event("core_load_options", options=options)

        self.option_classes = options

    def core_options(self, event, *args, **kwargs):
        options = kwargs["options"]
        from .utils import optionclasses as o
        options['Text'] = o.Text
        options['Email'] = o.Email
        options['Boolean'] = o.Boolean
        options['Color'] = o.Color
        options['Timezone'] = o.Timezone
        options['UnsignedInteger'] = o.UnsignedInteger
        options['SignedInteger'] = o.SignedInteger
        options['PositiveInteger'] = o.PositiveInteger
        options['Duration'] = o.Duration
        options['Datetime'] = o.Datetime
        options['Future'] = o.Future
        options['Lock'] = o.Lock


    def setup(self):
        self.load_typeclasses()
        self.load_cmdfamilies()
        self.load_functions()
        self.load_options()
        self.load_styles()

        self.welcomescreen = self.engine.settings.CORE_WELCOMESCREEN
        if isinstance(self.welcomescreen, str):
            self.welcomescreen = import_from_module(self.welcomescreen)


        self.selectscreen = self.engine.settings.CORE_SELECTSCREEN
        if isinstance(self.selectscreen, str):
            self.selectscreen = import_from_module(self.selectscreen)

        for k, v in self.objects.items():
            v.setup_relations()

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
        entry = QueueEntry(enactor=conn.name, executor=conn.name, caller=conn.name, actions=kwargs["text"], split=False)
        self.cmdqueue.push(entry)

    def net_client_gmcp(self, event, *args, **kwargs):
        pass

    def net_client_disconnected(self, event, *args, **kwargs):
        pass

    def net_client_reconfigured(self, event, *args, **kwargs):
        pass

    async def start(self):
        await self.cmdqueue.start()
