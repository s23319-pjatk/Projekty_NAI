from easyAI import TwoPlayerGame, Human_Player, AI_Player, Negamax

# Cztery kierunki sprawdzania linii: w prawo, w dół, skoks w dół-prawo, skos w dół-lewo
DIRECTIONS = [(0, 1), (1, 0), (1, 1), (1, -1)]
# Punkty za "okno" 5 pól w zależności od liczby własnych kamyczków (0...5)
WINDOW_SCORES = [0, 1, 10, 100, 1000, 100000]

class Gomoku(TwoPlayerGame):
  """Gracze na zmianę kładą kamień na kwadratowej planszy. Wygrywa ten, kto pierwszy ułoży pięć kamieni w rzędzie."""
  def __init__(self, players=None, size=9):
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

            r, c = self._to_rc(move)
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
            """Gracz, który ma teraz ruch, przegrał, jeśli przeciwnik właśnie ułożył pięć w rzędzie.
            Zwraca:
            bool: True, jeśli przeciwnik ma pięć w rzędzie"""

            return self.has_five(self._opponent())
  def is_draw(self):
            """Sprawdzamy czy plansza jest pełna (remis).
            Zwraca:
            bool: True, jeśli nie ma już wolnych pól"""

            return all(cell != 0 for row in self.board for cell in row)
  def is_over(self):
            """Gra kończy się, gdy ktoś wygra albo plansza jest pełna.
            Zwraca:
            bool: True, jeśli gra jest zakończona"""
            return self.lose() or self.is_draw()

  def show(self):
      """Wypisuje plansze w konsoli"""
      symbols = {0: ".", 1: "X", 2: "0"}
      # Nagłówek z literami kolumn
      print("\n  " + " ".join(chr(65 + c) for c in range(self.size)))
      for r in range(self.size):
          row = " ".join(symbols[v] for v in self. board[r])
          print(f"{r + 1:>3} {row}")
          print()

  def scoring(self):
                """Ocenia pozycję z punktu widzenia gracza, który ma ruch"""


                #Przegrana jest oceniana bardzo nisko
                if self.lose():
                    return -10000
                me, opp = self.current_player, self.opponent()
                n = self.size
                score = 0
                for r in range(n):
                    for c in range(n):
                        for dr, dc in DIRECTIONS:
                            er, ec = r + 4 * dr, c + 4 * dc
                            # Okno musi w całości mieścic się na planszy
                            if not (0 <= er < n and 0 <= ec < n):
                                continue
                            cells = [self.board[r + i * dr][c + i * dc] for i in range(5)]
                            mine, theirs = cells.count(me), cells.count(opp)
                            if theirs == 0:
                                score += WINDOW_SCORES[mine] #Okno "moje"
                            elif mine == 0:
                                score += WINDOW_SCORES[theirs] #Okno "przeciwnika"
                return score
  def _to_str(self, r, c):
                """Zmienia współrzędne na tekst np. (4, 4) -> 'E5'

                Parametry:
                r (int): Indeks wiersza (liczony od 0)
                c (int): Indeks wiersza (liczony od 0)

                Zwraca:
                str: Ruch w postaci litera + numer"""

                return f"{chr(65 + c)}{r + 1}"

  def _to_rc(self,move):
                """Zamienia tekst na współrzędne, np. 'E5' -> (4, 4).

                Paramety:
                move (str): Ruch w postaci litera + numer

                Zwraca:
                tuple[int, int]: (wiersz, kolumna), liczone od 0"""

                return int(move[1:]) -1, ord(move[0].upper()) - 65

if __name__ == "__main__":
    ai = Negamax(3) # AI myśli 3 ruchy do przodu (większa liczba = silniejsze, ale wolniejsze AI
    game = Gomoku([Human_Player(), AI_Player(ai)])
    game.play()
    # Po zakończeniu gry wypisujemy wynik
    if game.is_draw() and not game.lose():
        print("Remis!")
    else:
        print("Wygrywa gracz %d!" % game._opponent())
