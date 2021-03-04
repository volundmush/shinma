from typing import Any, Dict
from . exception import GameObjectException


class Attribute:
    __slots__ = ["category", "name", "value"]

    def __init__(self, category, name, value):
        self.category = category
        self.name = name
        self.value = value

    def set(self, value):
        old_value = self.get()
        self.value = value
        return old_value

    def get(self):
        return self.value


class AttributeCategory:
    __slots__ = ["parent", "name", "attributes"]

    def __init__(self, parent, name):
        self.parent = parent
        self.name = name
        self.attributes = dict()

    def get(self, name):
        if (attr := self.attributes.get(name, None)):
            return attr.get()
        return None

    def has(self, name):
        return name in self.attributes

    def all(self):
        return {k: value for k, v in self.attributes.items() if (value := v.get()) is not None}

    def set(self, name, value):
        if value is None:
            raise GameObjectException("Attributes cannot be set to None.")
        if (attr := self.attributes.get(name, None)):
            return attr.set(value)
        else:
            attr = Attribute(self, name, value)
            self.attributes[name] = attr
            return None

    def delete(self, name):
        if (attr := self.attributes.pop(name, None)):
            return attr.get()

    def clear(self):
        self.attributes.clear()

    def dump(self):
        return self.all()

    def count(self):
        return len(self.attributes)

    def __len__(self):
        return len(self.attributes)


class AttributeHandler:
    __slots__ = ["obj", "categories"]

    def __init__(self, obj):
        self.obj = obj
        self.categories = dict()

    def get(self, category: str, name: str):
        if (cat := self.categories.get(category, None)):
            return cat.get(name)
        return None

    def set(self, category: str, name: str, value: Any):
        if (cat := self.categories.get(category, None)):
            return cat.set(name, value)
        else:
            cat = AttributeCategory(self, name)
            self.categories[category] = cat
            return cat.set(name, value)

    def delete(self, category: str, name: str = None):
        if (cat := self.categories.get(category, None)):
            if name is None:
                cat = self.categories.pop(category, None)
                return cat.all()
            else:
                return cat.delete(name)

    def clear(self, category: str = None):
        if not category:
            self.categories.clear()
        else:
            if (cat := self.categories.get(category, None)):
                return cat.clear()

    def has(self, category: str, name: str):
        if not (cat := self.categories.get(category, None)):
            return False
        return cat.has(name)

    def dump(self):
        return {k: dump for k, v in self.categories.items() if (dump := v.dump())}

    def load_category(self, category: str, data: Dict[str, Any]):
        if not (cat := self.categories.get(category, None)):
            cat = AttributeCategory(self, category)
            self.categories[category] = cat
        for k, v in data.items():
            cat.set(k, v)
