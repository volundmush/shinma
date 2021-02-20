# Connection details for the Portal.
from collections import defaultdict

PORTAL = "http://127.0.0.1:7998"

# A list of folder names for game modules contained within the profile's modules directory.
MODULES = ["net", "core"]

APPLICATION_CORE = "shinma.engine.ShinmaEngine"


PROTOTYPES = {
    "connection": "CoreConnection",
    "session": "CoreSession",
    "account": "CoreAccount",
    "playview": "CorePlayView"
}