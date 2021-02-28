from asyncio import Queue


class CommandException(Exception):
    pass


class Command:
    name = None  # Name must be set to a string!
    re_match = None # this should be a re.compile() pattern

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
        if (result := cls.re_match.fullmatch(text)):
            return result


    def __init__(self, enactor, match_obj, group, obj_chain):
        """
        Instantiates the command.
        """
        self.enactor = enactor
        self.match_obj = match_obj
        self.cmd_group = group
        self.obj_chain = obj_chain
        self.entry = None

    def execute(self):
        """
        Do whatever the command does.
        """

    def at_pre_execute(self):
        pass

    def at_post_execute(self):
        pass

    def msg(self, text=None, **kwargs):
        print(f"{self} is generating message {text} for {self.enactor}")
        self.enactor.msg(text=text, **kwargs)

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"


class BaseCommandMatcher:
    priority = 0
    core = None

    def __init__(self, name):
        self.name = name
        self.at_cmdmatcher_creation()

    @classmethod
    def access(self, enactor):
        return True

    def at_cmdmatcher_creation(self):
        """
        This is called when the CommandGroup is instantiated in order to load
        Commands. use self.add(cmdclass) to add Commands.
        """
        pass

    def match(self, enactor, text, obj_chain):
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"


class PythonCommandMatcher(BaseCommandMatcher):

    def __init__(self, name):
        self.cmds = set()
        super().__init__(name)

    def add(self, cmd_class):
        self.cmds.add(cmd_class)

    def match(self, enactor, text, obj_chain):
        for cmd in self.cmds:
            if cmd.access(enactor) and (result := cmd.match(enactor, text)):
                obj_chain[enactor.typeclass_name] = self
                return cmd(enactor, result, self, obj_chain)
