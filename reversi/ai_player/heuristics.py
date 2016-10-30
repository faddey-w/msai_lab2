from collections import Counter
from ..game import Reversi


__all__ = ['win_state_utility', 'material_advantage_estimation',
           'positional_advantage_estimation', 'max_depth_decision']


def max_depth_decision(middle, end):
    def choose_max_depth(game, player):
        num_empty = sum(1 for _, cell in game.iter_cells() if cell is None)
        if num_empty > (NUM_CELLS - 10):
            return 2
        elif num_empty < (NUM_CELLS / 5):
            return end
        else:
            return middle
    return choose_max_depth


def win_state_utility(game, player):
    winner = game.get_winner()
    if player == winner:
        return 1
    elif winner is None:
        return 0
    else:
        return -1


def material_advantage_estimation(weight_ratio):

    def estimate_material_advantage(game, player):
        counts = Counter(cell for _, cell in game.iter_cells())
        total_occupied = counts[player] + counts[player.opponent]
        utility_by_count = 2*counts[player]/total_occupied - 1

        my_moves_cnt = len(game.get_possible_moves(player))
        his_moves_cnt = len(game.get_possible_moves(player.opponent))
        utility_by_moves = 2*(my_moves_cnt / (my_moves_cnt + his_moves_cnt)) - 1

        return weight_ratio * utility_by_count + (weight_ratio - 1) * utility_by_moves

    return estimate_material_advantage


def positional_advantage_estimation(corner_weight, side_weight, insider_ratio):

    def estimate_positional_advantage(game, player):
        num_empty = sum(1 for _, cell in game.iter_cells() if cell is None)
        position_significance = (
            0 if num_empty < NUM_CELLS / 4
            else (4/3) * num_empty / NUM_CELLS - (1/3)
        )
        value = 0
        all_cells_weight = 0
        for position, cell in game.iter_cells():
            if cell is None:
                continue
            opponents_around, total_around = 0, 0
            for pos in _iter_around(position):
                cell_beside = game.get(pos)
                if cell_beside is None:
                    continue
                total_around += 1
                if cell_beside != cell:
                    opponents_around += 1

            if position_significance == 0:
                weight = 1
            else:
                if _is_corner(position):
                    weight = corner_weight
                elif _is_side(position):
                    weight = side_weight
                else:
                    weight = 1
                weight = 1 + position_significance * (weight - 1)
            all_cells_weight += weight
            incr = weight + insider_ratio * opponents_around/total_around
            if cell != player:
                incr = -incr
            value += incr

        return value / (all_cells_weight + insider_ratio*(NUM_CELLS-num_empty))

    return estimate_positional_advantage


def _is_corner(position):
    return (
        position[0] in (0, Reversi.FIELD_SIZE-1)
        and position[1] in (0, Reversi.FIELD_SIZE-1)
    )


def _is_side(position):
    return (
        position[0] in (0, Reversi.FIELD_SIZE - 1)
        or position[1] in (0, Reversi.FIELD_SIZE - 1)
    )


def _iter_around(position):
    for d_row in (-1, 0, 1):
        for d_col in (-1, 0, 1):
            if (d_row, d_col) == (0, 0):
                continue
            yield (position[0]+d_row, position[1]+d_col)


NUM_CELLS = Reversi.FIELD_SIZE * Reversi.FIELD_SIZE
