import random
from . import heuristics, alpha_beta


__all__ = ['random_ai', 'material_advantage_ai', 'positional_advantage_ai']


def random_ai():
    def random_decide(game):
        moves = game.get_possible_moves()
        return random.choice(list(moves))
    return random_decide


def material_advantage_ai(player, max_depth, weight_ratio):
    return alpha_beta.alpha_beta_ai(
        player,
        max_depth,
        heuristics.material_advantage_estimation(weight_ratio),
        heuristics.win_state_utility,
    )


def positional_advantage_ai(player, max_depth,
                            corner_weight, side_weight, insider_ratio):
    return alpha_beta.alpha_beta_ai(
        player, max_depth,
        heuristics.positional_advantage_estimation(
            corner_weight, side_weight, insider_ratio
        ),
        heuristics.win_state_utility,
    )
