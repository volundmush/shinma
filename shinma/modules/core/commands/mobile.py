from . base import MushCommand, CommandException, PythonCommandMatcher


class LookCommand(MushCommand):
    name = 'look'
    aliases = ['l', 'lo', 'loo']

    def execute(self):
        if self.args:
            arg = self.gather_arg()
            if len(arg):
                if (found := self.enactor.locate(arg)):
                    self.look_at(found)
                else:
                    raise CommandException("I don't see that here.")
            else:
                self.look_here()
        else:
            self.look_here()

    def look_at(self, target):
        if (loc := self.enactor.relations.get('location')):
            if loc == target:
                loc.render_appearance(self, self.enactor, internal=True)
            else:
                loc.render_appearance(self, self.enactor)
        else:
            loc.render_appearance(self, self.enactor)

    def look_here(self):
        if (loc := self.enactor.relations.get('location')):
            loc.render_appearance(self, self.enactor, internal=True)
        else:
            raise CommandException("You are nowhere. There's not much to see.")


class MobileCommandMatcher(PythonCommandMatcher):

    def at_cmdmatcher_creation(self):
        self.add(LookCommand)
