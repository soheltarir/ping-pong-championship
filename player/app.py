import json
import random
import sys

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)


def get_player_info(player_id):
    fp = open("config.json")
    settings = json.load(fp)
    if not settings.get(player_id):
        raise KeyError("Player with id {0} not found.".format(player_id))
    return settings[player_id]


@app.route("/attack_value", methods=["GET"])
def get_attack_value():
    return jsonify({"value": random.choice(range(1, 11))})


@app.route("/defend/<player_id>", methods=["POST"])
def can_defend(player_id):
    attack_value = request.get_json()["attack_value"]
    player = get_player_info(player_id)
    if attack_value > player["defense_length"]:
        return app.response_class(status=200)
    else:
        return app.response_class(status=400)


def main(args):
    player_id = args[1]
    player_settings = get_player_info(player_id)
    print("Starting player {0}".format(player_settings["name"]))
    port = "".join(["500", player_id])
    print("Joining the game...")
    player_settings["id"] = player_id
    player_settings["port"] = port
    res = requests.post(url="http://localhost:5000/join", json=player_settings)
    game_id = res.json()["game_id"]
    print("Joined game no. {0}".format(game_id))
    return port


if __name__ == '__main__':
    arguments = sys.argv
    if len(arguments) != 2:
        print("Invalid usage.")
        print("usage: python app.py [player_id]")
        sys.exit(1)

    port = main(arguments)
    app.run(debug=False, port=int(port))
