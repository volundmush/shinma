import asyncio
import re
import sys
from collections import OrderedDict
from .commands.base import CommandException
from .mush.ansi import AnsiString
import traceback


class StackFrame:
    def __init__(self, entry, parent):
        self.parent = parent
        self.entry = entry
        self.enactor = None
        self.spoof = None
        self.executor = None
        self.caller = None
        self.dolist_val = None
        self.iter_val = None
        self.localized = False
        if parent:
            self.vars = parent.vars
        else:
            self.vars = entry.vars

    def localize(self):
        self.localized = True
        # We are localizing this frame, so break the connection to its parent.
        self.vars = dict(self.vars)


class QueueEntry:
    re_func = re.compile(r"^(?P<bangs>!|!!|!\$|!!\$|!\^|!!\^)?(?P<func>\w+)(?P<open>\()")

    def __init__(self, enactor: str, executor: str, caller: str, actions: str, spoof: str = None, split=True):
        self.source = enactor
        self.enactor = enactor
        self.executor = executor
        self.caller = caller
        self.spoof = spoof
        self.actions = actions
        self.semaphore_obj = None
        self.inplace = None
        self.next = None
        self.pid = None
        self.stack = list()
        self.frame = None
        self.cpu_start = None
        self.func_count = 0
        self.cmd = None
        self.vars = dict()
        self.core = None
        self.split_actions = split

    def eval_sub(self, text: str):
        """
        Eventually this will process % and other substitutions.
        """
        if text.startswith('%#'):
            return str(self.enactor), text[2:]
        elif text.startswith('%n'):
            return self.enactor.name, text[2:]
        elif text.startswith('%a'):
            return 'ansi', text[2:]
        else:
            return '', text

    def find_function(self, funcname: str):
        return self.core.functions.get(funcname.lower(), None)

    def evaluate(self, text: str, localize: bool = False, spoof: str = None, called_recursively: bool = False, stop_at=None,
                 recurse=True, substitute=True, functions=True, curly_literals=True, noeval=False):
        if text is None:
            text = ''
        if isinstance(text, AnsiString):
            text = text.clean
        if stop_at is None:
            stop_at = list()
        if isinstance(stop_at, str):
            stop_at = [stop_at]
        if not len(text):
            return AnsiString(""), '', None
        if noeval:
            recurse = False
            substitute = False
            functions = False
            curly_literals = True
        # if cpu exceeded, cancel here.
        # if fil exceeded, cancel here.
        # if recursion limit reached, cancel here.
        if not noeval:
            if self.frame:
                new_frame = StackFrame(self, self.frame)
                self.frame = new_frame
                if localize:
                    new_frame.localize()
                self.stack.append(new_frame)
            else:
                self.frame = StackFrame(self, None)
                self.stack.append(self.frame)
        out = AnsiString()
        remaining = text
        escaped = False
        called_func = False
        stopped = None
        curl_escaped = False

        i = -1

        while i < len(remaining)-1:
            i += 1
            c = remaining[i]

            if escaped:
                out += c
                escaped = False
            else:
                if c == '\\':
                    escaped = True
                elif c == '{' and curly_literals and not curl_escaped:
                    curl_escaped += 1
                elif c == '}' and curly_literals and curl_escaped > 0:
                    curl_escaped -= 1
                elif stop_at and c in stop_at:
                    if curl_escaped:
                        out += c
                    else:
                        remaining = remaining[i+1:]
                        stopped = c
                        break
                elif c == '%' and substitute:
                    subbed, remaining = self.eval_sub(remaining[i:])
                    out += subbed
                    i = -1
                elif c == '[' and recurse:
                    evaled, remaining, stop_char = self.evaluate(remaining[i+1:], called_recursively=True, stop_at=']')
                    i = -1
                    out += evaled
                elif c == '(' and not called_func and functions:
                    out += c
                    if (match := self.re_func.fullmatch(out.clean)):
                        gdict = match.groupdict()
                        if gdict:
                            if (func := self.find_function(gdict["func"])):
                                # hooray we have a function!
                                ready_fun = func(self, remaining[i+1:])
                                ready_fun.execute()
                                called_func = True
                                # the function's output will replace everything that lead up to its calling.
                                out = ready_fun.output
                                remaining = ready_fun.remaining
                                i = -1
                            else:
                                if called_recursively:
                                    # if called recursively, a failed function match should error.
                                    out = AnsiString(f"#-1 FUNCTION ({gdict['func'].upper()}) NOT FOUND")
                                called_func = True
                else:
                    out += c

        # if we reach down here, then we are doing well and can pop a frame off.
        if not noeval:
            self.stack.pop(-1)
            if self.stack:
                self.frame = self.stack[-1]

        # If stopped was never set, then we ended because we reached EOL.
        if stopped is None and remaining:
            remaining = ''

        return out, remaining, stopped

    def process_action(self, enactor, text):
        try:
            cmd = enactor.find_cmd(text)
            if cmd:
                cmd.core = self.core
                self.cmd = cmd
                cmd.entry = self
                try:
                    cmd.at_pre_execute()
                    cmd.execute()
                    cmd.at_post_execute()
                except CommandException as e:
                    cmd.msg(str(e))
                except Exception as e:
                    cmd.msg(text=f"EXCEPTION: {str(e)}")
                    traceback.print_exc(file=sys.stdout)
                self.cmd = None
            else:
                enactor.msg('Huh?  (Type "help" for help.)')
        except Exception as e:
            print(f"Something foofy happened: {e}")
            traceback.print_exc(file=sys.stdout)

    def action_splitter(self, text, split=True):
        if not split:
            yield text
        else:
            remaining = text
            while len(remaining):
                result, remaining, stopped = self.evaluate(remaining, noeval=True, stop_at=[';'])
                if result:
                    yield result

    def execute(self):
        if not (enactor := self.core.objects.get(self.enactor, None)):
            return 0
        if not len(self.actions):
            return 0
        for action in self.action_splitter(self.actions, self.split_actions):
            self.process_action(enactor, action)


class WaitAction:
    def __init__(self, queue, pid, entry, duration):
        self.queue = queue
        self.pid = pid
        self.entry = entry
        self.duration = duration

    def start(self):
        pass

    async def run(self):
        await asyncio.sleep(0.1)
        self.queue.execute(self.entry)
        self.queue.wait_queue.pop(self.pid)


class CmdQueue:
    def __init__(self, core):
        self.core = core
        self.queue_data = OrderedDict()
        self.async_queue = asyncio.Queue()
        self.wait_queue = dict()
        self.pid = 0

    def push(self, entry):
        self.pid += 1
        self.queue_data[self.pid] = entry
        self.async_queue.put_nowait(self.pid)

    def wait(self, entry, duration):
        self.pid += 1
        w = WaitAction(self, self.pid, entry, duration)
        self.wait_queue[self.pid] = w
        w.start()

    async def execute(self, entry, pid):
        entry.pid = pid
        entry.core = self.core
        entry.execute()

    async def start(self):
        while True:
            try:
                pid = await self.async_queue.get()
                if (entry := self.queue_data.pop(pid, None)):
                    await self.execute(entry, pid)
            except Exception as e:
                print(f"Oops, CmdQueue encountered Exception: {str(e)}")