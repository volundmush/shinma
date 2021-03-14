from . base import BaseTypeClass, ReverseHandler
from shinma.utils import lazy_property


class MobileTypeClass(BaseTypeClass):
    typeclass_name = "CoreMobile"
    typeclass_family = 'mobile'
    prefix = "mobile"
    class_initial_data = {
        "tags": ["mobile"]
    }
    command_families = ['mobile']

    def listeners(self):
        return self.playviews.all()

    def is_active(self):
        return self.playviews.all()

    @lazy_property
    def playviews(self):
        return ReverseHandler(self, 'core', 'character', 'character')

    @lazy_property
    def controllers(self):
        return ReverseHandler(self, 'core', 'puppet', 'puppet')

    def init_attributes(self):
        self.attributes.set('core', 'playtime', 0)

    def get_slevel(self):
        if (pview := self.playviews.all()):
            return max([p.get_slevel() for p in pview])
        return super().get_slevel()
