class Player:
    def __init__(self, id, name, defense_set, port, host="http://localhost"):
        self.id = id
        self.name = name
        self.defense_set = defense_set
        self.port = port
        self.host = host

    def __str__(self):
        return self.name
