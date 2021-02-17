from shinma.core import BaseService
from asyncio import Queue


class PlayView:

    def __init__(self,  name, gameobject, character):
        self.name = name
        self.cmd_queue = Queue()
        self.connections = dict()
        self.incoming_queue = Queue()
        self.outgoing_queue = Queue()
        self.gameobject = gameobject
        self.character = character
        self.puppet = character


class Connection:

    def __init__(self, name, gameobject):
        self.name = name
        self.incoming_queue = Queue()
        self.outgoing_queue = Queue()
        self.session = None
        self.gameobject = gameobject


class Session:

    def __init__(self, name, account, gameobject):
        self.name = name
        self.account = account
        self.connections = set()
        self.gameobject = gameobject


class NetService(BaseService):

    def __init__(self):
        self.playviews = dict()
        self.connections = dict()
        self.link = None
        self.sessions = dict()