import logging
import pickle

import redis
import sys
import yaml


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

    def get_all(self, pattern):
        keys = self.conn.keys(pattern)
        unpicked_values = []
        for _ in sorted(keys):
            unpicked_values.append(self.get(_))
        return unpicked_values

    def flushdb(self):
        self.conn.flushdb()


class Settings:
    def __init__(self):
        self.file_name = "config.yml"
        fp = open(self.file_name, "r")
        self.data = yaml.load(fp)

    @property
    def referee_host(self):
        return self.data["referee.server.host"]

    @property
    def referee_port(self):
        return self.data["referee.server.port"]

    @property
    def referee_url(self):
        return "http://{0}:{1}".format(self.referee_host, self.referee_port)

    @property
    def player_port_start(self):
        return self.data["player.server.start_port"]

    @property
    def players(self):
        return self.data["players"]

    def get_player(self, player_id):
        for player in self.players:
            if player["id"] == player_id:
                return player
        raise LookupError("No player config with id {0} found.".format(player_id))

    @property
    def total_players(self):
        return self.data["total_players"]

    @property
    def player_cache_key_prefix(self):
        return self.data["player.cache_key_prefix"]

    @property
    def competition_cache_key(self):
        return self.data["competition.cache_key"]

    @property
    def game_cache_key_prefix(self):
        return self.data["games.cache_key_prefix"]


def setup_logging(verbose=0, name=None):
    """Configure console logging. Info and below go to stdout, others go to stderr.

    :param int verbose: Verbosity level. > 0 print debug statements. > 1 passed to sphinx-build.
    :param str name: Which logger name to set handlers to. Used for testing.
    """
    root_logger = logging.getLogger(name)
    root_logger.setLevel(logging.DEBUG if verbose > 0 else logging.INFO)
    formatter = logging.Formatter("%(asctime)s (PID:%(process)s) [%(levelname)s]: %(message)s")

    handler_stdout = logging.StreamHandler(sys.stdout)
    handler_stdout.setFormatter(formatter)
    handler_stdout.setLevel(logging.DEBUG)
    handler_stdout.addFilter(type('', (logging.Filter,), {'filter': staticmethod(lambda r: r.levelno <= logging.INFO)}))
    root_logger.addHandler(handler_stdout)

    handler_stderr = logging.StreamHandler(sys.stderr)
    handler_stderr.setFormatter(formatter)
    handler_stderr.setLevel(logging.WARNING)
    root_logger.addHandler(handler_stderr)
