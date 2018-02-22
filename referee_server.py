import multiprocessing
from time import sleep

import atexit
import requests
from flask import Flask, request
from requests.exceptions import ConnectionError as ReqConnError

from referee.exceptions import PlayerAlreadyJoined
from referee.models import Competition, Player, Game
from utils import RedisConnection

app = Flask(__name__)
REDIS_CONN = RedisConnection()
PLAYERS_REQUIRED = 8


def run_game(game: Game):
    print("Started game no. {0}".format(game.id))
    game.create()
    attacker = game.player1
    defender = game.player2
    while True:
        attack_res = requests.get("http://localhost:{0}/attack_value".format(attacker.port))
        defense_res = requests.post("http://localhost:{0}/can_defend/{1}".format(defender.port, defender.id),
                                    json={"attack_value": attack_res.json()["value"]})
        if defense_res.json()["result"] == "WIN":
            game.add_score(attacker)
            print("Attacker ({0}) wins the round.".format(attacker.name))
        else:
            game.add_score(defender)
            print("Defender ({0}) wins the round.".format(defender.name))
            attacker, defender = defender, attacker
        if game.has_finished():
            print("Game no. {0} has finished.".format(game.id))
            break
    print("Winner: {0}".format(game.winner.name))
    # Send kill signal to the loser
    try:
        requests.post("http://localhost:{0}/eliminate/{1}".format(game.loser.port, game.loser.id))
    except ReqConnError:
        print("Player {0} has left the competition".format(game.loser.name))
    game.end_game()
    # Add the winner back in competition
    competition = Competition.get()
    competition.add_player(game.winner)
    return competition


def games():
    print("Started Game Thread")
    while True:
        sleep(10)
        competition = Competition.get()
        if len(competition.players) < PLAYERS_REQUIRED:
            print("Waiting for players to join...")
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
        print(competition.players)
    # Run the last game
    if game.player1 and game.player2:
        run_game(game)
    print("Competition has ended.")


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
        return app.response_class(status=201)
    except PlayerAlreadyJoined:
        return app.response_class(response="Player {0} has already joined.".format(player.id), status=409)


if __name__ == "__main__":
    http_server_process = multiprocessing.Process(target=app.run)
    games_process = multiprocessing.Process(target=games)
    http_server_process.start()
    games_process.start()
    atexit.register(REDIS_CONN.flushdb)
    http_server_process.join()
    games_process.join()
