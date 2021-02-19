from shinma.game.commands import Command


class CoreModuleException(Exception):
    pass


class BaseCommand(Command):
    re_match = None

    def __init__(self, enactor, match_obj, group):
        super().__init__(enactor, match_obj, group)
        self.net = self.app.services["net"]
        self.game = self.app.services["game"]

    @classmethod
    def match(cls, enactor, text):
        if (result := cls.re_match.fullmatch(text)):
            return result

    def execute(self):
        try:
            self.do_execute()
        except CoreModuleException as e:
            self.msg(text=str(e))

    def do_execute(self):
        pass
