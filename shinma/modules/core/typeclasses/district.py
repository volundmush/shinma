from . base import BaseTypeClass


class DistrictTypeClass(BaseTypeClass):
    typeclass_name = "CoreDistrict"
    prefix = "district"
    class_initial_data = {
        "tags": ["district"]
    }
