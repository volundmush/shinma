from . base import BaseTypeClass


class MobileTypeClass(BaseTypeClass):
    typeclass_name = "CoreMobile"
    prefix = "mobile"
    class_initial_data = {
        "tags": ["mobile"]
    }

    def get_playview(self):
        if (all := self.reverse["playview_character"]):
            return list(all)[0]

    def get_or_create_playview(self):
        if (pview := self.get_playview()):
            return pview, None
        pview, errors = self.core.mapped_typeclasses["playview"].create(objid=f"playview_{self.objid}")
        if errors:
            return None, errors
        pview.set_character(self)
        return pview, None

    def listeners(self):
        if (p := self.get_playview()):
            return [p]
        return []
