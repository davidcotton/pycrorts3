

class Player:
    def __init__(self, player_id, minerals) -> None:
        super().__init__()
        self.id = int(player_id)
        self.minerals = int(minerals)

    def __repr__(self) -> str:
        return f'Player{self.id}<minerals:{self.minerals}>'

    @staticmethod
    def from_xml(xml):
        return Player(xml['ID'], xml['resources'])
