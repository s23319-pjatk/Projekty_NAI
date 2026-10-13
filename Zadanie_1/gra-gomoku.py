from easyAI import TwoPlayerGame, Human_Player, AI_Player, Negamax

# Cztery kierunki sprawdzania linii: w prawo, w dół, skoks w dół-prawo, skos w dół-lewo
DIRECTIONS = [(0, 1), (1, 0), (1, 1), (1, -1)]
# Punkty za "okno" 5 pól w zależności od liczby własnych kamyczków (0...5)
WINDOW_SCORES = [0, 1, 10, 100, 1000, 100000]

class Gomoku(TwoPlayerGame):
  """Gracze na zmianę kładą kamień na kwadratowej planszy. Wygrywa ten, kto pierwszy ułoży pięć kamieni w rzędzie."""
    def __init__(self, player=None, size=9):
        """Tworzymy nową gre.

        Parametry:
        Players (list): Dwóch graczy (Human_Player / AI_Player)
        size (int): Rozmiar Planszy (size x size); 9 sprawia, że AI działa szybko
        zwraca:
        None"""

        self.players = players
        self.size = size
        # Plansza: 0 = puste pole, 1= kamien gracza 1 (x), 2 = kamien gracza 2 (0)
        self.board = [[0]* size for _ in range(size)]
        self.current_player = 1 # gracz 1 zaczyna

    def _opponent(self):

        return 3 - self.current_player

    def possible_moves(self):


        n = self.size
        stones = [(r, c) for r in range(n) for c in range(n) if self.board[r][c]]
        if not stones:
            return [self._to_str(r, c) for r in range(n) for c in range(n)]
            moves = set()
            for r, c in stones:
             for dr in range(-2, 3):
                for dc in range(-2, 3):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < n and 0 <= cc < n and self.board[rr][cc] == 0:
                        moves.add((rr, cc))
            return [self._to_str(r, c) for r, c in sorted(moves)]
        def make_move(self, move):
        """Kładzie kamyk aktualnego gracza na planszy.

        Parametry:
        move (str): Ruch w postaci np. 'E5'

        Zwraca:
        None"""

            r, c = self._to_str(move)
            self.board[r][c] = self.current_player

        def has_five(self, player):
            """Sprawdza czy gracz ma piec kamieni w jednej linii.

            Parametry:
            Player (int): Numer gracza (1 lub 2)

            Zwraca:
            bool: True, jesli gracz ułożył pięć w rzędzie"""

            n = self.size
            for r in range(n):
                for c in range(n):
                    if self.board[r][c] != player:
                        continue
                    for dr, dc in DIRECTIONS:
                        if all(
                            0 <= r + i * dr < n
                            and 0 <= c +i * dc < n
                            and self.board[r + i * dr][c + i * dc] == player
                            for i in range(5)
                        ):
                            return True
            return False
        def lose(self):

            return self.has_five(self.opponent())
        def is_draw(self):

            return all(cell != 0 for row in self.board for cell in row)
        def is_over(self):
