import asyncio
import re
from typing import List
from collections import OrderedDict
from .mush.parser import split_unescaped_text, identify_squares
from .commands.base import CommandException
from .mush.ansi import AnsiString


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

    def __init__(self, enactor: str, executor: str, caller: str, actions: List[str], spoof: str = None):
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

    def eval_sub(self, text: str):
        """
        Eventually this will process % and other substitutions.
        """
        return '', text

    def find_unescaped(self, character: str, remaining: str):
        """
        Looks ahead in remaining text to find a closing parentheses, and returns the idx of it.
        """
        escaped = False
        for i, c in enumerate(remaining):
            if escaped:
                escaped = False
            else:
                if c == '\\':
                    escaped = True
                elif c == character:
                    return i
        return None

    def evaluate(self, text: str, localize: bool = False, spoof: str = None):
        if not len(text):
            return AnsiString("")
        # if cpu exceeded, cancel here.
        # if fil exceeded, cancel here.
        # if recursion limit reached, cancel here.

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

        i = -1
        while i <= len(remaining):
            i += 1
            c = remaining[i]

            if escaped:
                out += c
                escaped = False
            else:
                if c == '\\':
                    escaped = True
                elif c == '%':
                    subbed, remaining = self.eval_sub(remaining[i:])
                    if subbed:
                        out += subbed
                elif c == '[':
                    if (closing := self.find_close_bracket(remaining[i:])):
                        section = remaining[i+1:closing-1]
                        remaining = remaining[closing+1:]
                        out += self.evaluate(section)
                elif c == '(' and not called_func:
                    if (closing := self.find_close_paren(remaining[i:])):
                        if (match := self.re_func.fullmatch(out.clean)):
                            gdict = match.groupdict()
                            if (func := self.find_function(gdict["func"])):
                                # hooray we have a function!
                                ready_fun = func(self, remaining[i + 1:])
                                ready_fun.execute()
                                called_func = True
                                # the function's output will replace everything that lead up to its calling.
                                out = ready_fun.output
                            else:
                                # no function matched... don't eval...
                                out += c
                                called_func = True
                    else:
                        # no closing paren... don't eval function...
                        out += c
                        called_func = True
                else:
                    out += c

        # if we reach down here, then we are doing well and can pop a frame off.
        self.stack.pop(-1)
        if self.stack:
            self.frame = self.stack[-1]

        return out


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
        if not (enactor := self.core.objects.get(entry.enactor, None)):
            return 0
        actions = list(entry.actions)

        if not len(actions):
            return 0

        s = actions.pop(0)
        try:
            while s is not None:
                cmd = enactor.find_cmd(s)
                if cmd:
                    cmd.core = self.core
                    cmd.at_pre_execute()
                    try:
                        cmd.execute()
                    except CommandException as e:
                        cmd.msg(str(e))
                    except Exception as e:
                        cmd.msg(text=f"EXCEPTION: {str(e)}")
                        print(f"SOMETHING FOOFY HAPPENED: {str(e)}")
                    cmd.at_post_execute()
                else:
                    enactor.msg('Huh?  (Type "help" for help.)')
                if len(actions):
                    s = actions.pop(0)
                else:
                    break
        except CpuTimeExceeded as e:
            pass
        except Exception as e:
            print(f"WTF happened? {str(e)}")

    async def start(self):
        while True:
            try:
                pid = await self.async_queue.get()
                if (entry := self.queue_data.pop(pid, None)):
                    await self.execute(entry, pid)
            except Exception as e:
                print(f"Oops, CmdQueue encountered Exception: {str(e)}")