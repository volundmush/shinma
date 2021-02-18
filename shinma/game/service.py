from collections import defaultdict
from shinma.core import BaseService
from typing import Union, List, Dict
import random
import string
import pathlib
import os
import importlib


class GameServiceException(Exception):
    pass


class GameModule:
    """
    Remember: each Module is called in its call order to load, in sequence:

    1. ACL Handlers
    2. Namespaces
    3. Tags
    4. Scripts
    5. Prototypes
    6. Objects

    This means that first, Module 1 loads ACL, then Module 2 loads ACL... and when they're all done,
    Module 1 starts loading Namespaces.

    Prototypes depend on everything before, and Objects depend on Prototypes.
    """
    name = None
    version = "0.0.1"
    requirements = dict()

    def __init__(self, game, *args, **kwargs):
        self.game = game
        self.prototypes = dict()
        self.objects = dict()
        self.tags = dict()
        self.namespaces = dict()
        self.acl_classes = dict()
        self.inventory_classes = dict()

    def config(self):
        pass

    def load_acl(self):
        """
        This is called to
        :return:
        """

    def load_tags(self):
        pass

    def load_prototypes(self):
        pass

    def load_namespaces(self):
        pass

    def load_scripts(self):
        pass

    def load_objects(self):
        pass

    def op_module_event(self, event: str, *args, **kwargs):
        """
        Called by the GameService via GameService.dispatch_module_event(event, *args, **kwargs)

        It does whatever you want it to do.
        """


class GameService(BaseService):

    def __init__(self):
        self.objects = dict()
        self.modules = dict()
        self.dependency_tiers = defaultdict(list)
        self.module_call_order = list()
        self.tags = dict()
        self.prototypes = dict()
        self.namespaces = dict()
        self.inventory_classes = dict()
        self.acl_classes = dict()
        self.scripts = dict()

    def setup(self):
        # Locate all Modules and instantiate them.
        for mname in self.app.settings.MODULES:
            module = None
            try:
                module = importlib.import_module(f"game_data.modules.{mname}")
            except ImportError:
                pass
            if not module:
                try:
                    module = importlib.import_module(f"shinma.modules.{mname}")
                except ImportError:
                    raise GameServiceException(f"Could not locate module: {mname}")
            if not (mclass := getattr(module, "Module", None)):
                raise GameServiceException(f"Module {mname} does not provide a Module class.")
            module = mclass(self)
            self.register_module(mname, module)

        # Check module dependencies.
        self.check_requirements()

        # Start loading assets...
        for m in self.module_call_order:
            m.load_acl()
            m.load_namespaces()
            m.load_tags()
            m.load_scripts()
            m.load_prototypes()
            m.load_objects()

        print(self.prototypes)


    def register_module(self, name, module):
        self.modules[name] = module

    def register_tag(self, name, tag):
        self.tags[name] = tag

    def register_namespace(self, name, namespace):
        self.namespaces[name] = namespace

    def register_acl(self, name, handler):
        pass

    def register_prototype(self, name, proto):
        self.prototypes[name] = proto

    def register_script(self, name, script):
        pass

    def register_object(self, name, obj):
        pass

    def find_prototype(self, pname: str):
        if (proto := self.prototypes.get(pname, None)):
            return proto
        raise GameServiceException(f"Prototype {pname} not found.")

    def find_object(self, objid: str):
        if (obj := self.objects.get(objid, None)):
            return obj
        raise GameServiceException(f"Object {objid} not found.")

    def spawn_object(self, prototypes: Union[str, List[str]], name=None, objid: str = None, module=None):
        if isinstance(prototypes, str):
            prototypes = [prototypes]
        if not prototypes:
            raise GameServiceException("No prototypes listed to spawn.")
        prototypes = [self.find_prototype(pname) for pname in prototypes]
        if objid is None:
            prefix = None
            for proto in prototypes:
                prefix = proto.objid_prefix
            if prefix is None:
                raise GameServiceException("No objid provided for dynamic spawn.")
            objid = self.generate_id(prefix)
        if name is None:
            name = objid
        out = self.app.classes["game"]["object"](module, name, objid, prototypes)
        # out.setup() might raise a GameServiceException, but if it doesn't, setup_reverse() is not allowed to.
        out.setup(self)

        self.objects[objid] = out
        out.setup_reverse()
        return out

    def generate_id(self, prefix=None):
        if prefix is None:
            prefix = ''
        else:
            prefix += "_"

        attempt = f"{prefix}{''.join(random.choices(string.ascii_letters + string.digits, k=20))}"
        while attempt in self.objects:
            attempt = f"{prefix}{''.join(random.choices(string.ascii_letters + string.digits, k=20))}"
        return attempt

    def dispatch_module_event(self, event: str, *args, **kwargs):
        """
        Dispatches a hook call to all plugins, according to plugin_call_order.

        Args:
            event (str): The event being triggered.
            *args: Any arguments to pass.
            **kwargs: Any kwargs to pass.
        """
        return [m.on_module_event(event, *args, **kwargs) for m in self.module_call_order]

    def dispatch_script_event(self, event: str, *args, **kwargs):
        return [v.on_game_event(event, *args, **kwargs) for k, v in self.scripts.items()]

    def dependencies_satisfied(self, name: str) -> bool:
        """
        Check whether a specific plugin's requirements are satisfied.

        Args:
            plugin (str): The name of the plugin being checked.

        Returns:
            true or false
        """
        for k, v in self.modules[name].requirements:
            if k not in self.modules:
                return False
            found_ver = self.modules[k].version
            if isinstance(v, str):
                return found_ver == v
            elif isinstance(v, dict):
                if "eq" in v and (found_ver != v["eq"]):
                    return False
                if "min" in v and (found_ver < v["min"]):
                    return False
                if "max" in v and (found_ver > v["max"]):
                    return False
            else:
                return True
        return True

    def check_requirements(self):
        """
        Checks dependencies and assembles sorted plugin information for further calls.
        """
        # first, separate plugins based on those with and without dependeices.
        remaining = set()
        loaded = set()

        for k, v in self.modules.items():
            if v.requirements:
                remaining.add(v)
            else:
                loaded.add(v)
                self.module_call_order.append(v)

        for r in remaining:
            # first we check to make sure that all dependencies are satisfied.
            if not self.dependencies_satisfied(r):
                raise Exception(f"Oops! Module {r} is not satisfied")

        # now confident that all versions check out, arrange the plugins into a suitable load order.
        # no reason to do anything fancy without requirements though.
        if not remaining:
            return

        while True:
            new_remaining = remaining.copy()
            for m in remaining:
                if loaded.issuperset({r.name for r in m.requirements}):
                    new_remaining.remove(m)
                    loaded.add(m)
                    self.module_call_order.append(m)
            if len(new_remaining) < len(remaining):
                # this is good.. we made progress!
                remaining = new_remaining
                if not remaining:
                    # hooray! No more plugins to process
                    break
            else:
                # this is bad. we are not making progress.
                raise Exception("dependency load order is not progressing!")
