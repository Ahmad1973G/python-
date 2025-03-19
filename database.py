
import sqlite3
conn = sqlite3.connect('players.db')

c = conn.cursor()

c.execute("""CREATE TABLE players (
      PlayerID INTEGER PRIMARY KEY,
      PlayerModel INTEGER,
      PlayerLifecount INTEGER,
      PlayerMoney INTEGER,
      Playerslot1 INTEGER,
      Playerslot2 INTEGER,
      Playerslot3 INTEGER,
      Playerslot4 INTEGER,
      Playerslot5 INTEGER
    )""")

conn.commit()


conn.close()

