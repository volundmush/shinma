from . base import BaseTypeClass
from passlib.context import CryptContext

CRYPT_CON = CryptContext(schemes=['argon2'])


class AccountTypeClass(BaseTypeClass):
    typeclass_name = "CoreAccount"
    prefix = "account"
    class_initial_data = {
        "tags": ["account"]
    }
    command_families = ['account']

    def get_next_cmd_object(self, obj_chain):
        if (conn := obj_chain.get("connection")):
            return conn.get_playview()

    def listeners(self):
        # the listeners of an Account should be all Connections which are
        # logged-in to it at the moment.

        # This shouldn't be used much, though...
        return set(self.get_connections())

    def at_login(self, connection):
        pass

    def at_logout(self, connection):
        pass

    def add_connection(self, connection):
        self.relations.set("account_connections", connection, "present", True)

    def remove_connection(self, connection):
        self.relations.delete("account_connections", connection)

    def get_connections(self):
        return self.relations.all("account_connections")

    def set_password(self, text, nohash=False):
        if not nohash:
            text = CRYPT_CON.hash(text)
        self.attributes.set("_core", "password_hash", text)

    def verify_password(self, text):
        pass_hash = self.attributes.get("_core", "password_hash")
        if not pass_hash:
            return False
        return CRYPT_CON.verify(text, pass_hash.value)