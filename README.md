# mobius-front-solitaire-solver
A solver for Cribbage Solitaire in Möbius Front '83 by Zachtronics

## Usage

- Run game in windowed mode at 1366x768
- Run `python3 mobius_mp.py`. Focus terminal window and press enter when hovering over the top left pixel of the inner game window.
- Copy value (X, Y) to mobius_mp.py:9 `preferred_window_pos = (X, Y)`
- Run `python3 mobius_mp.py` again.
- Enter cards from top to bottom for each column, columns are going from 1 to 4 left to right.
    - Cards are a 2 3 4 5 6 7 8 9 0 j q k, notice 10 is represented as 0
- After solution is found the cards will be clicked automatically.
- For a demo see https://youtu.be/n_rw_X3iZAY