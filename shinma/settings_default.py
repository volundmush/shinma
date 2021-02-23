# Connection details for the Portal.
from collections import defaultdict
import sys
from shinma.core import ShinmaEngine

ENGINE = ShinmaEngine()

# A list of folder names for game modules contained within the profile's modules directory.
MODULES = ["net", "gamedb", "core"]