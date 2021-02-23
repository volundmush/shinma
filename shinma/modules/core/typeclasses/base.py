import random
import string
from shinma.utils import to_str
from typing import Any


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


class BaseTypeClass:
    typeclass_name = None
    core = None
    prefix = "shinmaobject"
    initial_data = None

    def __init__(self, obj):
        self.obj = obj

    @classmethod
    def generate_id(cls, prefix=None):
        if prefix is None:
            prefix = cls.prefix

        if prefix:
            prefix = f"{prefix}_"

        attempt = f"{prefix}{''.join(random.choices(string.ascii_letters + string.digits, k=20))}"
        while attempt in cls.core.objmanager.objects:
            attempt = f"{prefix}{''.join(random.choices(string.ascii_letters + string.digits, k=20))}"
        return attempt

    @classmethod
    def create(cls, name: str=None, objid=None, prefix=None, initial_data=None):
        if objid is None:
            objid = cls.generate_id(prefix)
        if name is None:
            name = objid
        if initial_data is None:
            initial_data = cls.initial_data
        try:
            obj = cls.core.objmanager.create_object(objid, name, initial_data=initial_data)
            wrap_obj = cls(obj)
            cls.core.objects[objid] = wrap_obj
        except cls.core.objmanager.exception_class as e:
            return None, str(e)
        return wrap_obj, None

    def __repr__(self):
        return f"<{self.__class__.__name__} TypeClass: {self.objid} - {self.name}>"

    @property
    def name(self):
        return self.obj.name

    @property
    def objid(self):
        return self.obj.objid

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
        if (loc := self.obj.locations.get("contents", None)):
            return self.core.objects.get(loc[0], None)
        return None

    def render_appearance_external(self, viewer=None):
        pass

    def render_appearance_internal(self, viewer=None):
        pass

    def get_cmd_groups(self):
        return []

    def get_next_cmd_object(self, obj_chain):
        return None

    def find_cmd(self, text: str, obj_chain=None):
        if obj_chain is None:
            obj_chain = dict()
        for g in self.get_cmd_groups():
            if (cmd := g.match(self, text, obj_chain)):
                return cmd
        if (next_obj := self.get_next_cmd_object(obj_chain)):
            obj_chain[self.typeclass_name] = self
            next_obj.find_cmd(text, obj_chain)


    def get_attribute(self, category: str, name: str, default: Any = None):
        return self.obj.attributes.get(category, name)

    def _get_obj(self, category, attrname, field):
        if (out := getattr(self, field, None)):
            return out
        if not (attr := self.get_attribute(category, attrname)):
            return None
        if (obj := self.core.get_obj(attr)):
            setattr(self, field, obj)
            return obj