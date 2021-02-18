from shinma.core import BaseService
import asyncio
from asyncio import Queue
from aiohttp import ClientSession, WSMsgType
import ujson


class PlayView:
    service = None

    def __init__(self,  name, character):
        self.name = name
        self.cmd_queue = Queue()
        self.connections = dict()
        self.incoming_queue = Queue()
        self.outgoing_queue = Queue()
        self.character = character
        self.puppet = character


class Connection:
    service = None

    def __init__(self, data):
        self.name = data["id"]
        self.incoming_queue = Queue()
        self.outgoing_queue = Queue()
        self.session = None
        self.playview = None
        self.gameobject = None
        self.incoming_task = None
        self.outgoing_task = None
        self.switchboard = {
            "client_json": self.msg_client_json,
            "client_gmcp": self.msg_client_gmcp,
            "client_capabilities": self.msg_client_capabilities,
            "client_disconnected": self.msg_client_disconnected,
            "client_line": self.msg_client_line,
            "client_lines": self.msg_client_lines
        }
        self.address = data.get("addr", "UNKNOWN")
        self.tls = data.get("tls", False)

        self.protocol = "UNKNOWN"
        self.client_name = "UNKNOWN"
        self.client_version = "UNKNOWN"
        self.utf8 = False
        self.html = False
        self.mxp = False
        self.gmcp = False
        self.msdp = False
        self.mssp = False
        self.ansi = False
        self.xterm256 = False
        self.width = 78,
        self.height = 24
        self.screen_reader = False

        new_msg = {
            "id": self.name,
            "kind": "client_capabilities",
            "capabilities": data.get("capabilities")
        }

        self.incoming_queue.put_nowait(new_msg)

    def create_gameobject(self):
        self.gameobject = self.service.app.services["game"].spawn_object(self.service.app.settings.PROTOTYPES["connection"], name=self.name)
        self.gameobject.connection = self

    async def msg_client_json(self, msg):
        pass

    async def msg_client_gmcp(self, msg):
        pass

    async def msg_client_capabilities(self, msg):
        cap = msg.get("capabilities", dict())

        old_protocol = self.protocol
        self.protocol = cap.get("protocol", "UNKNOWN").upper()

        old_client_name = self.client_name
        self.client_name = cap.get("client_name", "UNKNOWN").upper()

        old_client_version = self.client_version
        self.client_version = cap.get("client_version", "UNKNOWN").upper()

        old_utf8 = self.utf8
        self.utf8 = cap.get("utf8", False)

        old_html = self.html
        self.html = cap.get("html", False)

        old_mxp = self.mxp
        self.mxp = cap.get("mxp", False)

        old_gmcp = self.gmcp
        self.gmcp = cap.get("gmcp", False)

        old_msdp = self.msdp
        self.msdp = cap.get("msdp", False)

        old_ansi = self.ansi
        self.ansi = cap.get("ansi", False)

        old_mssp = self.mssp
        self.mssp = cap.get("mssp", False)

        # MSSP is a bit different here!
        # if MSSP is suddenly enabled, we should send the MSSP update.
        if old_mssp == False and self.mssp == True:
            print("i ought to MSSP!")

        old_xterm256 = self.xterm256
        self.xterm256 = cap.get("xterm256", False)

        old_width = self.width
        self.width = cap.get("width", 78)

        old_height = self.height
        self.height = cap.get("height", 24)

        old_screen_reader = self.screen_reader
        self.screen_reader = cap.get("screen_reader", False)

    async def msg_client_disconnected(self, msg):
        """
        This message is received if the client has closed their connection on the Portal.

        TODO: Remove self from NetService.connections and other components.
        If all Connections vacate a PlayView, terminate the PlayView.
        """
        pass

    async def msg_client_line(self, msg):
        if self.gameobject:
            await self.gameobject.cmd_queue.put(msg["line"])

    async def msg_client_lines(self, msg):
        if self.gameobject:
            for line in msg["lines"]:
                await self.gameobject.cmd_queue.put(line)

    async def start(self):
        await asyncio.gather(self.process_incoming(), self.process_outgoing())

    async def process_incoming(self):
        while True:
            msg = await self.incoming_queue.get()
            if (kind := msg.get("kind", None)) and (handler := self.switchboard.get(kind, None)):
                await handler(msg)

    async def process_outgoing(self):
        while True:
            msg = await self.outgoing_queue.get()
            await self.service.outgoing_queue.put(msg)

    def stop(self):
        if self.incoming_task:
            self.incoming_task.cancel()
        if self.outgoing_task:
            self.outgoing_task.cancel()


