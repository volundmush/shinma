from collections import defaultdict
from shinma.core import BaseService
from . objects import GameObject, GamePrototype, Attribute, AttributeHolder, AttributeCategory


class GameService:

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

    def setup(self):
        pass

    def add_module(self, name, module):
        self.modules[name] = module

    def dispatch(self, hook: str, *args, **kwargs):
        """
        Dispatches a hook call to all plugins, according to plugin_call_order.

        Args:
            hook (str): The hook to call.
            *args: Any arguments to pass.
            **kwargs: Any kwargs to pass.
        """
        for m in self.module_call_order:
            if (c := getattr(m, hook, None)):
                c(*args, **kwargs)

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

        for m in self.modules:
            if m.requirements:
                remaining.add(m)
            else:
                loaded.add(m)
                self.module_call_order.append(m)

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
