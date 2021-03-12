from . base import MushCommand, CommandException, PythonCommandMatcher, BaseCommandMatcher, Command
from ..utils import formatter as fmt


class LookCommand(MushCommand):
    name = 'look'
    aliases = ['l', 'lo', 'loo']
    help_category = 'Interaction'

    def execute(self):
        if self.args:
            arg = self.gather_arg()
            if len(arg):
                loc = self.enactor.relations.get('location', None)
                candidates = loc.contents.all() if loc else []
                if (found := self.enactor.search(arg.clean, candidates)):
                    for f in found:
                        self.look_at(f)
                else:
                    raise CommandException("I don't see that here.")
            else:
                self.look_here()
        else:
            self.look_here()

    def look_at(self, target):
        if (loc := self.enactor.relations.get('location', None)):
            if loc == target:
                loc.render_appearance(self.enactor, internal=True)
            else:
                target.render_appearance(self.enactor)
        else:
            target.render_appearance(self.enactor)

    def look_here(self):
        if (loc := self.enactor.relations.get('location', None)):
            loc.render_appearance(self.enactor, internal=True)
        else:
            raise CommandException("You are nowhere. There's not much to see.")


class MobileCommandMatcher(PythonCommandMatcher):
    priority = 10

    def at_cmdmatcher_creation(self):
        self.add(LookCommand)


class ExitCommand(Command):
    name = 'goto'
    help_category = 'Navigation'

    def execute(self):
        ex = self.match_obj
        if not (des := ex.relations.get('destination', None)):
            raise CommandException("Sorry, that's going nowhere fast.")

        out_here = fmt.FormatList(ex)
        out_here.add(fmt.Text(f"{self.enactor.name} heads over to {des.name}."))

        out_there = fmt.FormatList(ex)
        if not (loc := self.enactor.relations.get('location', None)):
            out_there.add(fmt.Text(f"{self.enactor.name} arrives from somewhere..."))
        else:
            out_there.add(fmt.Text(f"{self.enactor.name} arrives from {loc.name}"))
        des.send(out_there)
        self.enactor.move_to(self.match_obj.relations.get('destination'), look=True)
        loc.send(out_here)


class MobileExitMatcher(BaseCommandMatcher):
    priority = 110

    def match(self, enactor, text, obj_chain):
        if not (loc := enactor.relations.get('location', None)):
            return
        if not (exits := [e for e in loc.exits.all() if enactor.can_see(e)]):
            return

        if text.lower().startswith('goto '):
            text = text[5:]
        elif text.lower().startswith('go '):
            text = text[3:]

        if text:
            if not (found := enactor.search(text, exits)):
                return
            cmd = ExitCommand(enactor, found[0], self, obj_chain)
            return cmd

    def populate_help(self, enactor, data):
        data['Navigation'].add(ExitCommand)
