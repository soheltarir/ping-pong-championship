import pickle

import redis


class RedisConnection:
    def __init__(self):
        self.conn = redis.StrictRedis(host="localhost", port=6379, db=0)

    def get(self, key):
        value = self.conn.get(key)
        if not value:
            raise LookupError("No such key exists.")
        return pickle.loads(value)

    def set(self, key, value):
        self.conn.set(key, pickle.dumps(value))

    def flushdb(self):
        self.conn.flushdb()
