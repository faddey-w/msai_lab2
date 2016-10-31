

def alpha_beta_ai(player, max_depth, estimate_utility, utility,
                  order_moves_traverse=None):
    if callable(max_depth):
        get_max_depth = max_depth
    else:
        get_max_depth = None

    def alpha_beta_decide(game):
        if get_max_depth:
            max_depth_ = get_max_depth(game, player)
        else:
            max_depth_ = max_depth
        assert max_depth_ > 0
        _, plan = max_value(game, 0, float('-Inf'), float('Inf'), max_depth_)
        return plan

    def max_value(game, depth, alpha, beta, max_depth_):
        if game.is_game_over:
            return utility(game, player), []
        if depth >= max_depth_:
            return estimate_utility(game, player), []
        best_value, best_plan = float('-Inf'), None
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
            value, plan = func(next_game, depth+1, alpha, beta, max_depth_)
            if value > best_value:
                best_value = value
                best_plan = [move] + plan
            if best_value >= beta:
                return best_value, best_plan
            alpha = max(alpha, best_value)
        return best_value, best_plan

    def min_value(game, depth, alpha, beta, max_depth_):
        if game.is_game_over:
            return utility(game, player), None
        if depth >= max_depth_:
            return estimate_utility(game, player), None
        worst_value, worst_plan = float('Inf'), None
        for move in game.get_possible_moves():
            next_game = game.copy()
            next_game.make_move(*move)
            if next_game.current_player == game.current_player:
                # opponent cannot move, there is MIN move again
                func = min_value
            else:
                func = max_value
            value, plan = func(next_game, depth+1, alpha, beta, max_depth_)
            if value < worst_value:
                worst_value = value
                worst_plan = [move] + plan
            if worst_value <= alpha:
                return worst_value, worst_plan
            beta = min(beta, worst_value)
        return worst_value, worst_plan

    return alpha_beta_decide
