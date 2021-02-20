class GameScript:

    def __init__(self, game, name):
        self.game = game
        self.name = name
        self.objects = set()
        self.prototypes = set()
        self.task = None

    def on_object_event(self, gameobj, event: str, *args, **kwargs):
        """
        This is called by GameObject's dispatch_event method. event is an arbitrary string,
        and *args and **kwargs are data attributed to that event.

        This call must never raise an unhandled exception or otherwise break. Try to keep it as self-contained
        as possible.
        """
        pass

    def on_game_event(self, event: str, *args, **kwargs):
        """
        This is called by the GameService, which is why a gameobj is not passed. This is meant to be used for
        things such as 'timers' - like processing hunger for all attached Objects every x seconds. It is also
        useful for 'global events' for which no GameObject is (yet?) relevant.
        """

    async def start(self):
        pass

    def stop(self):
        if self.task:
            self.task.cancel()
