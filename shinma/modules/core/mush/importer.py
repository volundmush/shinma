from . flatfile import PennDB
from shinma.utils import partial_match


class VolDB(PennDB):
    def __init__(self):
        super().__init__()
        self.ccp = None

    def cobj(self, abbr):
        if self.ccp is None:
            if not (code_object := partial_match("Core Code Parent <CCP>", self.objects.values(), key=lambda x: x.name)):
                raise Exception("Oops. No Core Code Parent in database!")
            self.ccp = code_object
        if not (attr := self.ccp.get(f"COBJ`{abbr.upper()}")):
            return None
        return self.find_obj(attr.value.clean)

    def list_accounts(self):
        if not (account_parent := self.cobj('accounts')):
            return None
        return {o.id: o for o in account_parent.children}

    def list_groups(self):
        if not (group_parent := self.cobj('gop')):
            return None
        return {o.id: o for o in group_parent.children}

    def list_index(self, number: int):
        return {o.id: o for o in self.type_index.get(number, set())}

    def list_players(self):
        return self.list_index(8)

    def list_rooms(self):
        return self.list_index(1)

    def list_exits(self):
        return self.list_index(4)

    def list_things(self):
        return self.list_index(2)


class Importer:
    def __init__(self, connection, path):
        self.db = VolDB.from_outdb(path)
        self.connection = connection
        self.core = connection.core
        connection.penn = self
        self.complete = set()
        self.obj_map = dict()

    def create_obj(self, dbobj, mode):
        obj, error = self.core.mapped_typeclasses[mode].create(name=dbobj.name, objid=dbobj.objid)
        self.obj_map[dbobj.id] = obj
        return obj

    def get_or_create_obj(self, dbobj, mode):
        if not (obj := self.obj_map.get(dbobj.id, None)):
            obj = self.create_obj(dbobj, mode)
            for k, v in dbobj.attributes.items():
                obj.attributes.set('mush', k, v.value.encoded)
        return obj

    def import_rooms(self):
        data = self.db.list_rooms()
        total = list()
        for k, v in data.items():
            obj = self.get_or_create_obj(v, 'room')
            total.append(obj)
            obj.add_tag('penn_room')
        return total

    def import_exits(self):
        data = self.db.list_exits()
        total = list()
        for k, v in data.items():
            if not (location := self.obj_map.get(v.location, None)):
                continue  # No reason to make an Exit for a room that doesn't exist, is there?
            if not (destination := self.obj_map.get(v.destination, None)):
                continue  # No reason to make an Exit for a room that doesn't exist, is there?
            obj = self.get_or_create_obj(v, 'exit')
            obj.attributes.set('core', 'room', location.objid)
            location.reverse.add('exits', obj)

            obj.attributes.set('core', 'destination', destination.objid)
            destination.reverse.add('entrances', obj)

            obj.add_tag('penn_exit')
            total.append(obj)
        return total

    def import_accounts(self):
        data = self.db.list_accounts()
        total = list()
        for k, v in data.items():
            obj = self.get_or_create_obj(v, 'account')
            obj.add_tag('penn_account')
            total.append(obj)
        return total

    def import_characters(self):
        data = self.db.list_players()
        total = list()
        for k, v in data.items():
            if 'Guest' in v.powers:
                # Filtering out guests.
                continue
            obj = self.get_or_create_obj(v, 'mobile')
            obj.attributes.set("core", "penn_hash", v.get('XYXXY').value.clean)
            if (account := self.obj_map.get(v.parent, None)):
                # Hooray, we have an account!
                account.reverse.add('characters', obj)
                obj.attributes.set('core', 'account', account.objid)
                obj.relations.set('account', account)

                if 'WIZARD' in v.flags:
                    if not account.attributes.has('core', 'supervisor_level'):
                        account.attributes.set('core', 'supervisor_level', 10)
                elif 'ROYALTY' in v.flags:
                    if not account.attributes.has('core', 'supervisor_level'):
                        account.attributes.set('core', 'supervisor_level', 8)
                elif (va := obj.attributes.get('mush', 'V`ADMIN')):
                    if va == '1':
                        if not account.attributes.has('core', 'supervisor_level'):
                            account.attributes.set('core', 'supervisor_level', 6)

                # if we don't get an account, then this character can still be accessed using their password, but...
            if (location := self.obj_map.get(v.location, None)):
                obj.attributes.set('core', 'location', location.objid)
                obj.relations.set('location', location)
                location.reverse.add('contents', obj)
            obj.add_tag('penn_character')
            total.append(obj)
        return total
