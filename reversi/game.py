import enum
from itertools import product


class Player(str, enum.Enum):
    Black = 'b'
    White = 'w'

    @property
    def opposite(self):
        if self == self.Black:
            return self.White
        else:
            return self.Black


class GameEvent(str, enum.Enum):
    PlayerCannotMove = 'on_cant_move'
    NormalMove = 'on_normal_move'
    GameOver = 'on_game_over'
    CellOwnerChange = 'on_cell_change'


class Reversi(object):

    FIELD_SIZE = 8

    def __init__(self, player, field, **callbacks):
        self._player = Player(player)
        self.callbacks = {
            GameEvent(key): val
            for key, val in callbacks.items()
        }

        # validate the field
        field = [
            [
                Player(cell) if cell is not None else None
                for cell in row
            ] for row in field
        ]
        assert len(field) == self.FIELD_SIZE
        assert all(len(row) == self.FIELD_SIZE for row in field)

        self._field = field
        self._possible_moves = None
        self._calculate_possible_moves()

    @classmethod
    def New(cls, **callbacks):
        field = [
            [None for _ in range(cls.FIELD_SIZE)]
            for _ in range(cls.FIELD_SIZE)
        ]
        middle = cls.FIELD_SIZE // 2 - 1
        field[middle][middle] = field[middle+1][middle+1] = Player.Black
        field[middle+1][middle] = field[middle][middle+1] = Player.White
        return cls(Player.Black, field, **callbacks)

    @classmethod
    def Load(cls, game_dump, **callbacks):
        return cls(game_dump['player'], game_dump['field'], **callbacks)

    @classmethod
    def LoadFromText(cls, text_repr, **callbacks):
        lines = list(filter(bool,
                     map(str.strip, text_repr.splitlines())))
        player = Player(lines.pop(0))
        field = []
        for line in lines:
            row = [
                Player(item) if item != '*' else None
                for item in line.split()
            ]
            field.append(row)
        return cls(player, field, **callbacks)

    @property
    def is_game_over(self):
        return not self._possible_moves

    @property
    def current_player(self):
        return self._player

    def iter_cells(self):
        for row_id, row in enumerate(self._field):
            for col_id, cell in enumerate(row):
                yield (row_id, col_id), cell

    def get_scores(self):
        black_cnt, white_cnt = 0, 0
        for pos, cell in self.iter_cells():
            if cell == Player.White:
                white_cnt += 1
            elif cell == Player.Black:
                black_cnt += 1
        return black_cnt, white_cnt

    def __getitem__(self, pos):
        row_id, col_id = pos
        if row_id < 0 or col_id < 0:
            # prevent indexing from end
            # because it gives ability to specify cell in two ways.
            # our semantics: indices should be strictly within [0..8]
            raise IndexError
        return self._field[row_id][col_id]

    def _get(self, position):
        row_id, col_id = position
        try:
            return self[row_id, col_id]
        except IndexError:
            return None

    def get_winner(self):
        if not self.is_game_over:
            return None
        black_cnt, white_cnt = self.get_scores()
        if black_cnt > white_cnt:
            return Player.Black
        elif white_cnt > black_cnt:
            return Player.White

    def _set(self, position, player):
        row_id, col_id = position
        prev_player = self._get(position)
        self._field[row_id][col_id] = player
        self._send_event(GameEvent.CellOwnerChange,
                         row_id, col_id, player, prev_player)

    def _calculate_possible_moves(self, player=None):
        def _pos_add(pos1, delta, coeff=1):
            return pos1[0] + coeff*delta[0], pos1[1] + coeff*delta[1]
        increments = set(product([-1, 0, 1], [-1, 0, 1])) - {(0, 0)}

        player = player or self._player
        result = {}

        for pos, cell in self.iter_cells():
            if cell is not None:
                continue
            total_cells_to_revert = []
            for inc in increments:
                cells_to_revert = []
                step = 0
                while True:
                    step += 1
                    tested_pos = _pos_add(pos, inc, step)
                    cell_state = self._get(tested_pos)
                    if cell_state is None:
                        # we go out from the game field or this cell is empty
                        cells_to_revert.clear()
                        break
                    elif cell_state == player.opposite:
                        # we may revert this cell
                        cells_to_revert.append(tested_pos)
                    else:
                        # this cell is ours,
                        # so we can move from here
                        break
                total_cells_to_revert.extend(cells_to_revert)
            if total_cells_to_revert:
                result[pos] = total_cells_to_revert

        self._possible_moves = result
        return result

    def get_possible_moves(self):
        return set(self._possible_moves.keys())

    def make_move(self, row_id, col_id):
        move_position = row_id, col_id
        if move_position not in self._possible_moves:
            raise InvalidMove
        self._set(move_position, self._player)
        for position in self._possible_moves[move_position]:
            self._set(position, self._player)

        if self._calculate_possible_moves(self._player.opposite):
            self._player = self._player.opposite
            self._send_event(GameEvent.NormalMove, self._player)
        elif self._calculate_possible_moves(self._player):
            self._send_event(GameEvent.PlayerCannotMove,
                             self._player.opposite)
        else:
            self._send_event(GameEvent.GameOver)

    def dump(self):
        return {
            'player': str(self.current_player),
            'field': [
                [str(cell) for cell in row]
                for row in self._field
            ]
        }

    def __str__(self):
        h_border = '{0}{1}{0}'.format(
            self.current_player,
            '-' * (2 * self.FIELD_SIZE + 1)
        )
        lines = [
            '| ' + ' '.join(c or '*' for c in row) + ' |'
            for row in self._field
        ]
        lines.insert(0, h_border)
        lines.append(h_border)
        return '\n'.join(lines)

    def _send_event(self, event, *args, **kwargs):
        if event in self.callbacks:
            self.callbacks[event](*args, **kwargs)


class InvalidMove(Exception):
    pass


def load_from_text_file(filename, **callbacks):
    with open(filename) as f:
        return Reversi.LoadFromText(f.read(), **callbacks)
