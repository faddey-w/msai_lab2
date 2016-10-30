import random
import time
import multiprocessing
import itertools
from ..game import Reversi, Player


class Score:

    def __init__(self, win_ratio, avg_time, time_dev):
        self.win_ratio = win_ratio
        self.avg_time = avg_time
        self.time_dev = time_dev

    def get_score(self, total_avg_time):
        # For two equally effective algorithms
        # the one with less and more stable timings will be better.
        # Though, influence of good timings must be limited,
        # because it may make fast and stupid algorithm better than smart.
        return self.win_ratio + 0.01 * min(
            self.win_ratio,
            total_avg_time / (self.avg_time + self.time_dev)
        )

    def __str__(self):
        return 'wins={:.2f}, timing={:.2f}±{:.2f}'.format(
            self.win_ratio, self.avg_time, self.time_dev
        )


class BasicIndividual:

    Attrs = ()
    TypeName = ''

    def __init__(self, **attrs):
        self.__dict__.update({
            attr: attrs[attr]
            for attr in self.attrs()
        })

    def attrs(self):
        return self.Attrs

    def type_name(self):
        return self.TypeName

    def mutate(self, **sigmas):
        new_attrs = {
            attr: getattr(self, attr) + random.gauss(0, sigmas.get(attr, 0.2))
            for attr in self.attrs()
        }
        return self.__class__(**new_attrs)

    def crossover(self, other):
        new_attrs = {}
        for attr in self.attrs():
            ratio = random.random()
            new_attrs[attr] = ratio*getattr(self, attr) + (1-ratio)*getattr(other, attr)
        return self.__class__(**new_attrs)

    def __str__(self):
        return _individual2str(self)


class MaterialIndividual(BasicIndividual):

    Attrs = ('weight_ratio',)
    TypeName = 'Material adv.'


class PositionIndividual(BasicIndividual):

    Attrs = ('corner_weight', 'side_weight', 'insider_ratio')
    TypeName = 'Position adv.'


class ConstDepthIndividual(BasicIndividual):

    Attrs = ('max_depth',)
    TypeName = 'const depth'

    def mutate(self, **sigmas):
        result = super(ConstDepthIndividual, self).mutate(**sigmas)
        if result.max_depth < 0.5:
            result.max_depth = 0.5
        elif result.max_depth > 11:
            result.max_depth = 11
        return result


class VariableDepthIndividual(BasicIndividual):

    Attrs = ('mid_max_depth', 'end_max_depth')
    TypeName = 'variable depth'

    def mutate(self, **sigmas):
        result = super(VariableDepthIndividual, self).mutate(**sigmas)
        if result.mid_max_depth < 0.5:
            result.mid_max_depth = 0.5
        elif result.mid_max_depth > 11:
            result.mid_max_depth = 11
        if result.end_max_depth < 0.5:
            result.end_max_depth = 0.5
        elif result.end_max_depth > 11:
            result.end_max_depth = 11
        return result


class CombinedIndividual:

    def __init__(self, ind1, ind2):
        self.ind1 = ind1
        self.ind2 = ind2

    def attrs(self):
        return self.ind1.attrs() + self.ind2.attrs()

    def type_name(self):
        return '{} with {}'.format(self.ind1.type_name(), self.ind2.type_name())

    def mutate(self, **sigmas):
        return self.__class__(self.ind1.mutate(**sigmas),
                              self.ind2.mutate(**sigmas))

    def crossover(self, other):
        return self.__class__(self.ind1.crossover(other.ind1),
                              self.ind2.crossover(other.ind2))

    def __getattr__(self, item):
        if item in self.ind1.attrs():
            return getattr(self.ind1, item)
        if item in self.ind2.attrs():
            return getattr(self.ind2, item)
        raise AttributeError(item)

    def __str__(self):
        return _individual2str(self)


def _individual2str(individual):
    return ', '.join(
        '{}={:.2f}'.format(attr, getattr(individual, attr))
        for attr in individual.attrs()
    )


