import random
import string
from typing import Any, Union
from collections import defaultdict
from shinma.utils import lazy_property
from .. gamedb.objects import GameObject
from .. gamedb.exception import GameObjectException
from .. mush.ansi import AnsiString
from ..utils import formatter as fmt
from ..mush.parser import Parser


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


class RelationHandler:
    def __init__(self, owner):
        self.owner = owner
        self.relations = dict()

    def set(self, kind: str, obj):
        self.relations[kind] = obj

    def clear(self, kind):
        self.relations.pop(kind, None)

    def get(self, kind):
        return self.relations.get(kind, None)


class ReverseHandler:

    def __init__(self, owner):
        self.owner = owner
        self.relations = defaultdict(set)

    def all(self, kind):
        if kind in self.relations:
            return set(self.relations[kind])
        return set()

    def add(self, kind, obj):
        self.relations[kind].add(obj)

    def remove(self, kind, obj):
        if kind in self.relations:
            if obj in self.relations[kind]:
                self.relations[kind].remove(obj)


class MushAttribute:
    def __init__(self, name):
        self.owner = None
        self.name = name
        self.value = None
        self.flags = set()

    def dump(self):
        return {
            'owner': self.owner.objid if self.owner else None,
            'flags': self.flags,
            'value': self.value.encoded() if self.value else ''
        }


class MushAttrHandler:

    def __init__(self, owner):
        self.owner = owner
        self.attributes = dict()
        for k, v in self.owner.attributes.all('mush').items():
            attr = MushAttribute(k)
            if (owner := self.owner.core.objects.get(v.get('owner', None), None)):
                attr.owner = owner
            attr.value = AnsiString(v.get('value', ''))
            attr.flags.update(v.get('flags', set()))

    def get_create_attr(self, attr: str):
        pass

    def get_attr(self, attr: str, inherit=True, ancestors=True, depth=0):
        if (attr := self.attributes.get(attr.upper())):
            return attr

    def get_attr_value(self, attr: str, inherit=True, ancestors=True, default=None):
        if (attr := self.get_attr(attr, inherit, ancestors)):
            return attr.value
        return default

    def set_attr_value(self, attr: str, value: Union[str, AnsiString]):
        if (attr := self.attributes.get(attr.upper(), None)):
            attr = MushAttribute(attr.upper())
            self.attributes[attr.name] = attr

        if isinstance(value, AnsiString):
            attr.value = value
        else:
            attr.value = AnsiString(value)

    def hasattr(self, attr: str, inherit=True, ancestors=True):
        if (attr := self.get_attr(attr, inherit, ancestors)):
            return True
        else:
            return False

    def hasattrval(self, attr: str, inherit=True, ancestors=True):
        if (attr := self.get_attr(attr, inherit, ancestors)):
            return attr.truthy()
        return False


class BaseTypeClass(GameObject):
    typeclass_name = None
    typeclass_family = None
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
            obj.setup_relations()
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
        return self.reverse.all('contents')

    def parser(self):
        return Parser(self.core, self.objid, self.objid, self.objid)

    def msg(self, text, **kwargs):
        flist = fmt.FormatList(self, **kwargs)
        flist.add(fmt.Text(text))
        self.send(flist)

    def send(self, message: fmt.FormatList):
        self.receive_msg(message)
        for listener in self.listeners():
            if listener not in message.relay_chain:
                listener.send(message.relay(self))

    def receive_msg(self, message: fmt.FormatList):
        pass

    def location(self):
        if (loc := self.reverse.get("room_contents", None)):
            return list(loc)[0]
        return None

    def render_appearance(self, viewer, internal=False):
        parser = viewer.parser()
        out = fmt.FormatList(viewer)
        if (nameformat := self.mush_attr.get_attr_value('NAMEFORMAT')):
            result, remaining, stopped = parser.evaluate(nameformat, executor=self, number_args={0: self.objid, 1: self.name})
            out.add(fmt.Text(result))
        else:
            out.add(fmt.Text(AnsiString.from_args('hw', self.name) + f"({self.objid})"))
        if internal and (idesc := self.mush_attr.get_attr_value('IDESCRIBE')):
            idesc_eval, remaining, stopped = parser.evaluate(idesc, executor=self)
            if (idescformat := self.mush_attr.get_attr_value('IDESCFORMAT')):
                result, remaining, stopped = parser.evaluate(idescformat, executor=self, number_args={0: idesc_eval})
                out.add(fmt.Text(result))
            else:
                out.add(fmt.Text(idesc_eval))
        elif (desc := self.mush_attr.get_attr_value('DESCRIBE')):
            desc_eval, remaining, stopped = parser.evaluate(desc, executor=self)
            if (descformat := self.mush_attr.get_attr_value('DESCFORMAT')):
                result, remaining, stopped = parser.evaluate(descformat, executor=self, number_args={0: desc_eval})
                out.add(fmt.Text(result))
            else:
                out.add(fmt.Text(desc_eval))
        if (contents := self.reverse.all('contents')):
            if (conformat := self.mush_attr.get_attr_value('CONFORMAT')):
                contents_objids = ' '.join([con.objid for con in contents])
                result, remaining, stopped = parser.evaluate(conformat, executor=self, number_args={0: contents_objids})
                out.add(fmt.Text(result))
            else:
                con = [AnsiString("Contents:")]
                for obj in contents:
                    con.append(f" * " + AnsiString.send_menu(AnsiString.from_args('hw', obj.name), [(f'look {obj.name}', 'Look')]) + f" ({obj.objid})")
                out.add(fmt.Text(AnsiString('\n').join(con)))
        if (exits := self.reverse.all('exits')):

            if (exitformat := self.mush_attr.get_attr_value('EXITFORMAT')):
                contents_objids = ' '.join([con.objid for con in exits])
                result, remaining, stopped = parser.evaluate(exitformat, executor=self, number_args={0: contents_objids})
                out.add(fmt.Text(result))
            else:
                con = [AnsiString("Obvious Exits:")]
                for obj in exits:
                    con.append(f" * " + AnsiString.send_menu(AnsiString.from_args('hw', obj.name), [(f'go {obj.name}', 'Move here')]) + f" leads to {obj.relations.get('destination').name}")
                out.add(fmt.Text(AnsiString('\n').join(con)))
        viewer.send(out)

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
            obj_chain[self.typeclass_family] = self
            return next_obj.find_cmd(text, obj_chain)

    def get_width(self):
        return 78

    def add_tag(self, tag: str):
        t = self.core.get_tag(tag)
        t.objects.add(self)

    def remove_tag(self, tag: str):
        t = self.core.get_tag(tag)
        if self in t.objects:
            t.objects.remove(self)

    @lazy_property
    def reverse(self):
        return ReverseHandler(self)

    @lazy_property
    def relations(self):
        return RelationHandler(self)

    def setup_relations(self):
        if (objid := self.attributes.get('core', 'parent')):
            if (obj := self.core.objects.get(objid, None)):
                obj.children.register(self)

    def move_to(self, destination, look=False):
        if (loc := self.relations.get('location')):
            loc.reverse.remove('contents', self)
        if destination:
            destination.reverse.add('contents', self)
            self.relations.set('location', destination)
            self.attributes.set('core', 'location', destination.objid)
            if look:
                destination.render_appearance(self, internal=True)
        else:
            self.relations.clear('location')
            self.attributes.delete('core', 'location')

    @lazy_property
    def mush_attr(self):
        return MushAttrHandler(self)