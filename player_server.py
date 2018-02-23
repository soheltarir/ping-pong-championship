import os
import random
import signal
import sys

import requests
from flask import Flask, jsonify, request, logging

from player import Player
from utils import RedisConnection, Settings, setup_logging

# Initialise Flask
app = Flask(__name__)
flask_log = logging.getLogger('werkzeug')
flask_log.setLevel(logging.ERROR)

# Get Settings
settings = Settings()
# Get Redis Connection
REDIS_CONN = RedisConnection()

# Current Process Logging settings
setup_logging(name="player")
log = logging.getLogger("player")


@app.route("/attack_value", methods=["GET"])
def get_attack_value():
    """
    Returns a random value from 1 to 10
    :return: Response [200]
    """
    return jsonify({"value": random.choice(range(1, 11))})


@app.route("/can_defend/<player_id>", methods=["POST"])
def can_defend(player_id):
    if request.get_json().get("attack_value"):
        attack_value = request.get_json()["attack_value"]
    else:
        return app.response_class(response="Missing attack_value in body", status=400)
    defender = REDIS_CONN.get("player_{0}".format(player_id))
    if attack_value > defender.defense_set:
        data = {"result": "WIN"}
    else:
        data = {"result": "LOSS"}
    return jsonify(data)


@app.route("/game_info/<player_id>", methods=["POST"])
def receive_game_info(player_id):
    p = REDIS_CONN.get("player_{0}".format(player_id))
    body = request.get_json()
    if body["status"] == 1:
        # Game has started
        if body["attacker_id"] == p.id:
            log.info("{0} has started playing Game (ID: {1}) and is the attacker".format(p.name, body["game_id"]))
        else:
            log.info("{0} has started playing Game (ID: {1}) and is the defender".format(p.name, body["game_id"]))
        return app.response_class(status=200)
    elif body["status"] == 2 and body["winner_id"] == p.id:
        log.info("{0} has won the Game (ID: {1})".format(p.name, body["game_id"]))
        return app.response_class(status=200)
    elif body["status"] == 2 and body["winner_id"] != p.id:
        log.info("{0} has lost the Game (ID: {1})".format(p.name, body["game_id"]))
        log.warning("Killing the player process.")
        os.kill(os.getpid(), signal.SIGTERM)
    else:
        log.error("Invalid request received.")


def main(player_id):
    config = settings.get_player(player_id)
    player = Player(
        id=player_id,
        name=config["name"],
        defense_set=config["defense"],
        port=settings.player_port_start + (player_id - 1)
    )
    log.info("Starting player {0} process.".format(player.id))
    res = requests.post(url="{0}/join".format(settings.referee_url), json=player.__dict__)
    if res.status_code != 201:
        log.error("Not able to join competition. Reason: {0}".format(res.content))
        sys.exit(1)
    log.info("Joined the competition successfully.")
    # Add player info in redis
    REDIS_CONN.set("player_{0}".format(player.id), player)
    app.run(port=player.port)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Invalid usage.")
        print("Usage: python player_server.py [player_id]")
        sys.exit(1)
    main(int(sys.argv[1]))
