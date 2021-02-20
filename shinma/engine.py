import asyncio
import random
import string
import importlib
from collections import defaultdict
from typing import Union, List

from shinma.objects import GameObject
from shinma.prototypes import GamePrototype


class GameServiceException(Exception):
    pass


def handle_exception(loop, context):
    print("HANDLING EXCEPTION")
    print(loop)
    print(context)


class GameModule:
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

    def __init__(self, game, *args, **kwargs):
        self.game = game
        self.prototypes = dict()
        self.objects = dict()
        self.tags = dict()
        self.namespaces = dict()
        self.acl_classes = dict()
        self.inventory_classes = dict()
        self.task = None

    def config(self):
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

    def op_module_event(self, event: str, *args, **kwargs):
        """
        Called by the GameService via GameService.dispatch_module_event(event, *args, **kwargs)

        It does whatever you want it to do.
        """

    async def start(self):
        pass

    def stop(self):
        if self.task:
            self.task.cancel()

    def __repr__(self):
        return f"<{self.__class__}: {self.name} {self.version}>"

class ShinmaEngine:
    object_class = GameObject
    prototype_class = GamePrototype

    def __init__(self, settings):
        self.settings = settings
        self.objects = dict()
        self.object_defs = dict()
        self.modules = dict()
        self.dependency_tiers = defaultdict(list)
        self.module_call_order = list()
        self.tags = dict()
        self.prototypes = dict()
        self.prototype_defs = dict()
        self.namespaces = dict()
        self.inventory_classes = dict()
        self.acl_classes = dict()
        self.scripts = dict()
        self.script_classes = dict()
        self.pending_cmds = set()

    def setup(self):
        # Locate all Modules and instantiate them.
        for mname in self.settings.MODULES:
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

        # Start loading assets...
        for m in self.module_call_order:
            m.load_acl()
        for m in self.module_call_order:
            m.load_namespaces()
        for m in self.module_call_order:
            m.load_tags()
        for m in self.module_call_order:
            m.load_scripts()

        # Give modules a chance to alter previous data.
        # Careful with this.
        for m in self.module_call_order:
            m.patch_basic()

        self.load_scripts()

        for m in self.module_call_order:
            m.load_prototypes()

        # Give modules a chance to modify prototype data.
        for m in self.module_call_order:
            m.patch_prototypes()

        # Now that all prototype data has been assembled, process it
        # from GamePrototypeDefs into GamePrototypes, and dispose of
        # the defs.
        self.process_prototypes_initial()

        for m in self.module_call_order:
            m.load_objects()

        # Do a final load of object data from the save game data.
        self.load_objects()

        for m in self.module_call_order:
            m.patch_objects()

        # Now that all object data has been assembled, process it
        # from GameObjectDefs into GameObjects, and dispose of
        # the defs.
        self.process_objects_initial()

        self.process_prototypes_final()
        self.process_objects_final()

    def register_module(self, name, module):
        if (found := self.modules.get(name, None)):
            return (found, f"Module {name} is already registered!")
        self.modules[name] = module
        return (module, False)

    def register_tag(self, name, tag):
        if (found := self.tags.get(name, None)):
            return (found, f"Tag {name} is already registered!")
        self.tags[name] = tag
        return (tag, False)

    def register_namespace(self, name, namespace):
        if (found := self.namespaces.get(name, None)):
            return (found, f"Namespace {name} is already registered!")
        self.namespaces[name] = namespace
        return (namespace, False)

    def register_acl(self, name, handler):
        if (found := self.acl_classes.get(name, None)):
            return (found, f"ACLHandler {name} is already registered!")
        self.acl_classes[name] = handler
        return (handler, False)

    def register_prototype(self, name, proto):
        if (found := self.prototype_defs.get(name, None)):
            return (found, f"PrototypeDef {name} is already registered!")
        self.prototype_defs[name] = proto
        return (proto, False)

    def register_inventory(self, name, inv):
        if (found := self.inventory_classes.get(name, None)):
            return (found, f"InventoryHandler {name} is already registered!")
        self.inventory_classes[name] = inv
        return (inv, False)

    def register_script(self, name, script):
        if (found := self.script_classes.get(name, None)):
            return (found, f"InventoryHandler {name} is already registered!")
        self.script_classes[name] = script
        return (script, False)

    def register_object(self, name, obj):
        if (found := self.object_defs.get(name, None)):
            return (found, f"ObjectDef {name} is already registered!")
        self.object_defs[name] = obj
        return (obj, False)

    def process_prototypes_initial(self):
        final_list = dict()
        for k, v in self.prototype_defs.items():
            result, error = self.process_prototype_initial(k, v)
            if error:
                return (None, error)
            final_list[result.name] = result
        self.prototypes.update(final_list)

    def find_prototype(self, pname: str):
        if (proto := self.prototypes.get(pname, None)):
            return (proto, None)
        return (None, f"Prototype {pname} not found.")

    def find_object(self, objid: str):
        if (obj := self.objects.get(objid, None)):
            return (obj, None)
        return (None, f"Object {objid} not found.")

    def find_namespace(self, name: str):
        if (found := self.namespaces.get(name, None)):
            return (found, None)
        return (None, f"Namespace {name} not found.")

    def find_tag(self, name: str):
        if (found := self.tags.get(name, None)):
            return (found, None)
        return (None, f"Tag {name} not found.")

    def find_inventory(self, name: str):
        if (found := self.inventory_classes.get(name, None)):
            return (found, None)
        return (None, f"InventoryHandler {name} not found.")

    def find_script(self, name: str):
        if (found := self.scripts.get(name, None)):
            return (found, None)
        return (None, f"Script {name} not found.")

    def load_scripts(self):
        for k, v in self.script_classes.items():
            self.scripts[k] = v(self, k)

    def process_prototype_initial(self, name, pdef):
        proto = self.prototype_class(pdef.module, pdef.name)
        proto.objid_prefix = pdef.objid_prefix
        if pdef.namespaces:
            for pname in pdef.namespaces:
                namespace, error = self.find_namespace(pname)
                if error:
                    return (None, f"Error while processing prototype {name}: {error}")
                proto.namespaces.add(namespace)

        if pdef.tags:
            for ptag in pdef.tags:
                tag, error = self.find_tag(ptag)
                if error:
                    return (None, f"Error while processing prototype {name}: {error}")
                proto.tags.add(tag)

        if pdef.inventories:
            for pinv in pdef.inventories:
                inv, error = self.find_inventory(pinv)
                if error:
                    return (None, f"Error while processing prototype {name}: {error}")
                proto.inventories[pinv] = inv

        if pdef.scripts:
            for pscr in pdef.scripts:
                scr, error = self.find_script(pscr)
                if error:
                    return (None, f"Error while processing prototype {name}: {error}")
                proto.scripts.add(scr)

        if isinstance(pdef.attributes, dict):
            proto.attributes = pdef.attributes

        return (proto, False)

    def process_prototypes_final(self):
        for name, proto in self.prototypes.items():
            for tag in proto.tags:
                tag.prototypes.add(proto)
            for namespace in proto.namespaces:
                namespace.prototypes.add(proto)
            for inventory in proto.inventories.values():
                inventory.prototypes.add(proto)
            for k, v in proto.saved_locations.items():
                if v["objid"] not in self.objects:
                    return (None,
                            f"Error while final processing prototype {name}: {v['objid']} not found for saved location {k}")
            for k, v in proto.acl.items():
                if v["objid"] not in self.objects:
                    return (None,
                            f"Error while final processing prototype {name}: {v['objid']} not found for saved location {k}")
            for script in proto.scripts:
                script.prototypes.add(proto)
            for k, v in proto.relations.items():
                if k not in self.objects:
                    return (None,
                            f"Error while final processing prototype {name}: {v['objid']} not found for relational attributes {k}")
        return None, False

    def load_objects(self):
        pass

    def process_objects_initial(self):
        for k, v in self.object_defs.items():
            self.process_object_initial(k, v)

    def process_object_initial(self, objid, odef):
        pass

    def process_objects_final(self):
        pass

    def spawn_object(self, prototypes: Union[str, List[str]], name=None, objid: str = None, module=None):
        if isinstance(prototypes, str):
            prototypes = [prototypes]
        if not prototypes:
            return (None, "Object Spawn error: No prototypes listed for spawn.")
        final_prototypes = list()
        for pname in prototypes:
            proto, error = self.find_prototype(pname)
            if error:
                return (None, f"Object Spawn error: {error}")
            final_prototypes.append(proto)
        if objid is None:
            prefix = None
            for proto in final_prototypes:
                prefix = proto.objid_prefix
            if prefix is None:
                return (None,
                        f"Object Spawn error: No objid provided, no objid_prefix available in prototypes for dynamic IDs.")
            objid = self.generate_id(prefix)
        if name is None:
            name = objid
        obj = self.object_class(self, module, name, objid, final_prototypes)
        result, error = obj.setup()
        if error:
            return None, f"Object Spawn error: {error}"
        self.objects[objid] = obj
        obj.setup_reverse()
        return obj, None

    def generate_id(self, prefix=None):
        if prefix is None:
            prefix = ''
        else:
            prefix += "_"

        attempt = f"{prefix}{''.join(random.choices(string.ascii_letters + string.digits, k=20))}"
        while attempt in self.objects:
            attempt = f"{prefix}{''.join(random.choices(string.ascii_letters + string.digits, k=20))}"
        return attempt

    def search_namespace(self, nspace, name, exact=False):
        namespace, error = self.find_namespace(nspace)
        if error:
            return None, error
        return namespace.search(name, exact=exact)

    def dispatch_module_event(self, event: str, *args, **kwargs):
        """
        Dispatches a hook call to all plugins, according to plugin_call_order.

        Args:
            event (str): The event being triggered.
            *args: Any arguments to pass.
            **kwargs: Any kwargs to pass.
        """
        return [m.on_module_event(event, *args, **kwargs) for m in self.module_call_order]

    def dispatch_event(self, event: str, *args, **kwargs):
        return [v.on_game_event(event, *args, **kwargs) for k, v in self.scripts.items()]

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

    async def start(self):
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(handle_exception)
        self.setup()
        start_modules = sorted(self.modules.values(), key=lambda s: getattr(s, 'start_order', 0))
        start_scripts = sorted(self.scripts.values(), key=lambda s: getattr(s, 'start_order', 0))
        combined = [s.start() for s in start_modules] + [s.start() for s in start_scripts]
        await asyncio.gather(*combined)
