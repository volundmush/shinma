import asyncio
import logging

from collections import defaultdict
from shinma.utils.misc import import_from_module
from logging.handlers import TimedRotatingFileHandler


class BaseService:
    init_order = 0
    setup_order = 0
    start_order = 0

    def setup(self):
        pass

    async def start(self):
        pass


class BaseApplication:

    def __init__(self, settings, loop):
        self.settings = settings
        self.classes = defaultdict(dict)
        self.services = dict()
        self.loop = loop
        self.root_awaitables = list()

    def setup(self):
        found_classes = list()
        # Import all classes from the given config object.
        for category, d in self.settings.CLASSES.items():
            for name, path in d.items():
                found = import_from_module(path)
                found.app = self
                self.classes[category][name] = found
                if hasattr(found, 'class_init'):
                    found_classes.append(found)

        for name, v in sorted(self.classes['services'].items(), key=lambda x: getattr(x[1], 'init_order', 0)):
            self.services[name] = v()

        for service in sorted(self.services.values(), key=lambda s: getattr(s, 'load_order', 0)):
            service.setup()
        for cls in found_classes:
            cls.class_init()

    async def start(self):
        self.setup()
        start_services = sorted(self.services.values(), key=lambda s: s.start_order)
        await asyncio.gather(*(service.start() for service in start_services))


class ApplicationCore(BaseApplication):
    pass

