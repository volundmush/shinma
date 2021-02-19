# Connection details for the Portal.
from collections import defaultdict

PORTAL = "http://127.0.0.1:7998"

# A list of folder names for game modules contained within the profile's modules directory.
MODULES = ["core"]

APPLICATION_CORE = "shinma.core.ApplicationCore"

CLASSES = defaultdict(dict)
CLASSES["services"]["net"] = "shinma.net.service.NetService"
CLASSES["net"]["connection"] = "shinma.net.service.Connection"
CLASSES["net"]["session"] = "shinma.net.service.Session"
CLASSES["net"]["playview"] = "shinma.net.service.PlayView"

CLASSES["services"]["game"] = "shinma.game.service.GameService"
CLASSES["game"]["object"] = "shinma.game.objects.GameObject"
CLASSES["game"]["prototype"] = "shinma.game.objects.GamePrototype"
CLASSES["game"]["attributehandler"] = "shinma.game.objects.AttributeHandler"
CLASSES["game"]["locationhandler"] = "shinma.game.objects.LocationHandler"
CLASSES["game"]["relationhandler"] = "shinma.game.objects.RelationHandler"
CLASSES["game"]["scripthandler"] = "shinma.game.objects.ScriptHandler"
CLASSES["game"]["aclhandler"] = "shinma.game.objects.ACLHandler"
CLASSES["game"]["contentshandler"] = "shinma.game.objects.ContentsHandler"

PROTOTYPES = {
    "connection": "CoreConnection",
    "session": "CoreSession",
    "account": "CoreAccount",
    "playview": "CorePlayView"
}