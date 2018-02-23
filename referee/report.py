import csv

from utils import RedisConnection, Settings

REDIS_CONN = RedisConnection()
settings = Settings()


class ExportReport:
    def __init__(self):
        self.file_name = "competition_report.csv"
        self.csvfile = open(self.file_name, "w")
        field_names = ["Game", "Player1", "Player1 Score", "Player2", "Player2 Score", "Winner"]
        self.writer = csv.DictWriter(self.csvfile, fieldnames=field_names)
        self.writer.writeheader()

    @staticmethod
    def get_games():
        return REDIS_CONN.get_all("{0}_*".format(settings.game_cache_key_prefix))

    def generate(self):
        games = self.get_games()
        for game in games:
            data = {
                "Game": game.id,
                "Player1": game.player1.name,
                "Player1 Score": game.get_score(game.player1),
                "Player2": game.player2.name,
                "Player2 Score": game.get_score(game.player2),
                "Winner": game.winner.name
            }
            self.writer.writerow(data)
        self.csvfile.close()
