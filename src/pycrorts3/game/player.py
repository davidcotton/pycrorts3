

class Player:
    def __init__(self, player_id, minerals) -> None:
        super().__init__()
        self.id = int(player_id)
        self.minerals = int(minerals)
