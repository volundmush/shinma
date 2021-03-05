from . base import MushCommand, CommandException, PythonCommandMatcher, BaseCommandMatcher, Command
from shinma.utils import partial_match
from ..utils import formatter as fmt


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
                loc.render_appearance(self.enactor, internal=True)
            else:
                loc.render_appearance(self.enactor)
        else:
            loc.render_appearance(self.enactor)

    def look_here(self):
        if (loc := self.enactor.relations.get('location')):
            loc.render_appearance(self.enactor, internal=True)
        else:
            raise CommandException("You are nowhere. There's not much to see.")


class MobileCommandMatcher(PythonCommandMatcher):

    def at_cmdmatcher_creation(self):
        self.add(LookCommand)


class ExitCommand(Command):
    name = 'EXIT_CMD'

    def execute(self):
        ex = self.match_obj
        if not (des := ex.relations.get('destination')):
            raise CommandException("Sorry, that's going nowhere fast.")

        out_here = fmt.FormatList(ex)
        out_here.add(fmt.Text(f"{self.enactor.name} heads over to {des.name}."))

        out_there = fmt.FormatList(ex)
        if not (loc := self.enactor.relations.get('location')):
            out_there.add(fmt.Text(f"{self.enactor.name} arrives from somewhere..."))
        else:
            out_there.add(fmt.Text(f"{self.enactor.name} arrives from {loc.name}"))
        des.send(out_there)
        self.enactor.move_to(self.match_obj.relations.get('destination'), look=True)
        loc.send(out_here)


class MobileExitMatcher(BaseCommandMatcher):

    def match(self, enactor, text, obj_chain):
        if not (loc := enactor.relations.get('location')):
            return
        if not (exits := loc.reverse.all('exits')):
            return
        if not (found := partial_match(text, exits, key=lambda x: x.name)):
            return
        cmd = ExitCommand(enactor, found, self, obj_chain)
        return cmd