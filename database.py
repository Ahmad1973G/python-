
import sqlite3


class database:



  def __init__(self):
      


    self.conn = sqlite3.connect('players.db')
    self.c = self.conn.cursor()
      

    self.id = 0


    self.c.execute("""  CREATE TABLE players (
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
  

   

  def getallplayer(self, PLAYERID):
    self.c.execute("SELECT * FROM players WHERE PlayerID = ?", (PLAYERID,))

    return(self.c.fetchall())

  def createplayer(self, PlayerModel):
    id = self.id
    self.c.execute("INSERT INTO players (PlayerID, PlayerModel, PlayerLifecount, PlayerMoney, Playerslot1, Playerslot2, Playerslot3, Playerslot4, Playerslot5) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (id, PlayerModel, 100, 0, None, None, None, None, None))
    self.id+=1


  def updateplayer(self, PlayerID, PlayerModel, PlayerLifecount, PlayerMoney, Playerslot1, Playerslot2, Playerslot3, Playerslot4, Playerslot5):
    self.c.execute("UPDATE players SET PlayerModel = ?, PlayerLifecount = ?, PlayerMoney = ?, Playerslot1 = ?, Playerslot2 = ?, Playerslot3 = ?, Playerslot4 = ?, Playerslot5 = ? WHERE PlayerID = ?", (PlayerModel, PlayerLifeself.count, PlayerMoney, Playerslot1, Playerslot2, Playerslot3, Playerslot4, Playerslot5, PlayerID))

  def deleteplayer(self, PlayerID):
    self.c.execute("DELETE FROM players WHERE PlayerID = ?", (PlayerID,))

  def updateplayermodel(self, PlayerID, PlayerModel):
    self.c.execute("UPDATE players SET PlayerModel = ? WHERE PlayerID = ?", (PlayerModel, PlayerID))

  def getplayermodel(self, PlayerID):
    self.c.execute("SELECT PlayerModel FROM players WHERE PlayerID = ?", (PlayerID,))

    return(self.c.fetchall())

  def updateplayerlifecount(self, PlayerID, PlayerLifecount):
    self.c.execute("UPDATE players SET PlayerLifecount = ? WHERE PlayerID = ?", (PlayerLifecount, PlayerID))

  def getplayerlifecount(self, PlayerID):
    self.c.execute("SELECT PlayerLifecount FROM players WHERE PlayerID = ?", (PlayerID,))

    return(self.c.fetchall())

  def updateplayermoney(self, PlayerID, PlayerMoney):
    self.c.execute("UPDATE players SET PlayerMoney = ? WHERE PlayerID = ?", (PlayerMoney, PlayerID))

  def getplayermoney(self, PlayerID):
    self.c.execute("SELECT PlayerMoney FROM players WHERE PlayerID = ?", (PlayerID,))

    return(self.c.fetchall())
  
  def updateplayerslot1(self, PlayerID, Playerslot1):
    self.c.execute("UPDATE players SET Playerslot1 = ? WHERE PlayerID = ?", (Playerslot1, PlayerID))

  def getplayerslot1(self, PlayerID):
    self.c.execute("SELECT Playerslot1 FROM players WHERE PlayerID = ?", (PlayerID,))
    return(self.c.fetchall())

  def updateplayerslot2(self, PlayerID, Playerslot2):
    self.c.execute("UPDATE players SET Playerslot2 = ? WHERE PlayerID = ?", (Playerslot2, PlayerID))

  def getplayerslot2(self, PlayerID):
    self.c.execute("SELECT Playerslot2 FROM players WHERE PlayerID = ?", (PlayerID,))
    return(self.c.fetchall())

  def updateplayerslot3(self, PlayerID, Playerslot3):
    self.c.execute("UPDATE players SET Playerslot3 = ? WHERE PlayerID = ?", (Playerslot3, PlayerID))

  def getplayerslot3(self, PlayerID):
    self.c.execute("SELECT Playerslot3 FROM players WHERE PlayerID = ?", (PlayerID,))
    return(self.c.fetchall())

  def updateplayerslot4(self, PlayerID, Playerslot4):
    self.c.execute("UPDATE players SET Playerslot4 = ? WHERE PlayerID = ?", (Playerslot4, PlayerID))

  def getplayerslot4(self, PlayerID):
    self.c.execute("SELECT Playerslot4 FROM players WHERE PlayerID = ?", (PlayerID,))
    return(self.c.fetchall())

  def updateplayerslot5(self, PlayerID, Playerslot5):
    self.c.execute("UPDATE players SET Playerslot5 = ? WHERE PlayerID = ?", (Playerslot5, PlayerID))

  def getplayerslot5(self, PlayerID):
    self.c.execute("SELECT Playerslot5 FROM players WHERE PlayerID = ?", (PlayerID,))
    return(self.c.fetchall())

  def getplayerslots(self, PlayerID):
    self.c.execute("SELECT Playerslot1, Playerslot2, Playerslot3, Playerslot4, Playerslot5 FROM players WHERE PlayerID = ?", (PlayerID,)) 
    return(self.c.fetchall())

  def updateplayerslots(self, PlayerID, Playerslot1, Playerslot2, Playerslot3, Playerslot4, Playerslot5):
    self.c.execute("UPDATE players SET Playerslot1 = ?, Playerslot2 = ?, Playerslot3 = ?, Playerslot4 = ?, Playerslot5 = ? WHERE PlayerID = ?", (Playerslot1, Playerslot2, Playerslot3, Playerslot4, Playerslot5, PlayerID))





