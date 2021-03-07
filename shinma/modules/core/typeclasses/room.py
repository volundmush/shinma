from . base import BaseTypeClass, ReverseHandler
from shinma.utils import lazy_property
from ..utils import formatter as fmt
from ..utils.text import tabular_table
from ..mush.ansi import AnsiString


class RoomExitFormatter(fmt.BaseFormatter):

    def __init__(self, exits):
        self.exits = exits

    def render(self, formatter, obj):
        sections = list()
        for ex in self.exits:
            commands = [(f'goto {ex.name}', 'Head through exit')]
            alias = ex.aliases[0] if ex.aliases else ex.name[:3]
            start = '<' + AnsiString.send_menu(AnsiString.from_args('hx', alias.upper()), commands=commands) + '>'
            start = start.ljust(6)
            if (dest := ex.relations.get('destination')):
                destname = dest.name
            else:
                destname = 'N/A'
            rest = AnsiString.send_menu(ex.name, commands=commands) + ' to ' + destname
            sections.append(start + rest)

        return tabular_table(sections, field_width=37, line_length=obj.get_width())


class RoomPlayersFormatter(fmt.BaseFormatter):

    def __init__(self, players):
        self.players = players

    def render(self, formatter, obj):
        table = fmt.Table("Idl", "Name", "Template", "Short-Desc")

        for p in self.players:
            table.add_row("NA", p.name, "Not Set", "Dunno Yet")
        return table.render(formatter, obj)


class RoomItemsFormatter(fmt.BaseFormatter):

    def __init__(self, items):
        self.items = items

    def render(self, formatter, obj):
        table = fmt.Table("Name", "Short-Desc")

        for p in self.items:
            table.add_row(p.name, "Dunno Yet")
        return table.render(formatter, obj)


class RoomTypeClass(BaseTypeClass):
    typeclass_name = "CoreRoom"
    typeclass_family = 'room'
    prefix = "room"
    class_initial_data = {
        "tags": ["room"]
    }

    def render_appearance(self, viewer, internal=False):
        parser = viewer.parser()
        out = fmt.FormatList(viewer)
        out.add(fmt.Header(self.name))
        if (desc := self.mush_attr.get_attr_value('DESCRIBE')):
            desc_eval, remaining, stopped = parser.evaluate(desc, executor=self)
            out.add(fmt.Text(desc_eval))
        if (contents := self.contents.all()):
            mobiles = [c for c in contents if c.typeclass_family == 'mobile' and viewer.can_see(c)]
            other = [c for c in contents if c not in mobiles and viewer.can_see(c)]
            if mobiles:
                out.add(fmt.Subheader('Players'))
                out.add(RoomPlayersFormatter(mobiles))
            if other:
                out.add(fmt.Subheader('Items'))
                out.add(RoomItemsFormatter(other))
        if (exits := self.exits.all()):
            exits = [e for e in exits if viewer.can_see(e)]
            if exits:
                out.add(fmt.Subheader('Exits'))
                out.add(RoomExitFormatter(exits))
        out.add(fmt.Footer())
        viewer.send(out)

    @lazy_property
    def exits(self):
        return ReverseHandler(self, 'core', 'location', 'location')

    @lazy_property
    def entrances(self):
        return ReverseHandler(self, 'core', 'destination', 'destination')
