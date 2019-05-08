

class Player:

    def __init__(self, player_id: int, minerals: int) -> None:
        super().__init__()
        self.id = int(player_id)
        self.minerals = int(minerals)
