from easyAI import TwoPlayerGame, Human_Player, AI_Player, Negamax

DIRECTIONS = [(0, 1), (1, 0), (1, 1), (1, -1)]
WINDOW_SCORES = [0, 1, 10, 100, 1000, 100000]

class Gomoku(TwoPlayerGame):

    def __init__(self, player=None, size=9):
        self.players = players
        self.size = size
        self.board = [[0]* size for _ in range(size)]
        self.current_player = 1 # gracz 1 zaczyna

    def _opponent(self):
