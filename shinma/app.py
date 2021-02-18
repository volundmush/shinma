#!/usr/bin/env python3.8
import os
import sys
import importlib

import asyncio
import uvloop

from shinma.utils.misc import import_from_module


def handle_exception(loop, context):
    print("HANDLING EXCEPTION")
    print(loop)
    print(context)


if __name__ == "__main__":
    if (new_cwd := os.environ.get("SHINMA_PROFILE")):
        if not os.path.exists(new_cwd):
            raise ValueError("Improper Shinma profile!")
        os.chdir(os.path.abspath(new_cwd))
        sys.path.insert(0, os.getcwd())

    pidfile = os.path.join('.', 'app.pid')
    with open(pidfile, 'w') as p:
        p.write(str(os.getpid()))

    loop = uvloop.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.set_debug(True)
    loop.set_exception_handler(handle_exception)

    # Step 1: get settings from profile.
    try:
        settings = importlib.import_module("game_data.settings")
    except Exception:
        raise Exception("Could not import settings!")

    # Step 2: Locate application Core from settings. Instantiate
    # application core and inject settings into it.
    core_class = import_from_module(settings.APPLICATION_CORE)
    app_core = core_class(settings, loop)

    # Step 3: Load application from core.
    #app_core.setup()

    # Step 4: Start everything up and run forever.
    asyncio.run(app_core.start(), debug=True)
    os.remove(pidfile)
