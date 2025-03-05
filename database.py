
import sqlite3
conn = sqlite3.connect('players.db')

c = conn.cursor()

c.execute("""CREATE TABLE players (
      PlayerID INTEGER PRIMARY KEY,
      PlayerModel TEXT,
      PlayerLifecount INTEGER,
      PlayerMoney INTEGER,
      Playerslot1 INTEGER,
      Playerslot2 INTEGER,
      Playerslot3 INTEGER,
      Playerslot4 INTEGER,
      Playerslot5 INTEGER
    )""")

c.execute("""CREATE TABLE items (
      ItemID INTEGER PRIMARY KEY,
      ItemName TEXT,
      ItemPrice INTEGER
    )""")

