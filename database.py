
import sqlite3
conn = sqlite3.connect('players.db')

c = conn.cursor()

c.execute("""CREATE TABLE players (

          PlayerDict = {PlayerID: {PlayerModel: null, PlayerLifecount: null,
                        PlayerMoney INTEGER: null, Playerslot1 INTEGER: null,
                        Playerslot2 INTEGER: null, Playerslot3 INTEGER: null,
                        Playerslot4 INTEGER: null, Playerslot5 INTEGER: null}}
          
          Item dict = {ItemID INTEGER: {ItemName TEXT: null, ItemPrice INTEGER: null}}
        )""")

