class PlayersGrid:
    def __init__(self, cell_size=1000):
        self.cell_size = cell_size  # Size of each grid cell
        self.grid = {}  # Dictionary to store players in cells: {(cell_x, cell_y): set(player_ids)}
        self.player_positions = {}  # Cache of player positions: {player_id: (x, y)}

    def get_cell_cords(self, x, y):
        """Convert world coordinates to grid cell coordinates"""
        cell_x = int(x // self.cell_size)
        cell_y = int(y // self.cell_size)
        return cell_x, cell_y

    def add_player(self, player_id, x, y):
        """Add a player to the grid"""
        # Remove from old position if exists
        self.remove_player(player_id)

        # Add to new position
        cell = self.get_cell_cords(x, y)
        if cell not in self.grid:
            self.grid[cell] = set()
        self.grid[cell].add(player_id)
        self.player_positions[player_id] = (x, y)

    def remove_player(self, player_id):
        """Remove a player from the grid"""
        if player_id in self.player_positions:
            old_pos = self.player_positions[player_id]
            old_cell = self.get_cell_cords(*old_pos)
            if old_cell in self.grid:
                self.grid[old_cell].discard(player_id)
                if not self.grid[old_cell]:  # Remove empty cells
                    del self.grid[old_cell]
            del self.player_positions[player_id]

    def get_nearby_players(self, x, y, radius):
        """Get all players within radius of given position"""
        nearby = set()
        cell_x, cell_y = self.get_cell_cords(x, y)
        cells_to_check = radius // self.cell_size + 1

        # Check surrounding cells
        for dx in range(-cells_to_check, cells_to_check + 1):
            for dy in range(-cells_to_check, cells_to_check + 1):
                cell = (cell_x + dx, cell_y + dy)
                if cell in self.grid:
                    for player_id in self.grid[cell]:
                        px, py = self.player_positions[player_id]
                        # Check actual distance
                        if ((px - x) ** 2 + (py - y) ** 2) ** 0.5 <= radius:
                            nearby.add(player_id)
        return nearby