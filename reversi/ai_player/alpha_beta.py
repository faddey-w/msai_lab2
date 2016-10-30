

def alpha_beta_ai(player, max_depth, estimate_utility, utility,
                  order_moves_traverse=None):
    if callable(max_depth):
        get_max_depth = max_depth
        max_depth = None
    else:
        get_max_depth = None
        # HOF accepts max depth in moves units, that is
        # in pairs of "our move, opponents move"
        # but internal algorithms use half-move units
        # so we double the max depth value
        max_depth *= 2

    def alpha_beta_decide(game):
        if get_max_depth:
            nonlocal max_depth
            max_depth = get_max_depth(game, player)
        _, move = max_value(game, 0, float('-Inf'), float('Inf'))
        return move

    def max_value(game, depth, alpha, beta):
        if game.is_game_over:
            return utility(game, player), None
        if depth >= max_depth:
            return estimate_utility(game, player), None
        best_value, best_move = float('-Inf'), None
        possible_moves = game.get_possible_moves()
        if order_moves_traverse:
            possible_moves = order_moves_traverse(game, possible_moves, player)
        if depth == 0 and len(possible_moves) == 1:
            return None, list(possible_moves)[0]
        for move in possible_moves:
            next_game = game.copy()
            next_game.make_move(*move)
            if next_game.current_player == game.current_player:
                # opponent cannot move, there is MAX move again
                func = max_value
            else:
                func = min_value
            value, _ = func(next_game, depth+1, alpha, beta)
            if value > best_value:
                best_value = value
                best_move = move
            if best_value >= beta:
                return best_value, best_move
            alpha = max(alpha, best_value)
        return best_value, best_move

    def min_value(game, depth, alpha, beta):
        if game.is_game_over:
            return utility(game, player), None
        if depth >= max_depth:
            return estimate_utility(game, player), None
        worst_value, worst_move = float('Inf'), None
        for move in game.get_possible_moves():
            next_game = game.copy()
            next_game.make_move(*move)
            if next_game.current_player == game.current_player:
                # opponent cannot move, there is MIN move again
                func = min_value
            else:
                func = max_value
            value, _ = func(next_game, depth+1, alpha, beta)
            if value < worst_value:
                worst_value = value
                worst_move = move
            if worst_value <= alpha:
                return worst_value, worst_move
            beta = min(beta, worst_value)
        return worst_value, worst_move

    return alpha_beta_decide
