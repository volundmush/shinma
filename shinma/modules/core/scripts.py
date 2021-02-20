from shinma.objects import GameObject
from shinma.scripts import GameScript
from .. net.ansi import ANSIString


class CoreConnectionScript(GameScript):

    def __init__(self, game, name):
        super().__init__(game, name)
        self.game_switchboard = {
            "net_client_connected": self.net_client_connected,
            "net_client_command": self.net_client_command,
            "net_client_gmcp": self.net_client_gmcp,
            "net_client_disconnected": self.net_client_disconnected,
            "net_client_reconfigured": self.net_client_reconfigured
        }
        self.object_switchboard = {

        }

    def on_object_event(self, gameobj: GameObject, event: str, *args, **kwargs):
        if (handler := self.object_switchboard.get(event, None)):
            return handler(gameobj, *args, **kwargs)

    def on_game_event(self, event: str, *args, **kwargs):
        if (handler := self.game_switchboard.get(event, None)):
            return handler(*args, **kwargs)

    def net_client_connected(self, *args, **kwargs):
        pass

    def net_client_command(self, *args, **kwargs):
        pass

    def net_client_gmcp(self, *args, **kwargs):
        pass

    def net_client_disconnected(self, *args, **kwargs):
        pass

    def net_client_reconfigured(self, *args, **kwargs):
        pass