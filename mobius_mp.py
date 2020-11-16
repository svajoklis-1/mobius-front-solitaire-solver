from threading import Thread
import sys
import random
import pyautogui
import time
from multiprocessing import Process, Pipe
import uuid

preferred_window_pos = None
search_depth = 4 # default 4

test_columns_a = [
    'Q 7 3 A 3 3 6 6 9 4 7 A Q',
    '2 5 2 2 0 K J 6 9 7 6 4 4',
    '5 5 9 5 8 3 9 Q K A 8 K 0',
    'J J Q 8 2 7 8 J A 0 K 0 4'
]

test_columns_c = [
    '4 7 A Q',
    '7 6 4 4',
    'A 8 K 0',
    '0 K 0 4'
]

test_columns_b = [
    '2 7',
    'Q 5',
    '5 6',
    '0 6'
]

preferred_cards = None

# -----------------------------------------------------------

def fail(reason):
    print(f'FAIL: {reason}')
    exit(1)

Value = {
    'A': 1,
    '2': 2,
    '3': 3,
    '4': 4,
    '5': 5,
    '6': 6,
    '7': 7,
    '8': 8,
    '9': 9,
    '0': 10,
    'J': 10,
    'Q': 10,
    'K': 10
}

Order = {
    'A': 0,
    '2': 1,
    '3': 2,
    '4': 3,
    '5': 4,
    '6': 5,
    '7': 6,
    '8': 7,
    '9': 8,
    '0': 9,
    'J': 10,
    'Q': 11,
    'K': 12
}

MOVE_PICK = 1
MOVE_NEXT_STACK = 2


def move_str(move):
    if move[0] == MOVE_PICK:
        return f'{move[1] + 1}'
    if move[0] == MOVE_NEXT_STACK:
        return '--'


def cards_equal(cards):
    first_card = cards[0]
    equal = True
    for c in cards:
        equal = equal and c == first_card
    return equal


def card_to_value(card):
    return Order[card]
def cards_are_run(cards):
    sorted_cards = sorted(cards, key=card_to_value)
    prev_order = Order[sorted_cards[0]]
    is_run = True
    for c in sorted_cards[1:]:
        is_run = is_run and (Order[c] == prev_order + 1)
        prev_order = Order[c]
    return is_run


class GameState:
    def __init__(self):
        self._table = [ [], [], [], [] ]
        self._table_depth_left = [ 0, 0, 0, 0 ]
        self._stack = []
        self._stack_value = 0
        self._score = 0
        self._moves = []
        self._id = uuid.uuid1()
        pass


    def copy(self):
        new = GameState()
        new._table = [ c.copy() for c in self._table ]
        new._table_depth_left = self._table_depth_left.copy()
        new._stack = self._stack.copy()
        new._stack_value = self._stack_value
        new._score = self._score
        new._moves = self._moves.copy()
        return new


    '''
        Return valid moves
        Move:
            ('pick', column_index)
    '''
    def moves(self):
        moves = []
        for ci, c in enumerate(self._table):
            if len(c) > 0 and Value[c[-1]] + self._stack_value <= 31:
                moves.append((MOVE_PICK, ci))

        return moves


    def append_stack_card(self, card):
        self._stack.append(card)
        self._stack_value += Value[card]


    def clear_stack(self):
        self._stack = []
        self._stack_value = 0


    '''
        Perform move modifying state
    '''
    def move(self, move):
        if len(move) < 1:
            fail(f'Invalid move: {move}')

        self._moves.append(move)

        if move[0] == MOVE_PICK:
            picked_card = self._table[move[1]][-1]
            if self._stack_value + Value[picked_card] <= 31:
                self._table[move[1]].pop()
                self._table_depth_left[move[1]] -= 1
                self.append_stack_card(picked_card)
                self._add_score()
                if self._stack_value == 31 or len(self.moves()) == 0:
                    self.move((MOVE_NEXT_STACK,))
            else:
                fail('Invalid state, stack higher than 31')
        if move[0] == MOVE_NEXT_STACK:
            self.clear_stack()


    def is_table_empty(self):
        is_empty = True
        for c in self._table:
            is_empty = is_empty and (len(c) == 0)
        return is_empty


    def print(self):
        print('Table:')
        for column in self._table:
            print('[', end='')
            print(' '.join(column), end='')
            print(']')
        print('Stack: [', end='')
        print(' '.join(self._stack), end='')
        print(f'] {self._stack_value}')
        depth_string = ' '.join([str(x) for x in self._table_depth_left])
        print(f'Depths: {depth_string}')

        print(f'Score: {self._score}')
        for move in self._moves:
            print(move_str(move), end=' ')
        print()


    def push_card(self, card):
        self._stack.append(card)
        if self._stack_value > 31:
            fail(f'Stack value over 31 when pushing card ({card})')
        self._add_score()


    def _add_score(self):
        if len(self._stack) == 1 and self._stack[0] == 'J':
            self._score += 2
        elif self._stack_value == 15:
            self._score += 2
        elif self._stack_value == 31:
            self._score += 2

        if len(self._stack) >= 4 and cards_equal(self._stack[-4:]):
            self._score += 12
        elif len(self._stack) >= 3 and cards_equal(self._stack[-3:]):
            self._score += 6
        elif len(self._stack) >= 2 and cards_equal(self._stack[-2:]):
            self._score += 2

        for count in [7, 6, 5, 4, 3]:
            if len(self._stack) >= count and cards_are_run(self._stack[-count:]):
                self._score += count
                break


    '''
        Columns: [string, string, string, string]
    '''
    def load_columns(self, columns):
        if len(columns) != 4:
            fail('Invalid number of columns when loading')
        for column_i, column in enumerate(columns):
            self._table[column_i] = [el for el in column.upper().split(' ') if len(el) > 0]
            # if len(self._table[column_i]) != 13:
            #     fail('Invalid column length when loading')


    def score(self):
        return self._score


    def redepth(self, height):
        for i in range(0, 4):
            self._table_depth_left[i] = min(len(self._table[i]), height)


    def depth_reached(self):
        for i in range(0, 4):
            if self._table_depth_left[i] == 0 and len(self._table[i]) > 0:
                return True
        return False

    # make moves discarding rest of cards on table
    def cleanup(self):
        for i in range(0, 4):
            while len(self._table[i]) > 0:
                self.move((MOVE_PICK, i))
                if (self._stack_value == 31):
                    self.move((MOVE_NEXT_STACK, ))

