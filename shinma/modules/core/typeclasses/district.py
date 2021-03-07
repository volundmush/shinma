from . base import BaseTypeClass, ReverseHandler
from shinma.utils import lazy_property


class DistrictTypeClass(BaseTypeClass):
    typeclass_name = "CoreDistrict"
    typeclass_family = 'district'
    prefix = "district"
    class_initial_data = {
        "tags": ["district"]
    }

    @lazy_property
    def exits(self):
        return ReverseHandler(self, 'core', 'district', 'district')

    @lazy_property
    def rooms(self):
        return ReverseHandler(self, 'core', 'district', 'district')

    @lazy_property
    def districts(self):
        return ReverseHandler(self, 'core', 'parent', 'parent')
