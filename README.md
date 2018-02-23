# Ping Pong Championship


## Description
Implement a virtual Ping-Pong championship, which features 8 players and 1 referee 
(all 9 implemented as distinct applications). The 8 players will be instances of the same app, 
with different attributes, defined in an external file

## The championship
The Referee program starts and waits all 8 players to join the championship. When all players have joined, 
the referee draws the 4 initial games and notifies the players about their game id, opponent and their order 
of play (first, second).
All games are knock-out and supervised by the referee. After all 4 games have ended, the referee informs the defeated 
players to shut down, draws the second round (semi finals), informs the players about their new game id and opponents. 
In a similar fashion, the process continues to the final game and cup winner.
## The game
The game starts with the first (offensive) player picking one random number (from 1 to 10) and informing the referee 
about it. The defending player creates a defense array of random numbers (from 1 to 10). The length of the defense array
is preset for each player (see players matrix at the end of this document) and defined in their individual 
configuration files.
If the number picked by the offensive player does not exist in the defense array, then the player gets one point and 
plays again. If it exists, the defender gets the point and they switch roles (defender attacks).
The first player to get 5 points wins the game.

## Requirements
* python 3
* pip
* redis

## Installation
`pip install -r requirments.txt`

## Configuration
The project configuration resides in **config.yml**. Please refer the existing config.yml to get details of the 
individual settings

## Deployment
### Running Referee Server
`python referee_server.py`
This will launch the referee server on the host and port based on the configurations `referee.server.host` and `referee.server.port`.
> Note: The script needs to run from the root directory.

### Running Player Servers
`python start_players.py`
This will launch player processes based on the configuration `players`
> Note: The script needs to run from the root directory.  

## Referee APIs
### Join the Competition
#### URL
`POST /join/`
#### Request Body
```json
{
    "id": "player_id",
    "name": "player_name",
    "defense_set": "defense",
    "port": "port"
}
```

## Player APIs

### Get Attack Points
#### URL
`GET /attack_value/`

### Can Defend the Attack
#### URL
`POST /can_defend/:player_id/`
#### Request Body
```json
{
    "attack_value": 5
}
```

### Receive Game Information
#### URL
`POST /game_info/:player_id/`
#### Request Body
```json
{
    "status": 1,        # 1 if game has started, 2 if game has ended.
    "game_id": 1,
    "attacker_id": 1,   # Sent at the start of the game (status=1) designating who plays first.
    "winner_id": 1      # Sent at the end of the game (status=2) designating who has won the game.
}
```