class Session:
    service = None

    def __init__(self, name, account, gameobject):
        self.name = name
        self.account = account
        self.connections = set()
        self.gameobject = gameobject


class NetService(BaseService):

    def __init__(self):
        self.playviews = dict()
        self.connections = dict()
        self.ws_link = None
        self.incoming_task = None
        self.outgoing_task = None
        self.sessions = dict()
        self.incoming_queue = Queue()
        self.outgoing_queue = Queue()
        self.switchboard = {
            "portal_json": self.msg_portal_json,
            "client_json": self.msg_client_general,
            "client_list": self.msg_client_list,
            "client_gmcp": self.msg_client_general,
            "client_capabilities": self.msg_client_general,
            "client_disconnected": self.msg_client_general,
            "client_connected": self.msg_client_connected,
            "client_line": self.msg_client_general,
            "client_lines": self.msg_client_general
        }
        for k, v in self.app.classes["net"].items():
            v.service = self

    async def start(self):
        await asyncio.gather(self.start_websocket(), self.process_outgoing(), self.process_incoming())

    async def process_outgoing(self):
        while True:
            if self.ws_link and not self.ws_link.closed:
                msg = await self.outgoing_queue.get()
                await self.ws_link.send_str(ujson.dumps(msg))
            else:
                await asyncio.sleep(0.1)

    async def process_incoming(self):
        while True:
            if self.ws_link:
                msg = await self.incoming_queue.get()
                if (kind := msg.get("kind", None)) and (handler := self.switchboard.get(kind, None)):
                    await handler(msg)
                else:
                    pass
            else:
                await asyncio.sleep(0.1)

    async def msg_client_connected(self, msg):
        if (data := msg.get("protocol", None)) and isinstance(data, dict):
            if (conn := self.connections.get(data["id"], None)):
                await conn.incoming_queue.put(msg)
            else:
                conn = self.app.classes["net"]["connection"](data)
                try:
                    conn.create_gameobject()
                    self.connections[data["id"]] = conn
                    asyncio.create_task(conn.start())
                except Exception as e:
                    print(f"something done goofed creating object: {e}")
                    await self.outgoing_queue.put({"kind": "client_disconnected", "id": data["id"],
                                                   "reason": "could not create game session"})

    async def msg_client_general(self, msg):
        if "id" in msg and (conn := self.connections.get(msg["id"], None)):
            await conn.incoming_queue.put(msg)

    async def msg_client_list(self, msg):
        """
        There are two ways this could be called - the first time we connect,
        or at another point.

        Although this message is meant to build the initial client list, we must handle
        the case where clients already exist.
        """
        print("server processing client list")
        if (data := msg.get("data", None)) and isinstance(data, dict):
            for k, v in data.items():
                if (conn := self.connections.get(k, None)):
                    new_msg = {
                        "id": k,
                        "kind": "client_capabilities",
                        "capabilities": v["capabilities"]
                    }
                    await conn.incoming_queue.put(new_msg)
                else:
                    conn = self.app.classes["net"]["connection"](v)
                    try:
                        conn.create_gameobject()
                        self.connections[v["id"]] = conn
                        asyncio.create_task(conn.start())
                    except Exception as e:
                        print(f"something done goofed creating object: {e}")
                        await self.outgoing_queue.put({"kind": "client_disconnected", "id": v["id"],
                                                       "reason": "could not create game session"})

    async def msg_portal_json(self, msg):
        pass

    async def start_websocket(self):
        running = True
        while running:
            async with ClientSession(loop=asyncio.get_event_loop()) as session:
                async with session.ws_connect(self.app.settings.PORTAL) as ws:
                    self.ws_link = ws
                    #self.outgoing_task = asyncio.create_task(self.process_outgoing())
                    #self.incoming_task = asyncio.create_task(self.process_incoming())
                    async for msg in ws:
                        if msg.type == WSMsgType.TEXT:
                            j_data = ujson.loads(msg.data)
                            await self.incoming_queue.put(j_data)
                        elif msg.type == WSMsgType.ERROR:
                            print("WS errored")
                            break
                        elif msg.type == WSMsgType.CLOSE:
                            print("WS Closed")
                            break
                        else:
                            print("WS else happened")
                            pass
                        print(f"CURRENT CONNECTIONS: {self.connections}")
                    print("websocket loop reached end")
                    self.ws_link = None
                    #self.incoming_task.cancel()
                    #self.outgoing_task.cancel()
