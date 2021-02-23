#!/usr/bin/env python3.8
import os
import sys
import importlib

import asyncio
import uvloop

from shinma.utils import import_from_module


async def main():
    if (new_cwd := os.environ.get("SHINMA_PROFILE")):
        if not os.path.exists(new_cwd):
            raise ValueError("Improper Shinma profile!")
        os.chdir(os.path.abspath(new_cwd))
        sys.path.insert(0, os.getcwd())

    pidfile = os.path.join('.', 'app.pid')
    with open(pidfile, 'w') as p:
        p.write(str(os.getpid()))

    # Step 1: get settings from profile.
    try:
        settings = importlib.import_module("game_data.settings")
    except Exception:
        raise Exception("Could not import settings!")

    # Step 2: Locate application Core from settings. Instantiate
    # application core and inject settings into it.
    settings.ENGINE.setup()

    # Step 3: Start everything up and run forever.
    await settings.ENGINE.start()
    os.remove(pidfile)


if __name__ == "__main__":
    uvloop.install()
    asyncio.run(main(), debug=True)
