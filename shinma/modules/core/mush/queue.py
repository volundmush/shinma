import asyncio
from collections import OrderedDict


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
        self.entry.execute()
        self.queue.wait_queue.pop(self.pid)


class ActionQueue:
    def __init__(self):
        self.queue = OrderedDict()
        self.wait_queue = dict()
        self.pid = 0

    def push(self, entry):
        self.pid += 1
        self.queue[self.pid] = entry

    def wait(self, entry, duration):
        self.pid += 1
        w = WaitAction(self, self.pid, entry, duration)
        self.wait_queue[self.pid] = w
        w.start()


class QueueEntry:

    def __init__(self, pid: int, enactor: str, executor: str, actions: str):
        self.pid = pid
        self.enactor = enactor
        self.executor = executor
        self.actions = actions


class FunctionCall:

    def __init__(self, enactor: str, executor: str, func):
        self.enactor = enactor
        self.executor = executor
        self.func = func