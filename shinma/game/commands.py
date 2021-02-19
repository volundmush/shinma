from shinma.game.objects import Msg


class Command:
    name = None  # Name must be set to a string!
    app = None

    @classmethod
    def access(cls, enactor):
        """
        This returns true if <enactor> is able to see and use this command.

        Use this for admin permissions locks as well as conditional access, such as
        'is the enactor currently in a certain kind of location'.
        """
        return True

    @classmethod
    def help(cls, enactor):
        """
        This is called by the command-help system if help is called on this command.
        """
        return "Help is not implemented for this command."

    @classmethod
    def match(cls, enactor, text):
        """
        Called by the CommandGroup to determine if this command matches.
        Returns False or a Regex Match object.

        Or any kind of match, really. The parsed match will be returned and re-used by .execute()
        so use whatever you want.
        """
        return False

    def __init__(self, enactor, match_obj, group):
        """
        Instantiates
        """
        self.enactor = enactor
        self.match_obj = match_obj
        self.cmd_group = group

    def execute(self):
        """
        Do whatever the command does.
        """

    def at_pre_execute(self):
        pass

    def at_post_execute(self):
        pass

    def msg(self, **kwargs):
        self.enactor.msg(Msg(self.enactor, **kwargs))


class CommandGroup:
    prototypes = set()
    objects = set()

    def __init__(self, name):
        self.name = name
        self.cmds = set()

    def at_cmdgroup_creation(self):
        """
        This is called when the CommandGroup is instantiated in order to load
        Commands. use self.add(cmdclass) to add Commands.
        """

    def add(self, cmd_class):
        pass

    def match(self, enactor, text):
        for cmd in self.cmds:
            if cmd.access(enactor) and (result := cmd.match(enactor, text)):
                return cmd(enactor, result, self)