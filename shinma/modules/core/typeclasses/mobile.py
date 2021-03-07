from . base import BaseTypeClass


class MobileTypeClass(BaseTypeClass):
    typeclass_name = "CoreMobile"
    typeclass_family = 'mobile'
    prefix = "mobile"
    class_initial_data = {
        "tags": ["mobile"]
    }
    command_families = ['mobile']

    def listeners(self):
        if (p := self.reverse.first('playview_puppet')):
            return [p]
        return []

    def is_active(self):
        return self.relations.first('playview_character') or self.relations.first('playview_puppet')