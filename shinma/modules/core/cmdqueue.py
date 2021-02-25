import asyncio
from typing import List
from collections import OrderedDict
from .mush.parser import split_unescaped_text, identify_squares
from .commands.base import CommandException

class CpuTimeExceeded(Exception):
    pass


class ExecFlags:
    QUEUE_DEFAULT = 0x0000
    QUEUE_PLAYER = 0x0001
    QUEUE_OBJECT = 0x0002
    QUEUE_SOCKET = 0x0004
    QUEUE_INPLACE = 0x0008
    QUEUE_NO_BREAKS = 0x0010
    QUEUE_PRESERVE_QREG = 0x0020
    QUEUE_CLEAR_QREG = 0x0040
    QUEUE_NOLIST = 0x0200
    QUEUE_BREAK = 0x0400
    QUEUE_RETRY = 0x800
    QUEUE_DEBUG = 0x1000
    QUEUE_NODEBUG = 0x2000
    QUEUE_PRIORITY = 0x4000
    QUEUE_DEBUG_PRIVS = 0x8000
    QUEUE_EVENT = 0x10000
    QUEUE_RECURSE = (QUEUE_INPLACE | QUEUE_NO_BREAKS | QUEUE_PRESERVE_QREG)

    PE_INFO_DEFAULT = 0x000
    PE_INFO_SHARE = 0x001
    PE_INFO_CLONE = 0x002
    PE_INFO_COPY_ENV = 0x004
    PE_INFO_COPY_QREG = 0x008
    PE_INFO_COPY_CMDS = 0x010


class PeInfo:

    def __init__(self):
        self.fun_invocations = 0
        self.fun_recursions = 0
        self.call_depth = 0
        self.nest_depth = 0
        self.debugging = 0
        self.refcount = 0
        self.debug_strings = None
        self.vars = dict()
        self.cmd_raw = None
        self.cmd_evaled = None
        self.attrname = None


class QueueEntry:

    def __init__(self, enactor: str, executor: str, caller: str, actions: List[str]):
        self.enactor = enactor
        self.executor = executor
        self.caller = caller
        self.actions = actions
        self.semaphore_obj = None
        self.inplace = None
        self.next = None
        self.pid = None
        self.vars = dict()
        self.connection = None
        self.pe_info = None
        self.save_attrname = None


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
                print(f"Oops, CmdQueue encountered: {str(e)}")