import asyncio

import importlib
from collections import defaultdict
from typing import Union, List


class GameServiceException(Exception):
    pass


def handle_exception(loop, context):
    print("HANDLING EXCEPTION")
    print(loop)
    print(context)


class ShinmaModule:
    """
    Remember: each Module is called in its call order to load, in sequence:

    1. ACL Handlers
    2. Namespaces
    3. Tags
    4. CommandGroups
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

    def __init__(self, engine, *args, **kwargs):
        self.engine = engine
        self.prototypes = dict()
        self.objects = dict()
        self.tags = dict()
        self.namespaces = dict()
        self.acl_classes = dict()
        self.inventory_classes = dict()
        self.task = None

    def init_settings(self, settings):
        pass

    def load_acl(self):
        pass

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

    def patch_basic(self):
        pass

    def patch_prototypes(self):
        pass

    def patch_objects(self):
        pass

    def on_module_event(self, event: str, *args, **kwargs):
        """
        Called by the GameService via GameService.dispatch_module_event(event, *args, **kwargs)

        It does whatever you want it to do.
        """

    async def start(self):
        pass

    def setup(self):
        pass

    def stop(self):
        if self.task:
            self.task.cancel()

    def __repr__(self):
        return f"<{self.__class__}: {self.name} {self.version}>"


class ModuleManager:

    def __init__(self):
        self.settings = None


class ShinmaEngine:

    def __init__(self):
        self.settings = None
        self.modules = dict()
        self.dependency_tiers = defaultdict(list)
        self.module_call_order = list()
        self.event_registry = defaultdict(set)

    def subscribe_event(self, event, callback):
        self.event_registry[event].add(callback)

    def load_modules(self, settings, modules: List[str]):
        # Locate all Modules and instantiate them.
        self.settings = settings
        for mname in modules:
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
            if not module:
                try:
                    module = importlib.import_module(mname)
                except ImportError:
                    raise GameServiceException(f"Could not locate module: {mname}")

            if not (mclass := getattr(module, "Module", None)):
                raise GameServiceException(f"Module {mname} does not provide a Module class.")
            module = mclass(self)
            self.register_module(mname, module)

        # Check module dependencies.
        self.check_requirements()

        for module in self.module_call_order:
            module.init_settings(self.settings)

    def setup(self):
        for module in self.module_call_order:
            module.setup()

    def register_module(self, name, module):
        if (found := self.modules.get(name, None)):
            return (found, f"Module {name} is already registered!")
        self.modules[name] = module
        return (module, False)

    def dependencies_satisfied(self, module) -> bool:
        """
        Check whether a specific plugin's requirements are satisfied.

        Args:
            plugin (str): The name of the plugin being checked.

        Returns:
            true or false
        """
        for k, v in module.requirements.items():
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
                loaded.add(k)
                self.module_call_order.append(v)

        for r in remaining:
            # first we check to make sure that all dependencies are satisfied.
            if not self.dependencies_satisfied(r):
                raise Exception(f"Oops! Module {r} is not satisfied! It desires: {r.requirements}")

        # now confident that all versions check out, arrange the plugins into a suitable load order.
        # no reason to do anything fancy without requirements though.
        if not remaining:
            return

        while True:
            new_remaining = remaining.copy()
            for m in remaining:
                if loaded.issuperset({r for r in m.requirements.keys()}):
                    new_remaining.remove(m)
                    loaded.add(m.name)
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

    def dispatch_module_event(self, event: str, *args, **kwargs):
        """
        Dispatches a hook call to all plugins, according to plugin_call_order.

        Args:
            event (str): The event being triggered.
            *args: Any arguments to pass.
            **kwargs: Any kwargs to pass.
        """
        return [callback(event, *args, **kwargs) for callback in self.event_registry[event]]

    async def start(self):
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(handle_exception)
        start_modules = sorted(self.modules.values(), key=lambda s: getattr(s, 'start_order', 0))
        print(start_modules)
        await asyncio.gather(*[s.start() for s in start_modules])
