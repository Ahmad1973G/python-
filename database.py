import sqlite3


class database:

    def __init__(self):

        self.conn = sqlite3.connect('players.db')
        self.c = self.conn.cursor()

        self.id = 0

        self.c.execute("""CREATE TABLE IF NOT EXISTS players (
      PlayerID INTEGER,
      Username TEXT,
      Password TEXT,
      PlayerModel INTEGER,
      PlayerLifecount INTEGER,
      PlayerMoney INTEGER,
      Playerammo INTEGER,
      Playerslot1 INTEGER,
      Playerslot2 INTEGER,
      Playerslot3 INTEGER,
      Playerslot4 INTEGER,
      Playerslot5 INTEGER
    )""")

    def getallplayer(self, Username):
        self.c.execute("SELECT * FROM players WHERE Username = ?", (Username,))

        # Get column names
        column_names = [description[0] for description in self.c.description]

        # Fetch rows
        rows = self.c.fetchall()

        # Convert to dictionary
        if rows:
            if len(rows) == 1:
                # Return single row as dict
                return dict(zip(column_names, rows[0]))
            else:
                # Return multiple rows as list of dicts
                return [dict(zip(column_names, row)) for row in rows]

        return None

    def createplayer(self, PlayerModel, Username, Password):
        try:
            self.c.execute(
                "INSERT INTO players (PlayerID, Username, Password, PlayerModel, PlayerLifecount, PlayerMoney, Playerammo, Playerslot1, Playerslot2, Playerslot3, Playerslot4, Playerslot5) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (self.id, Username, Password, PlayerModel, 100, 0, 0, 0, 0, 0, 0, 0)
            )
            self.conn.commit()  # Add commit here
            self.id += 1
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False

    def updateplayer(self, PlayerID, PlayerModel, PlayerLifecount, PlayerMoney, Playerammo, Playerslot1, Playerslot2,
                     Playerslot3, Playerslot4, Playerslot5):
        self.c.execute(
            "UPDATE players SET PlayerModel = ?, PlayerLifecount = ?, PlayerMoney = ?, Playerammo = ?, Playerslot1 = ?, Playerslot2 = ?, Playerslot3 = ?, Playerslot4 = ?, Playerslot5 = ? WHERE PlayerID = ?",
            (PlayerModel, PlayerLifecount, PlayerMoney, Playerammo, Playerslot1, Playerslot2, Playerslot3, Playerslot4,
             Playerslot5, PlayerID))

        self.conn.commit()  # Add commit here


    def deleteplayer(self, PlayerID):
        self.c.execute("DELETE FROM players WHERE PlayerID = ?", (PlayerID,))

    def updateplayermodel(self, PlayerID, PlayerModel):
        self.c.execute("UPDATE players SET PlayerModel = ? WHERE PlayerID = ?", (PlayerModel, PlayerID))

    def getplayermodel(self, PlayerID):
        self.c.execute("SELECT PlayerModel FROM players WHERE PlayerID = ?", (PlayerID,))

        return (self.c.fetchall())

    def updateplayerlifecount(self, PlayerID, PlayerLifecount):
        self.c.execute("UPDATE players SET PlayerLifecount = ? WHERE PlayerID = ?", (PlayerLifecount, PlayerID))

    def getplayerlifecount(self, PlayerID):
        self.c.execute("SELECT PlayerLifecount FROM players WHERE PlayerID = ?", (PlayerID,))

        return (self.c.fetchall())

    def updateplayermoney(self, PlayerID, PlayerMoney):
        self.c.execute("UPDATE players SET PlayerMoney = ? WHERE PlayerID = ?", (PlayerMoney, PlayerID))

    def getplayermoney(self, PlayerID):
        self.c.execute("SELECT PlayerMoney FROM players WHERE PlayerID = ?", (PlayerID,))

        return (self.c.fetchall())

    def updateplayerslot1(self, PlayerID, Playerslot1):
        self.c.execute("UPDATE players SET Playerslot1 = ? WHERE PlayerID = ?", (Playerslot1, PlayerID))

    def getplayerslot1(self, PlayerID):
        self.c.execute("SELECT Playerslot1 FROM players WHERE PlayerID = ?", (PlayerID,))
        return (self.c.fetchall())

    def updateplayerslot2(self, PlayerID, Playerslot2):
        self.c.execute("UPDATE players SET Playerslot2 = ? WHERE PlayerID = ?", (Playerslot2, PlayerID))

    def getplayerslot2(self, PlayerID):
        self.c.execute("SELECT Playerslot2 FROM players WHERE PlayerID = ?", (PlayerID,))
        return (self.c.fetchall())

    def updateplayerslot3(self, PlayerID, Playerslot3):
        self.c.execute("UPDATE players SET Playerslot3 = ? WHERE PlayerID = ?", (Playerslot3, PlayerID))

    def getplayerslot3(self, PlayerID):
        self.c.execute("SELECT Playerslot3 FROM players WHERE PlayerID = ?", (PlayerID,))
        return (self.c.fetchall())

    def updateplayerslot4(self, PlayerID, Playerslot4):
        self.c.execute("UPDATE players SET Playerslot4 = ? WHERE PlayerID = ?", (Playerslot4, PlayerID))

    def getplayerslot4(self, PlayerID):
        self.c.execute("SELECT Playerslot4 FROM players WHERE PlayerID = ?", (PlayerID,))
        return (self.c.fetchall())

    def updateplayerslot5(self, PlayerID, Playerslot5):
        self.c.execute("UPDATE players SET Playerslot5 = ? WHERE PlayerID = ?", (Playerslot5, PlayerID))

    def getplayerslot5(self, PlayerID):
        self.c.execute("SELECT Playerslot5 FROM players WHERE PlayerID = ?", (PlayerID,))
        return (self.c.fetchall())

    def getplayerslots(self, PlayerID):
        self.c.execute(
            "SELECT Playerslot1, Playerslot2, Playerslot3, Playerslot4, Playerslot5 FROM players WHERE PlayerID = ?",
            (PlayerID,))

        return (self.c.fetchall())

    def updateplayerslots(self, PlayerID, Playerslot1, Playerslot2, Playerslot3, Playerslot4, Playerslot5):
        self.c.execute(
            "UPDATE players SET Playerslot1 = ?, Playerslot2 = ?, Playerslot3 = ?, Playerslot4 = ?, Playerslot5 = ? WHERE PlayerID = ?",
            (Playerslot1, Playerslot2, Playerslot3, Playerslot4, Playerslot5, PlayerID))

    def updateplayerammo(self, PlayerID, Playerammo):
        self.c.execute("UPDATE players SET Playerammo = ? WHERE PlayerID = ?", (Playerammo, PlayerID))

    def getplayerammo(self, PlayerID):
        self.c.execute("SELECT Playerammo FROM players WHERE PlayerID = ?", (PlayerID,))
        return self.c.fetchall()

    def updateplayerusername(self, PlayerID, Username):
        self.c.execute("UPDATE players SET Username = ? WHERE PlayerID = ?", (Username, PlayerID))

    def getplayerusername(self, PlayerID):
        self.c.execute("SELECT Username FROM players WHERE PlayerID = ?", (PlayerID,))
        return self.c.fetchall()

    def updateplayerpassword(self, PlayerID, Password):
        self.c.execute("UPDATE players SET Password = ? WHERE PlayerID = ?", (Password, PlayerID))

    def getplayerpassword(self, PlayerID):
        self.c.execute("SELECT Password FROM players WHERE PlayerID = ?", (PlayerID,))
        return self.c.fetchall()

    def getplayerid(self, Username):
        self.c.execute("SELECT PlayerID FROM players WHERE Username = ?", (Username,))
        return self.c.fetchall()

    def login(self, Username, Password):
        self.c.execute("SELECT Password FROM players WHERE Username = ?", (Username,))
        result = self.c.fetchone()
        if result is None:
            return "Username not found"
        if result[0] == Password:
            return True
        return False

    def getusernames(self):
        self.c.execute("SELECT Username FROM players")
        return self.c.fetchall()

    def getpasswords(self):
        self.c.execute("SELECT Password FROM players")
        return self.c.fetchall()

    def getusernamesandpasswords(self):
        self.c.execute("SELECT Username, Password FROM players")
        return self.c.fetchall()

    def user_exists(self, Username):
        self.c.execute("SELECT * FROM players WHERE Username = ?", (Username,))
        result = self.c.fetchone()
        if result is None:
            return False
        return True