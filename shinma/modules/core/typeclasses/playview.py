from . base import BaseTypeClass
from ..cmdqueue import QueueEntry

class PlayViewTypeClass(BaseTypeClass):
    typeclass_name = "CorePlayView"
    typeclass_family = 'playview'
    prefix = "playview"
    class_initial_data = {
        "tags": ["playview"]
    }
    command_families = ['playview']

    def get_next_cmd_object(self, obj_chain):
        return self.relations.get('playview_puppet')

    def listeners(self):
        return self.reverse.all('connection_playview')

    def at_connection_join(self, connection):
        ex = self.relations.get('playview_puppet').objid
        entry = QueueEntry(enactor=ex, executor=ex, caller=ex, actions='look', split=False)
        self.core.cmdqueue.push(entry)

    def at_connection_leave(self, connection):
        pass

    def at_playview_creation(self, connection=None):
        self.relations.set('playview_puppet', self.relations.get('playview_character'))