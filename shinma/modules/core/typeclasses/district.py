from . base import BaseTypeClass


class DistrictTypeClass(BaseTypeClass):
    typeclass_name = "CoreDistrict"
    typeclass_family = 'district'
    prefix = "district"
    class_initial_data = {
        "tags": ["district"]
    }
