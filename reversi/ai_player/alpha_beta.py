

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
        print('\nИгрок MAX, состояние игры:')
        print(game)
        if game.is_game_over:
            return utility(game, player), []
        if depth >= max_depth_:
            est_util = estimate_utility(game, player)
            print('Оценка полезности:', est_util)
            return est_util, []
        best_value, best_plan = float('-Inf'), None
        possible_moves = game.get_possible_moves()
        if order_moves_traverse:
            possible_moves = order_moves_traverse(game, possible_moves, player)
        for move in possible_moves:
            next_game = game.copy()
            next_game.make_move(*move)
            if next_game.current_player == game.current_player:
                # opponent cannot move, there is MAX move again
                func = max_value
            else:
                func = min_value
            print('Делаем ход', move)
            value, plan = func(next_game, depth+1, alpha, beta, max_depth_)
            print('\nВозвращаемся к игроку MAX, состояние игры:')
            print(game)
            if value > best_value:
                best_value = value
                best_plan = [move] + plan
            if best_value >= beta:
                print('Отсечение! лучшее значение =', best_value, ' beta =', beta)
                print('Куда двигаться из этого положения:', '->'.join(map(str, best_plan)))
                return best_value, best_plan
            if best_value > alpha:
                alpha = best_value
                print('Значение alpha обновлено:', alpha)
        print('После перебора всех вариантов лучшее значение =', best_value)
        print('Куда двигаться из этого положения:', '->'.join(map(str, best_plan)))
        return best_value, best_plan

    def min_value(game, depth, alpha, beta, max_depth_):
        print('\nИгрок MIN, состояние игры:')
        print(game)
        if game.is_game_over:
            return utility(game, player), []
        if depth >= max_depth_:
            est_util = estimate_utility(game, player)
            print('Оценка полезности:', est_util)
            return est_util, []
        worst_value, worst_plan = float('Inf'), None
        possible_moves = game.get_possible_moves()
        if order_moves_traverse:
            possible_moves = order_moves_traverse(game, possible_moves, player)
        for move in possible_moves:
            next_game = game.copy()
            next_game.make_move(*move)
            if next_game.current_player == game.current_player:
                # opponent cannot move, there is MIN move again
                func = min_value
            else:
                func = max_value
            print('Делаем ход', move)
            value, plan = func(next_game, depth+1, alpha, beta, max_depth_)
            print('\nВозвращаемся к игроку MIN, состояние игры:')
            print(game)
            if value < worst_value:
                worst_value = value
                worst_plan = [move] + plan
            if worst_value <= alpha:
                print('Отсечение! худшее значение =', worst_value, ' alpha =', alpha)
                print('Куда двигаться из этого положения:', '->'.join(map(str, worst_plan)))
                return worst_value, worst_plan
            if worst_value < beta:
                beta = worst_value
                print('Значение beta обновлено:', beta)
        print('После перебора всех вариантов худшее значение =', worst_value)
        print('Куда двигаться из этого положения:', '->'.join(map(str, worst_plan)))
        return worst_value, worst_plan

    return alpha_beta_decide
