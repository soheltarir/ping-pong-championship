import multiprocessing

from player_server import main
from utils import Settings

if __name__ == "__main__":
    settings = Settings()
    processes = []
    for player_cfg in settings.players:
        process = multiprocessing.Process(target=main, args=(player_cfg["id"], ),
                                          name="{0}_process".format(player_cfg["name"].lower()))
        processes.append(process)
    for process in processes:
        process.start()

    for process in processes:
        process.join()
