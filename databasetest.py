import database

players = database.database()
players.createplayer(1)
print(players.getallplayer(0))
players.updateplayer(0, 2, 100, 34, 42, 781, 312, None, None, None)
print(players.getallplayer(0))
players.createplayer(1)
print(players.getallplayer(1))
print(players.getallplayer(0))
