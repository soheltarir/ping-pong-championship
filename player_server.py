import random
import sys

import atexit
import requests
from flask import Flask, jsonify, request

from player import Player
from utils import RedisConnection

app = Flask(__name__)
PORT_PREFIX = "500"
REFEREE_HOST = "http://localhost:5000"
REDIS_CONN = RedisConnection()


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


@app.route("/eliminate/<player_id>", methods=["POST"])
def eliminate(player_id):
    p = REDIS_CONN.get("player_{0}".format(player_id))
    print("Player {0} eliminated, killing the process".format(p))
    sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Invalid usage.")
        print("Usage: python player_server.py [player_id] [player_name] [defense_set]")
        sys.exit(1)
    player = Player(
        id=int(sys.argv[1]),
        name=sys.argv[2],
        defense_set=int(sys.argv[3]),
        port=int("".join([PORT_PREFIX, sys.argv[1]]))
    )
    print("Starting player {0} process.".format(player.id))
    res = requests.post(url="{0}/join".format(REFEREE_HOST), json=player.__dict__)
    if res.status_code != 201:
        print("Not able to join competition. Reason: {0}".format(res.content))
        sys.exit(1)
    print("Joined the competition successfully.")
    # Add player info in redis
    REDIS_CONN.set("player_{0}".format(player.id), player)
    app.run(port=player.port)
