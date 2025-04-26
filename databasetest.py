import database

table = database.database()
table.createplayer(1, "testuser", "testpassword")

print(table.getallplayer(0))