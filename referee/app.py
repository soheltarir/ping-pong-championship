import json
import multiprocessing

import redis
import requests
from flask import Flask, request

app = Flask(__name__)
REDIS_CONN = redis.StrictRedis(host="localhost", port=6379, db=0)


def add_value(redis_key, value: dict):
    REDIS_CONN.set(redis_key, json.dumps(value))


def get_value(redis_key):
    value = REDIS_CONN.get(redis_key)
    if value:
        return json.loads(value)
    else:
        return value


def end_game(redis_key):
    value = get_value(redis_key)
    value["status"] = 2
    add_value(redis_key, value)


def add_player_to_game(player, game_id):
    key = game_id
    value = get_value(key)
    if value:
        value["players"].append(player)
    else:
        value = {
            "players": [player],
            "status": 0
        }
    add_value(key, value)


def get_next_game_id():
    games = REDIS_CONN.keys()
    if not len(games):
        return 1
    last_key = sorted(games)[0]
    value = get_value(last_key)
    if len(value["players"]) > 1:
        return last_key + 1
    else:
        return last_key


def get_game_to_run():
    games = REDIS_CONN.keys()
    for game in games:
        value = get_value(game)
        if value["status"] == 0 and len(value["players"]) == 2:
            return game
    return None


def game_thread():
    print("Started Game Thread.")
    while True:
        game_id = get_game_to_run()
        if not game_id:
            continue
        start_game(game_id)


def start_game(game_id):
    print("Started game {0}".format(game_id))
    game_info = get_value(game_id)
    attacker = game_info["players"][0]
    defender = game_info["players"][1]
    scores = {
        attacker["id"]: 0,
        defender["id"]: 0
    }
    winner = None
    while True:
        url = "http://localhost:{0}/attack_value".format(attacker["port"])
        res = requests.get(url=url)
        url = "http://localhost:{0}/defend/{1}".format(defender["port"], defender["id"])
        res = requests.post(url=url, json={"attack_value": res.json()["value"]})
        if res.status_code == 200:
            scores[attacker["id"]] += 1
        else:
            scores[defender["id"]] += 1
            attacker, defender = defender, attacker
        print(scores)
        for player_id, score in scores.items():
            if score == 5:
                winner = player_id
                break
        if winner:
            print("Player {0} has won".format(winner))
            break
    end_game(game_id)


@app.route("/join", methods=["POST"])
def join_competition():
    body = request.get_json()
    print("{0} has joined".format(body["name"]))
    game_id = get_next_game_id()
    add_player_to_game(body, game_id)
    return app.response_class(response=json.dumps({"game_id": str(game_id)}), mimetype="application/json", status=201)


if __name__ == '__main__':
    try:
        app_server_thread = multiprocessing.Process(target=app.run)
        game = multiprocessing.Process(target=game_thread)
        app_server_thread.start()
        game.start()
        app_server_thread.join()
        game.join()
    except KeyboardInterrupt:
        REDIS_CONN.flushdb()
