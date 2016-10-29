import random


def random_ai_player():
    def random_decide(game):
        moves = game.get_possible_moves()
        return random.choice(list(moves))
    return random_decide
