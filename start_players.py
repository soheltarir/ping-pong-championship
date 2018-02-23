import logging
import multiprocessing

import os
import signal
from time import sleep

import requests
from requests.exceptions import ConnectionError as ReqConnError

from player_server import main
from utils import Settings, setup_logging

# Current Process Logging settings
setup_logging(name="player")
log = logging.getLogger("player")


def ping_referee():
    """
    Function to check the current status of the competition
    """
    while True:
        sleep(10)
        try:
            log.info("Fetching current competition status.")
            res = requests.get("{0}/competition/status".format(settings.referee_url))
            log.info("Current competition status is {0}".format(res.json()["status"]))
            if res.json()["status"] == 2:
                # Exit the parent process
                log.info("Competition has ended, killing the MAIN process")
                os.kill(os.getpgid(os.getpid()), signal.SIGTERM)
        except ReqConnError:
            # Exit the parent process
            log.info("Competition has ended, killing the MAIN process")
            parent_pid = os.getpid()
            os.kill(os.getpgid(os.getpid()), signal.SIGTERM)
            os.kill(parent_pid, signal.SIGTERM)


if __name__ == "__main__":
    settings = Settings()
    processes = []
    for player_cfg in settings.players:
        process = multiprocessing.Process(target=main, args=(player_cfg["id"], ),
                                          name="{0}_process".format(player_cfg["name"].lower()))
        processes.append(process)
    # ping_process = multiprocessing.Process(target=ping_referee)
    for process in processes:
        process.start()
    # ping_process.start()

    for process in processes:
        process.join()
    # ping_process.join()
