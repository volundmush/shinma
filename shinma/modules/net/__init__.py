from shinma.engine import GameModule
from . scripts import NetScript


class Module(GameModule):
    name = "net"

    def load_scripts(self):
        self.game.register_script("NetScript", NetScript)