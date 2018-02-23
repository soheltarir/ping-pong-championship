from referee import PlayerAlreadyJoined
from utils import RedisConnection, Settings

REDIS_CONN = RedisConnection()
settings = Settings()


class Player:
    def __init__(self, id, name, defense_set, port, host="http://localhost"):
        self.id = id
        self.name = name
        self.defense_set = defense_set
        self.port = port
        self.host = host
        self.current_game_id = None

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<Player: {0}>".format(self.name)

    def set_current_game(self, game_id):
        self.current_game_id = game_id


class Competition:
    def __init__(self):
        self.players = list()

    @property
    def cache_key(self):
        return "competition"

    def add_player(self, player: Player):
        try:
            self.players.index(player)
            raise PlayerAlreadyJoined
        except ValueError:
            self.players.append(player)
        REDIS_CONN.set(self.cache_key, self)

    def pop_player(self):
        player = self.players.pop(0)
        REDIS_CONN.set(self.cache_key, self)
        return player

    def remove_player(self, player: Player):
        value = REDIS_CONN.get(self.cache_key)
        value.players.remove(player)
        REDIS_CONN.set(self.cache_key, value)
        return player

    @classmethod
    def get(cls):
        try:
            value = REDIS_CONN.get("competition")
        except LookupError:
            value = cls()
            REDIS_CONN.set("competition", value)
        return value


class Game:
    def __init__(self, game_id):
        self.id = game_id
        self.status = 0
        self.player1, self.player2 = None, None
        self.scores = {}
        self.winner = None
        self.loser = None

    @property
    def cache_key(self):
        return "{0}_{1}".format(settings.game_cache_key_prefix, self.id)

    def create(self):
        REDIS_CONN.set(self.cache_key, self)

    def add_player(self, player: Player):
        if not self.player1:
            self.player1 = player
        elif not self.player2:
            self.player2 = player
        else:
            raise AssertionError("Already two players added for game {0}".format(self.id))
        REDIS_CONN.set(self.cache_key, self)

    def add_score(self, player: Player):
        if self.scores.get(player.id):
            self.scores[player.id] += 1
        else:
            self.scores[player.id] = 1

    def get_score(self, player: Player):
        return self.scores.get(player.id, 0)

    @classmethod
    def get(cls, game_id):
        cache_key = "{0}_{1}".format(settings.game_cache_key_prefix, game_id)
        value = REDIS_CONN.get(cache_key)
        if not value:
            raise LookupError("No game found with id {0}".format(game_id))
        return value

    def start_game(self):
        self.status = 1
        REDIS_CONN.set(self.cache_key, self)

    def end_game(self):
        self.status = 2
        REDIS_CONN.set(self.cache_key, self)

    def has_finished(self):
        for player_id, value in self.scores.items():
            if value >= 5:
                if self.player1.id == player_id:
                    self.winner = self.player1
                    self.loser = self.player2
                else:
                    self.winner = self.player2
                    self.loser = self.player1
                return True
        return False
