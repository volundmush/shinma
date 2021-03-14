import random
import string
import re
import time
import weakref
from typing import Any, Union
from collections import defaultdict
from shinma.utils import lazy_property, partial_match
from .. gamedb.objects import GameObject
from .. gamedb.exception import GameObjectException
from .. mush.ansi import AnsiString
from ..utils import formatter as fmt
from ..mush.parser import Parser


class RelationHandler:
    def __init__(self, owner):
        self.owner = owner
        self.relations = dict()

    def set(self, kind: str, obj):
        if (found := self.relations.get(kind, None)):
            if found == obj:
                return
            else:
                found.reverse.remove(kind, self.owner)
        self.relations[kind] = obj
        obj.reverse.add(kind, self.owner)

    def clear(self, kind: str):
        if (found := self.relations.pop(kind, None)):
            found.reverse.remove(kind, self.owner)

    def get(self, kind: str):
        return self.relations.get(kind, None)

    def dump(self):
        return {k: v.objid for k, v in self.relations.items()}

    def delete(self):
        for rel in self.relations.keys():
            self.clear(rel)


class ReverseHandler:

    def __init__(self, owner, category: str, attr: str, rel: str = None):
        self.owner = owner
        self.category = category
        self.attr = attr
        self.rel = rel
        self.relations = weakref.WeakSet()

    def all(self):
        return list(self.relations)

    def add(self, obj, loading=False):
        self.relations.add(obj)
        if not loading:
            obj.attributes.set(self.category, self.attr, self.owner.objid)
        if self.rel:
            obj.relations[self.rel] = self.owner

    def remove(self, obj):
        if obj in self.relations:
            self.relations.remove(obj)
        if self.rel:
            obj.relations.pop(self.rel, None)


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
            self.attributes[k.upper()] = attr

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
    re_search = re.compile(r"(?i)^(?P<pre>(?P<quant>all|\d+)\.)?(?P<target>[A-Z0-9_.-]+)")

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
    def create(cls, name: str = None, objid=None, prefix=None, initial_data=None, asset=False, timestamp=None, identity=None):
        if objid is None:
            objid = cls.generate_id(prefix)
        if name is None:
            name = objid
        if initial_data is None:
            initial_data = cls.class_initial_data
        try:
            if identity:
                if not identity.valid(name):
                    return None, f"{name} is not a valid name for a {identity.name}"
                if not identity.available(name):
                    return None, f"The name {name} is already in use."
            obj = cls(objid, name, initial_data=initial_data, asset=asset)
            cls.core.objects[objid] = obj
            obj.load_initial()
            if timestamp is None:
                timestamp = time.time()
            obj.attributes.set('core', 'datetime_created', timestamp)
            obj.attributes.set('core', 'datetime_modified', timestamp)
            if identity:
                obj.identity = identity
                identity.objects.add(obj)
            obj.init_attributes()
            obj.setup_relations()
        except GameObjectException as e:
            cls.core.objects.pop(objid, None)
            return None, str(e)
        return obj, None

    def init_attributes(self):
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__} TypeClass: {self.objid} - {self.name}>"

    def __str__(self):
        return self.name

    def listeners(self):
        return self.contents.all()

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

    def render_appearance(self, viewer, internal=False):
        parser = viewer.parser()
        out = fmt.FormatList(viewer)
        if (nameformat := self.mush_attr.get_attr_value('NAMEFORMAT')):
            result, remaining, stopped = parser.evaluate(nameformat, executor=self, number_args={0: self.objid, 1: self.name})
            out.add(fmt.Text(result))
        else:
            out.add(fmt.Text(AnsiString.from_args('hw', self.name) + f" ({self.objid})"))
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
        if (contents := self.contents.all()):
            if (conformat := self.mush_attr.get_attr_value('CONFORMAT')):
                contents_objids = ' '.join([con.objid for con in contents])
                result, remaining, stopped = parser.evaluate(conformat, executor=self, number_args={0: contents_objids})
                out.add(fmt.Text(result))
            else:
                con = [AnsiString("Contents:")]
                for obj in contents:
                    con.append(f" * " + AnsiString.send_menu(AnsiString.from_args('hw', obj.name), [(f'look {obj.name}', 'Look')]) + f" ({obj.objid})")
                out.add(fmt.Text(AnsiString('\n').join(con)))
        viewer.send(out)

    def get_cmd_matchers(self):
        results = set()
        for fam in self.command_families:
            results = results.union(self.core.cmdfamilies.get(fam, []))
        results = [matcher for matcher in results if matcher.access(self)]
        return sorted(results, key=lambda g: getattr(g, "priority", 0))

    def get_full_chain(self):
        chain = {self.typeclass_family: self}
        obj = self
        while obj is not None:
            obj = obj.get_next_cmd_object(chain)
            if obj:
                chain[obj.typeclass_family] = obj
        return chain

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

    def setup_relations(self):
        pass

    def move_to(self, destination, look=False):
        if (loc := self.relations.get('location', None)):
            if loc == destination:
                return
            loc.contents.remove(self)
        if destination:
            destination.contents.add(self)
            if look:
                destination.render_appearance(self, internal=True)

    @lazy_property
    def mush_attr(self):
        return MushAttrHandler(self)

    def is_active(self):
        return True

    def can_see(self, other):
        if not other.is_active():
            return False
        return True

    def generate_identifiers_for(self, other, names=True, aliases=True):
        out = list()
        if names:
            out.extend(other.name.split())
        if aliases:
            out.extend(other.aliases)
        return out

    def search(self, text, candidates, exact=False, names=True, aliases=True, use_objids=False):
        text_lower = text.lower()
        if text_lower in ('self', 'me'):
            return [self]
        if text_lower in ('here',):
            return [self.relations.get('location')]
        if not (candidates := set(candidates)):
            return []
        if self in candidates:
            candidates.remove(self)
        if not candidates:
            return []

        if use_objids:
            objids = {c.objid: c for c in candidates}
            if (found := objids.get(text, None)):
                return [found]

        if not (names or aliases):
            return []

        if not (match := self.re_search.fullmatch(text)):
            return []
        gdict = match.groupdict()

        identifiers = defaultdict(list)

        target = gdict['target'].strip('"')

        for can in candidates:
            for iden in self.generate_identifiers_for(can, names=names, aliases=aliases):
                ilower = iden.lower()
                if ilower in ('the', 'of', 'an', 'a', 'or', 'and'):
                    continue
                identifiers[iden.lower()].append(can)
        out = []

        if exact:
            if (found := identifiers.get(target.lower())):
                out = found
            else:
                return out
        else:
            m = partial_match(target, identifiers.keys())
            if not m:
                return out
            out = identifiers[m]

        if (q := gdict.get('quant')):
            if q == 'all':
                return out
            else:
                q = int(q)
                if len(out) < q:
                    l = list()
                    l.append(out[q-1])
                else:
                    return []
        else:
            if out:
                return [out[0]]
            else:
                return []

    def dump(self):
        return {
            'objid': self.objid,
            'name': self.name,
            'aliases': self.aliases,
            'attributes': self.attributes.dump(),
            'tags': [t for t in self.tags.keys()],
            'typeclass': self.typeclass_name,
        }

    @lazy_property
    def contents(self):
        return ReverseHandler(self, 'core', 'location', 'location')

    def get_slevel(self):
        if self.attributes.has('core', 'supervisor_level'):
            return self.attributes.get('core', 'supervisor_level')
        else:
            return self.core.engine.settings.CORE_DEFAULT_SLEVEL