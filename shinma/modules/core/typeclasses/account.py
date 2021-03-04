from . base import BaseTypeClass
from passlib.context import CryptContext
from ..utils.styling import StyleHandler
CRYPT_CON = CryptContext(schemes=['argon2'])
from shinma.utils import lazy_property


class AccountTypeClass(BaseTypeClass):
    typeclass_name = "CoreAccount"
    typeclass_family = 'account'
    prefix = "account"
    class_initial_data = {
        "tags": ["account"]
    }
    command_families = ['account']

    def get_next_cmd_object(self, obj_chain):
        if (conn := obj_chain.get("connection")):
            return conn.relations.get('playview')

    def listeners(self):
        # the listeners of an Account should be all Connections which are
        # logged-in to it at the moment.

        # This shouldn't be used much, though...
        return self.reverse.all('connections')

    def at_login(self, connection):
        pass

    def at_logout(self, connection):
        pass

    def set_password(self, text, nohash=False):
        if not nohash:
            text = CRYPT_CON.hash(text)
        self.attributes.set("core", "password_hash", text)

    def verify_password(self, text):
        pass_hash = self.attributes.get("core", "password_hash")
        if not pass_hash:
            return False
        return CRYPT_CON.verify(text, pass_hash)

    @lazy_property
    def style(self):
        return StyleHandler(self, save=True)