def run_evolution(population, ai_factories, selection_capacity=None,
                  population_size=None, max_generations=None):
    population_size = population_size or len(population)
    gen_id = 0
    while population:
        gen_id += 1
        population = next_generation(population)
        if selection_capacity and len(population) > selection_capacity:
            population = random.sample(population, selection_capacity)
        total_time_acc = Accumulator()
        total_games = len(population) * (len(population) - 1)
        print(total_games, end=' ', flush=True)
        scores, disqualified = calc_scores(
            population, ai_factories, total_time_acc,
            progress_callback(total_games)
        )
        pop_with_scores = [
            item for idx, item in enumerate(zip(population, scores))
            if idx not in disqualified
        ]
        avg_time = total_time_acc.avg
        pop_with_scores.sort(key=lambda item: item[1].get_score(avg_time), reverse=True)
        pop_with_scores = pop_with_scores[:population_size]
        population, scores = zip(*pop_with_scores)
        print_report(population, scores, gen_id)
        if max_generations and gen_id > max_generations:
            break


def progress_callback(total_games):
    printed = 0

    def callback(games_cnt):
        nonlocal printed
        if games_cnt > printed:
            print('#' * (games_cnt - printed), end='', flush=True)
            printed = games_cnt
    return callback


def next_generation(population):
    type_names = {ind.type_name() for ind in population}
    result = []
    for type_ in type_names:
        subpopulation = [ind for ind in population if ind.type_name() == type_]
        for ind1, ind2 in itertools.product(subpopulation, subpopulation):
            if ind1 is ind2:
                result.append(ind1)
                continue
            child = ind1.crossover(ind2)
            result.append(child)
            result.append(child.mutate())
            result.append(child.mutate())
    return result


def print_report(population, scores, generation_id):
    print()
    print('Generation #{}'.format(generation_id))
    pop_lines = [
        '{}, {}'.format(indiv.type_name(), indiv)
        for indiv in population
    ]
    score_lines = list(map(str, scores))
    for pop_line, score_line in zip(pop_lines, score_lines):
        print('>>> {}: {}'.format(pop_line, score_line))
    print()


def calc_scores(population, ai_factories, total_time_acc, progress_callback):
    pop_size = len(population)
    win_accs = {idx: Accumulator() for idx in range(pop_size)}
    time_accs = {idx: Accumulator() for idx in range(pop_size)}
    disqualified = set()
    games_cnt = 0
    for idx1, indiv1 in enumerate(population):
        if idx1 in disqualified:
            games_cnt += (pop_size - 1)
            continue
        for idx2, indiv2 in enumerate(population):
            games_cnt += 1
            if idx2 in disqualified or idx1 == idx2:
                continue
            track_tuples = {
                Player.Black: [
                    ai_factories[indiv1.type_name()](Player.Black, indiv1),
                    win_accs[idx1], time_accs[idx1]
                ],
                Player.White: [
                    ai_factories[indiv2.type_name()](Player.White, indiv2),
                    win_accs[idx2], time_accs[idx2]
                ],
            }
            try:
                run_game(track_tuples, total_time_acc)
            except Disqualification as disq:
                idx = idx1 if disq.player == Player.Black else idx2
                disqualified.add(idx)
            progress_callback(games_cnt)
    return [
        Score(win_accs[idx].avg, time_accs[idx].avg, time_accs[idx].std_dev)
        for idx in range(pop_size)
    ], disqualified


def run_game(track_tuples, total_time_acc):
    game = Reversi.New()
    while not game.is_game_over:
        ai, _, time_acc = track_tuples[game.current_player]
        result = {}
        worker(ai, game, result)
        if result['time'] > 10:
            raise Disqualification(game.current_player)
        time_acc.add(result['time'])
        total_time_acc.add(result['time'])
        game.make_move(*result['move'])
    winner = game.get_winner()
    for player, (_, win_acc, _) in track_tuples.items():
        win_acc.add(int(player == winner))


class Accumulator:
    def __init__(self):
        self.sum = 0
        self.sqr_sum = 0
        self.count = 0

    def add(self, value):
        self.sum += value
        self.sqr_sum += value ** 2
        self.count += 1

    @property
    def avg(self):
        if self.count == 0:
            return 0
        return self.sum / self.count

    @property
    def std_dev(self):
        if self.count == 0:
            return float('inf')
        return (self.sqr_sum / self.count) - self.avg**2


def worker(ai, game, result):
    start = time.time()
    move = ai(game)
    duration = time.time() - start
    result['move'] = move
    result['time'] = duration


class Disqualification(Exception):
    def __init__(self, player):
        self.player = player
