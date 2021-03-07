import time
from . base import BaseTypeClass, ReverseHandler
from ..cmdqueue import QueueEntry
from shinma.utils import lazy_property


class PlayViewTypeClass(BaseTypeClass):
    typeclass_name = "CorePlayView"
    typeclass_family = 'playview'
    prefix = "playview"
    class_initial_data = {
        "tags": ["playview"]
    }
    command_families = ['playview']

    def get_next_cmd_object(self, obj_chain):
        return self.relations.get('puppet')

    def listeners(self):
        return self.connections.all()

    def at_connection_join(self, connection):
        if (pup := self.relations.get('puppet', None)):
            if (loc := pup.relations.get('location', None)):
                loc.render_appearance(pup, internal=True)

    def at_connection_leave(self, connection):
        pass

    def at_last_connection_leave(self, connection):
        self.end_playview()

    def at_playview_creation(self, character, connection=None):
        character.playviews.add(self)
        character.controllers.add(self)
        if (loc := self.core.objects.get(character.attributes.get('core', 'logout_location'), None)):
            loc.msg(text=f"{character.name} has entered the game.")
            character.move_to(loc)

    @lazy_property
    def connections(self):
        return ReverseHandler(self, 'core', 'playview', 'playview')

    def end_playview(self):
        char = self.relations['character']
        if (loc := char.relations.get('location', None)):
            char.attributes.set('core', 'logout_location', loc.objid)
            char.move_to(destination=None, look=False)
            loc.msg(text=f"{char.name} has left the game.")