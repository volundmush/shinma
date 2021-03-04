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
        if (p := self.relations.get('playview')):
            return [p]
        return []
