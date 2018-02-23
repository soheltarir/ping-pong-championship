import logging
import multiprocessing
from time import sleep

import atexit
import requests
from flask import Flask, request
from requests.exceptions import ConnectionError as ReqConnError

from referee.exceptions import PlayerAlreadyJoined
from referee.models import Competition, Player, Game
from utils import RedisConnection, Settings, setup_logging

# Initialize Flask
app = Flask(__name__)
flask_log = logging.getLogger('werkzeug')
flask_log.setLevel(logging.ERROR)

# Get Redis Connection
REDIS_CONN = RedisConnection()
# Get Config
settings = Settings()

# Setup Process logger
setup_logging(name="referee")
log = logging.getLogger("referee")


def run_game(game: Game):
    log.info("Started game no. {0}".format(game.id))
    game.create()
    attacker = game.player1
    defender = game.player2
    while True:
        attack_res = requests.get("http://localhost:{0}/attack_value".format(attacker.port))
        defense_res = requests.post("http://localhost:{0}/can_defend/{1}".format(defender.port, defender.id),
                                    json={"attack_value": attack_res.json()["value"]})
        if defense_res.json()["result"] == "WIN":
            game.add_score(attacker)
            log.info("Attacker ({0}) wins the round.".format(attacker.name))
        else:
            game.add_score(defender)
            log.info("Defender ({0}) wins the round.".format(defender.name))
            attacker, defender = defender, attacker
        if game.has_finished():
            log.info("Game no. {0} has finished. Winner: {1}".format(game.id, game.winner.name))
            break
    # Send kill signal to the loser
    try:
        requests.post("http://localhost:{0}/eliminate/{1}".format(game.loser.port, game.loser.id))
    except ReqConnError:
        log.info("Player {0} has left the competition".format(game.loser.name))
    game.end_game()
    # Add the winner back in competition
    competition = Competition.get()
    competition.add_player(game.winner)
    return competition


def games():
    log.info("Started Game Thread")
    while True:
        sleep(10)
        competition = Competition.get()
        if len(competition.players) < settings.total_players:
            log.info("{0} out of {1} players have joined, waiting for others.".
                     format(len(competition.players), settings.total_players))
            continue
        break
    # Initialize the 1st game
    game_id = 1
    game = Game(game_id)
    while len(competition.players):
        if game.player1 and game.player2:
            competition = run_game(game)
            # Initialize new game
            game_id += 1
            game = Game(game_id)
        game.add_player(competition.pop_player())
    # Run the last game
    if game.player1 and game.player2:
        run_game(game)
    log.info("Competition has ended, the winner is {0}".format(game.winner.name))


@app.route("/join", methods=["POST"])
def join_competition():
    """
    API to join the ping pong competition
    :return: Response 201
    """
    body = request.get_json()
    player = Player(**body)
    competition = Competition.get()
    try:
        competition.add_player(player)
        log.info("{0} (ID: {1}) has joined the game.".format(player.name, player.id))
        return app.response_class(status=201)
    except PlayerAlreadyJoined:
        return app.response_class(response="Player {0} has already joined.".format(player.id), status=409)


if __name__ == "__main__":
    http_server_process = multiprocessing.Process(target=app.run, kwargs={"port": settings.referee_port})
    games_process = multiprocessing.Process(target=games)
    http_server_process.start()
    games_process.start()
    atexit.register(REDIS_CONN.flushdb)
    http_server_process.join()
    games_process.join()
