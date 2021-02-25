import random
import string
from typing import Any
from shinma.utils import to_str
from .. gamedb.objects import GameObject
from .. gamedb.exception import GameObjectException


class ScriptHandler:

    def __init__(self, obj):
        self.obj = obj
        self.scripts = dict()

    def dispatch_event(self, event: str, *args, **kwargs):
        return [v.on_object_event(self.obj, event, *args, **kwargs) for k, v in self.scripts.items()]

    def setup(self):
        final = set()
        for proto in self.obj.prototypes:
            final = final.union(proto.scripts)
        self.scripts = {s.name: s for s in final}
        for s in final:
            s.objects.add(self.obj)


class Msg:
    __slots__ = ["source", "data", "relay_chain"]

    def __init__(self, source, data=None):
        self.source = source
        if data is None:
            data = dict()
        self.data = data
        self.relay_chain = list()

    def set(self, text=None, **kwargs):
        if text is not None:
            if not (isinstance(text, str) or isinstance(text, tuple)):
                # sanitize text before sending across the wire
                try:
                    text = to_str(text)
                except Exception:
                    text = repr(text)
            kwargs["text"] = text
        self.data = kwargs

    @classmethod
    def create(cls, source, text=None, **kwargs):
        msg = cls(source)
        msg.set(text=text, **kwargs)
        return msg

    def relay(self, obj):
        c = self.__class__(self.source, **self.data)
        c.relay_chain = list(self.relay_chain)
        c.relay_chain.append(obj)
        return c


class BaseTypeClass(GameObject):
    typeclass_name = None
    prefix = "shinmaobject"
    class_initial_data = None
    command_families = set()

    @classmethod
    def generate_id(cls, prefix=None):
        if prefix is None:
            prefix = cls.prefix

        if prefix:
            prefix = f"{prefix}_"

        attempt = f"{prefix}{''.join(random.choices(string.ascii_letters + string.digits, k=20))}"
        while attempt in cls.core.objects:
            attempt = f"{prefix}{''.join(random.choices(string.ascii_letters + string.digits, k=20))}"
        return attempt

    @classmethod
    def create(cls, name: str=None, objid=None, prefix=None, initial_data=None):
        if objid is None:
            objid = cls.generate_id(prefix)
        if name is None:
            name = objid
        if initial_data is None:
            initial_data = cls.class_initial_data
        try:
            obj = cls(objid, name, initial_data=initial_data)
            cls.core.objects[objid] = obj
            obj.load_initial()
            obj.load_relations()
            obj.attributes.set("_core", "typeclass", cls.typeclass_name)
        except GameObjectException as e:
            cls.core.objects.pop(objid, None)
            return None, str(e)
        return obj, None

    def __repr__(self):
        return f"<{self.__class__.__name__} TypeClass: {self.objid} - {self.name}>"

    def __str__(self):
        return self.name

    def listeners(self):
        return []

    def msg(self, text=None, **kwargs):
        self.send(Msg.create(self, text=text, **kwargs))

    def send(self, message: Msg):
        self.receive_msg(message)
        for listener in self.listeners():
            if listener not in message.relay_chain:
                listener.receive_relayed_msg(message.relay(self))

    def receive_msg(self, message: Msg):
        pass

    def receive_relayed_msg(self, message: Msg):
        pass

    def location(self):
        if (loc := self.reverse.get("room_contents", None)):
            return list(loc)[0]
        return None

    def render_appearance_external(self, viewer=None):
        pass

    def render_appearance_internal(self, viewer=None):
        pass

    def get_cmd_matchers(self):
        results = set()
        for fam in self.command_families:
            results = results.union(self.core.cmdfamilies.get(fam, []))
        results = [matcher for matcher in results if matcher.access(self)]
        return sorted(results, key=lambda g: getattr(g, "priority", 0))

    def get_next_cmd_object(self, obj_chain):
        return None

    def find_cmd(self, text: str, obj_chain=None):
        if obj_chain is None:
            obj_chain = dict()
        for g in self.get_cmd_matchers():
            if (cmd := g.match(self, text, obj_chain)):
                return cmd
        if (next_obj := self.get_next_cmd_object(obj_chain)):
            obj_chain[self.typeclass_name] = self
            next_obj.find_cmd(text, obj_chain)