def read_columns():
    columns = []
    for i in range(0, 4):
        input_text = input(f'Column {i + 1}: ').upper()
        row = ' '.join([x for x in input_text.split(' ') if len(x) > 0])
        columns.append(row)
    return columns

def dive(state):
    if state.depth_reached() or state.is_table_empty():
        return state

    max_state = state
    for move in state.moves():
        next_state = state.copy()
        next_state.move(move)
        dive_state = dive(next_state)
        if dive_state._score > max_state._score:
            max_state = dive_state
    return max_state

def dive_task(conn, max_state):
    max_state = dive(max_state)
    conn.send(max_state)

def calculate():
    global preferred_cards

    s = GameState()
    if preferred_cards == None:
        preferred_cards = read_columns()
    s.load_columns(preferred_cards)

    max_state = s
    try:
        while True:
            max_state.redepth(search_depth)
            threads = []
            for move in max_state.moves():
                next_state = max_state.copy()
                next_state.move(move)
                pconn, cconn = Pipe()
                p = Process(target=dive_task, args=(cconn, next_state))
                threads.append((pconn, p))
                p.start()

            dive_max_state = max_state
            for thread in threads:
                pconn, p = thread
                process_max_state = pconn.recv()
                if process_max_state._score > dive_max_state._score:
                    dive_max_state = process_max_state
                p.join()

            if dive_max_state._id == max_state._id:
                break
            else:
                max_state = dive_max_state
                max_state.print()
    except (KeyboardInterrupt):
        pass

    return max_state

# -----------------------------------------------------------------------
# ----------------------------------------------------------------------- performing
# -----------------------------------------------------------------------

def add_points(a, b):
    return (a[0] + b[0], a[1] + b[1])

def read_window_pos():
    input('Point to top left of window and press enter')
    x, y = pyautogui.position()
    print(f'Captured mouse at ({x}, {y})')
    exit(0)

def click_in_window(point):
    target = add_points(preferred_window_pos, point)
    pyautogui.moveTo(x=target[0], y=target[1])
    pyautogui.mouseDown()
    time.sleep(0.025)
    pyautogui.mouseUp()

def perform_moves(state):
    next_button_point = (430, 349)
    card_voffset = 38
    card_hoffset = 200
    stack_v_offset = 44
    card0_point = (666, 152)
    table_heights = [13, 13, 13, 13]
    stack_height = 0

    click_in_window((0, 0))

    def click_card_point(columni):
        card_x = card0_point[0] + (card_hoffset * columni)
        card_y = card0_point[1] + (card_voffset * (table_heights[columni] - 1))
        card_point = (card_x, card_y)
        click_in_window(card_point)

    def click_next_stack():
        if stack_height < 8:
            next_button_x = next_button_point[0]
            next_button_y = next_button_point[1] + (stack_height - 1) * stack_v_offset
            next_button_target = (next_button_x, next_button_y)
        else:
            next_button_target = (424, 620)

        click_in_window(next_button_target)

    for m in state._moves:
        if m[0] == MOVE_PICK:
            click_card_point(m[1])
            table_heights[m[1]] -= 1
            stack_height += 1
        if m[0] == MOVE_NEXT_STACK:
            click_next_stack()
            stack_height = 0

# -----------------------------------------------------------------------
# ----------------------------------------------------------------------- top-level logic
# -----------------------------------------------------------------------

if not preferred_window_pos:
    read_window_pos()

max_state = calculate() # kill with ^C
max_state.cleanup()

print('Finished search, performing...')
perform_moves(max_state)

