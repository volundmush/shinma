import os, pathlib, sys, time, re, weakref
from collections import defaultdict
from shinma.utils import import_from_module, partial_match
from . gamedb import Module as GameDBModule
from . cmdqueue import QueueEntry, CmdQueue
from . commands import connection as LoginCmds, account as AccountCmds, mobile as MobileCmds
from . utils.welcome import render_welcome_screen
from . utils.selectscreen import render_select_screen
import ujson

REG_BASIC_NAME = re.compile(r"(?s)^(\w|\.|-| |')+$")
REG_EMAIL_NAME = re.compile(r"(?s)^(\w|\.|-| |'|@)+$")


class Identity:

    def __init__(self, core, name, prefix, reg=None, priority=0):
        self.core = core
        self.name = name
        self.prefix = prefix
        self.priority = priority
        if reg is None:
            self.reg = REG_BASIC_NAME
        else:
            self.reg = reg
        self.objects = weakref.WeakSet()
        self.aliases = weakref.WeakValueDictionary()

    def search(self, name, aliases=True, exact=False):
        name_lower = name.lower()
        if aliases:
            for k, v in self.aliases.items():
                if name_lower == k.lower():
                    return v, None
        if exact:
            for obj in self.objects:
                if name_lower == obj.name.lower():
                    return obj, None
        else:
            if (found := partial_match(name, self.objects, key=lambda x: x.name)):
                return found, None
        return None, f"Sorry, nothing matches: {name}"

    def valid(self, name: str):
        return self.reg.match(name)

    def available(self, name: str, exclude=None):
        for obj in self.objects:
            if obj == exclude:
                continue
            if obj.name.lower() == name.lower():
                return False
        for k, v in self.aliases.items():
            if v == exclude:
                continue
            if k.lower() == name.lower():
                return False
        return True


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
        engine.subscribe_event('core_load_identities', self.core_identities)
        engine.subscribe_event('core_object_setup_relations', self.core_object_setup_relations)
        self.cmdqueue = CmdQueue(self)
        self.cmdfamilies = dict()
        self.typeclasses = dict()
        self.mapped_typeclasses = dict()
        self.welcomescreen = None
        self.selectscreen = None
        self.functions = dict()
        self.option_classes = dict()
        self.styles = dict()
        self.identities = dict()
        self.identity_prefix = dict()

    def dump(self):
        with open('gamedb.json', 'w') as f:
            data = {k: v.dump() for k, v in self.objects.items()}
            ujson.dump(data, f)

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
        settings.CORE_DEFAULT_SLEVEL = 0

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
        cmdfamilies['mobile']['core_mobile_exit'] = MobileCmds.MobileExitMatcher('core_mobile_exit')


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

    def load_asset_objects(self):
        pass

    def load_dynamic_objects(self):
        if os.path.exists('gamedb.json'):
            print(f"Loading data...")
            start = time.time()
            with open('gamedb.json', 'r') as f:
                data = ujson.load(f)

            for k, v in data.items():
                if (typeclass := self.typeclasses.get(v.pop('typeclass', None), None)):
                    obj = typeclass(objid=v.pop('objid'), name=v.pop('name'), initial_data=v)
                    self.objects[k] = obj
                    obj.load_initial()
            end = time.time()
            dur = (end - start) * 1000
            print(f"Loading gamedb took: {dur:.4f} ms")


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

    def core_object_setup_relations(self, event, *args, **kwargs):
        obj = kwargs['object']
        if obj.typeclass_family == 'exit':
            if (dest := self.objects.get(obj.attributes.get('core', 'destination'),None)):
                dest.entrances.add(obj)
                obj.relations['destination'] = obj
            if (loc := self.objects.get(obj.attributes.get('core', 'location'), None)):
                loc.exits.add(obj)
                obj.relations['location'] = obj
            if (dist := self.objects.get(obj.attributes.get('core', 'district'), None)):
                dist.exits.add(obj)
                obj.relations['district'] = obj

        if obj.typeclass_family == 'room':
            if (dist := self.objects.get(obj.attributes.get('core', 'district'), None)):
                dist.rooms.add(obj)
                obj.relations['district'] = obj

        if obj.typeclass_family == 'mobile':
            if (acc := self.objects.get(obj.attributes.get('core', 'account'), None)):
                acc.characters.add(obj)
                obj.relations['account'] = acc
            if (pview := self.objects.get(obj.attributes.get('core', 'playview'), None)):
                pview.characters.add(obj)
                obj.relations['playview'] = pview

        if obj.typeclass_family == 'connection':
            if (acc := self.objects.get(obj.attributes.get('core', 'account'), None)):
                acc.connections.add(obj)
                obj.relations['account'] = acc
            if (pview := self.objects.get(obj.attributes.get('core', 'playview'), None)):
                pview.connections.add(obj)
                obj.relations['playview'] = pview


    def core_identities(self, event, *args, **kwargs):
        identities = kwargs['identities']
        identities['account'] = {
            'prefix': 'A',
            'description': 'For Accounts',
            'priority': 10,
            'reg': REG_EMAIL_NAME
        }
        identities['character'] = {
            'prefix': 'C',
            'description': 'For Player Characters',
            'priority': 20
        }
        identities['special'] = {
            'prefix': 'S',
            'description': 'For special entities.',
            'priority': -9999999
        }
        identities['faction'] = {
            'prefix': 'F',
            'description': 'For Factions',
            'priority': 0
        }
        identities['theme'] = {
            'prefix': 'T',
            'description': 'For themes/settings.',
            'priority': 5
        }

    def load_identities(self):
        identities = dict()
        self.engine.dispatch_module_event('core_load_identities', identities=identities)

        for k, v in identities.items():
            iden = Identity(self, k, prefix=v['prefix'], priority=v.get('priority', 0), reg=v.get('reg', None))
            self.identities[k] = iden
            self.identity_prefix[iden.prefix] = iden

    def setup(self):
        self.load_typeclasses()
        self.load_cmdfamilies()
        self.load_functions()
        self.load_options()
        self.load_styles()
        self.load_identities()
        self.load_asset_objects()
        self.load_dynamic_objects()

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
        if (conn := self.objects.get(kwargs["connection"].name, None)):
            text = kwargs['text']
            if text == 'IDLE':
                return
            t = time.time()
            conn.attributes.set('core', 'last_cmd', t)
            if (acc := conn.relations.get('account', None)):
                acc.attributes.set('core', 'last_cmd', t)
            if (play := conn.relations.get('playview', None)):
                play.attributes.set('core', 'last_cmd', t)
            entry = QueueEntry(enactor=conn.name, executor=conn.name, caller=conn.name, actions=kwargs["text"], split=False)
            self.cmdqueue.push(entry)

    def net_client_gmcp(self, event, *args, **kwargs):
        pass

    def net_client_disconnected(self, event, *args, **kwargs):
        if (conn := self.objects.get(kwargs["connection"].name, None)):
            conn.close_connection(reason="lost connection")

    def delete(self, obj):
        self.objects.pop(obj.objid, None)
        obj.delete()

    def net_client_reconfigured(self, event, *args, **kwargs):
        pass

    async def start(self):
        await self.cmdqueue.start()

    def search_identity(self, text, aliases=True, exact=False):
        if ':' not in text:
            return None, "Identity search syntax - Prefix:Name"
        pre, name = text.split(':')
        pre = pre.strip().upper()
        name = name.strip()
        if not (pre and name):
            return None, "Identity search syntax - Prefix:Name"
        if not (pre_found := partial_match(pre, list(self.identity_prefix.keys()))):
            return None, f"No prefix matching {pre}"
        return self.identity_prefix[pre_found].search(name, aliases=aliases, exact=exact)
