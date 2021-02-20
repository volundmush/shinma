from shinma.scripts import GameScript
import asyncio
from asyncio import Queue
from aiohttp import ClientSession, WSMsgType
import ujson
from . ansi import parse_ansi


class Connection:
    service = None

    def __init__(self, script, data):
        self.script = script
        self.game = script.game
        self.name = data["id"]
        self.incoming_queue = Queue()
        self.outgoing_queue = Queue()
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
        self.task = None

        new_msg = {
            "id": self.name,
            "kind": "client_capabilities",
            "capabilities": data.get("capabilities")
        }
        self.update_capabilities(new_msg)

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"

    async def msg_client_json(self, msg):
        pass

    async def msg_client_gmcp(self, msg):
        pass

    async def msg_client_capabilities(self, msg):
        self.update_capabilities(msg)
        self.game.dispatch_event("net_client_reconfigured", connection=self)

    def update_capabilities(self, msg):
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
        """
        self.game.dispatch_event("net_client_disconnected", reason=msg["reason"], connection=self)
        self.stop()

    async def msg_client_line(self, msg):
        """
        This message is received when a client sends a text command.
        """
        self.game.dispatch_event("net_client_command", text=msg["line"], connection=self)

    async def msg_client_lines(self, msg):
        for line in msg["lines"]:
            self.game.dispatch_event("net_client_command", text=line, connection=self)

    def start(self):
        self.game.dispatch_event("net_client_connected", connection=self)
        self.task = asyncio.create_task(self.run())

    async def run(self):
        await asyncio.gather(self.process_incoming(), self.process_outgoing())

    async def process_incoming(self):
        while True:
            try:
                msg = await self.incoming_queue.get()
                if (kind := msg.get("kind", None)) and (handler := self.switchboard.get(kind, None)):
                    await handler(msg)
            except Exception as e:
                print(f"Exception on {self} Incoming: {e}")

    async def process_outgoing(self):
        while True:
            try:
                msg = await self.outgoing_queue.get()
                await self.service.outgoing_queue.put(msg)
            except Exception as e:
                print(f"Exception on {self} Outgoing: {e}")


    def stop(self):
        if self.task:
            self.task.cancel()
        self.service.connections.pop(self.name)

    def msg(self, message):
        if "text" in message.data:
            self.outgoing_queue.put_nowait({
                "kind": "session_line",
                "id": self.name,
                "line": parse_ansi(message.data["text"], strip_ansi=True if not self.ansi else False, xterm256=self.xterm256,
                                   mxp=self.mxp)
            })


class NetScript(GameScript):
    name = "net"
    version = "0.0.1"
    connection_class = Connection

    def __init__(self, game, name):
        super().__init__(game, name)
        self.connections = dict()
        self.ws_link = None
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

    async def start(self):
        await asyncio.gather(self.start_websocket(), self.process_outgoing(), self.process_incoming())

    async def process_outgoing(self):
        while True:
            try:
                if self.ws_link and not self.ws_link.closed:
                    msg = await self.outgoing_queue.get()
                    await self.ws_link.send_str(ujson.dumps(msg))
                else:
                    await asyncio.sleep(0.1)
            except Exception as e:
                print(f"{self} Outgoing encountered a traceback: {e}")

    async def process_incoming(self):
        while True:
            try:
                if self.ws_link:
                    msg = await self.incoming_queue.get()
                    if (kind := msg.get("kind", None)) and (handler := self.switchboard.get(kind, None)):
                        await handler(msg)
                    else:
                        pass
                else:
                    await asyncio.sleep(0.1)
            except Exception as e:
                print(f"{self} Incoming encountered a traceback: {e}")

    async def msg_client_connected(self, msg):
        if (data := msg.get("protocol", None)) and isinstance(data, dict):
            if (conn := self.connections.get(data["id"], None)):
                await conn.incoming_queue.put(msg)
            else:
                await self.create_client(data)


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
                    await self.create_client(v)

    async def create_client(self, data):
        for result in self.game.dispatch_event("net_client_allow_connect", data):
            # This event call is for banning checks and the like.
            if isinstance(result, str):
                await self.outgoing_queue.put({"kind": "client_disconnected", "id": data["id"],
                                               "reason": "could not create game session"})
                return
        conn = self.connection_class(self, data)
        self.connections[conn.name] = conn
        conn.start()

    async def msg_portal_json(self, msg):
        pass

    async def start_websocket(self):
        running = True
        while running:
            try:
                async with ClientSession(loop=asyncio.get_event_loop()) as session:
                    async with session.ws_connect(self.game.settings.PORTAL) as ws:
                        self.ws_link = ws
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
            except Exception as e:
                print(f"{self} encountered a traceback: {e}")