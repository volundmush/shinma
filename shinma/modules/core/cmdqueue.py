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
        self.core = None

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

    def find_close_bracket(self, remaining: str):
        print(f"FINDCLOSEBRACK: Searching {remaining}")
        escaped = False
        depth = 0
        for i, c in enumerate(remaining):
            print(f"SEARCH Char {i} - {c}")
            if escaped:
                escaped = False
            else:
                if c == '\\':
                    escaped = True
                elif c == '[':
                    depth += 1
                elif c == ']':
                    if depth == 0:
                        return i
                    else:
                        depth -= 1

    def find_close_paren(self, remaining: str):
        print(f"FINDCLOSEPAREN: Searching {remaining}")
        escaped = False
        depth = 0
        for i, c in enumerate(remaining):
            print(f"SEARCH Char {i} - {c}")
            if escaped:
                escaped = False
            else:
                if c == '\\':
                    escaped = True
                elif c == '(':
                    depth += 1
                elif c == ')':
                    if depth == 0:
                        return i
                    else:
                        depth -= 1

    def find_function(self, funcname: str):
        return self.core.functions.get(funcname.lower(), None)

    def evaluate(self, text: str, localize: bool = False, spoof: str = None, called_recursively: bool = False):
        print(f"EVAL: {text}")
        print(f"CURRENT DEPTH: {len(self.stack)}")
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
        while i < len(remaining)-1:
            i += 1
            c = remaining[i]
            print(f"SCANNING Char {i} - {c}")

            if escaped:
                out += c
                escaped = False
            else:
                if c == '\\':
                    escaped = True
                elif c == '%':
                    print(f"SUB: Detected % at {i}")
                    subbed, remaining = self.eval_sub(remaining[i:])
                    out += subbed
                    i = -1
                elif c == '[':
                    print(f"RECURSE: Detected [ at {i}")
                    closing = self.find_close_bracket(remaining[i+1:])
                    if closing is not None:
                        print(f"RECURSE: Detected ] at {i+1+closing}")
                        section = remaining[i+1:i+1+closing]
                        remaining = remaining[i+closing+2:]
                        i = -1
                        print(f"RECURSE: Recursively evaluating: {section}")
                        out += self.evaluate(section, called_recursively=True)
                        print(f"RECURSE: Remaining to eval: {remaining}")
                elif c == '(' and not called_func:
                    print(f"FUNC: Detected ( at {i}")
                    out += c
                    closing = self.find_close_paren(remaining[i+1:])
                    print(f"FUNC: Closing is {closing}")
                    if closing is not None:
                        args = remaining[i+1:i+1+closing]
                        print(f"FUNC: Detected ) at {i+1+closing}")
                        print(f"THEORETICAL FUNC ARGS: {args}")
                        if (match := self.re_func.fullmatch(out.clean)):
                            gdict = match.groupdict()
                            if gdict:
                                print(f"FUNC: Signature match: {gdict}")
                            if (func := self.find_function(gdict["func"])):
                                print(f"FUNC: Function located: {func}")
                                # hooray we have a function!
                                ready_fun = func(self, args)
                                ready_fun.execute()
                                called_func = True
                                # the function's output will replace everything that lead up to its calling.
                                print(f"FUNC: Returned: {ready_fun.output.clean}")
                                out = ready_fun.output
                                remaining = remaining[i+closing+2:]
                                i = -1
                                print(f"FUNC: Remaining to eval: {remaining}")
                            else:
                                if called_recursively:
                                    print("FUNC: Called Recursively, func not found!")
                                    # if called recursively, a failed function match should error.
                                    out = AnsiString(f"#-1 FUNCTION ({gdict['func'].upper()}) NOT FOUND")
                                    remaining = remaining[i + closing + 2:]
                                    i = -1
                                    print(f"FUNC: Remaining to eval: {remaining}")
                                else:
                                    print(f"FUNC: Not called recursively, no error")
                                    print(f"FUNC: NO function matched...")
                                    # no function matched... don't eval...
                                called_func = True
                    else:
                        # no closing paren... don't eval function...
                        called_func = True
                else:
                    out += c

        # if we reach down here, then we are doing well and can pop a frame off.
        self.stack.pop(-1)
        if self.stack:
            self.frame = self.stack[-1]

        return out

    def execute(self):
        if not (enactor := self.core.objects.get(self.enactor, None)):
            return 0
        actions = list(self.actions)
        if not len(actions):
            return 0
        s = actions.pop(0)

        try:
            while s is not None:
                cmd = enactor.find_cmd(s)
                if cmd:
                    cmd.core = self.core
                    self.cmd = cmd
                    cmd.entry = self
                    cmd.at_pre_execute()
                    try:
                        cmd.execute()
                    except CommandException as e:
                        cmd.msg(str(e))
                    except Exception as e:
                        cmd.msg(text=f"EXCEPTION: {str(e)}")
                        print(f"SOMETHING FOOFY HAPPENED: {str(e)}")
                    cmd.at_post_execute()
                    self.cmd = None
                else:
                    enactor.msg('Huh?  (Type "help" for help.)')

                # need to stick something in here to cover next/include/etc.

                if len(actions):
                    s = actions.pop(0)
                else:
                    break
        except Exception as e:
            print(f"WTF happened? {str(e)}")


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