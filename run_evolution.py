from reversi.ai_player import evolution
from reversi import ai_player
import itertools


def make_ai(player, individual):
    if hasattr(individual, 'weight_ratio'):
        return ai_player.material_advantage_ai(
            player,
            max_depth=make_depth(individual),
            weight_ratio=individual.weight_ratio,
        )
    else:
        return ai_player.positional_advantage_ai(
            player,
            max_depth=make_depth(individual),
            corner_weight=individual.corner_weight,
            side_weight=individual.side_weight,
            insider_ratio=individual.insider_ratio
        )


def make_depth(individual):
    if hasattr(individual, 'max_depth'):
        return individual.max_depth
    else:
        return ai_player.max_depth_decision(
            middle=individual.mid_max_depth,
            end=individual.end_max_depth,
        )


material_individuals = [
    evolution.MaterialIndividual(weight_ratio=ratio)
    for ratio in [0.5, 2]
]
position_individuals = [
    evolution.PositionIndividual(
        corner_weight=corner,
        side_weight=side,
        insider_ratio=insider)
    for corner in [4]
    for side in [2]
    for insider in [0]
]
const_depth_individuals = [
    evolution.ConstDepthIndividual(max_depth=depth)
    for depth in [0.5]
]
variable_depth_individuals = [
    evolution.VariableDepthIndividual(mid_max_depth=mid, end_max_depth=end)
    for mid in [0.5, 2]
    for end in [0.5, 9.5]
]


initial_population = [
    evolution.CombinedIndividual(heuristic, depth)
    for heuristic, depth in itertools.product(
        material_individuals + position_individuals,
        const_depth_individuals + variable_depth_individuals,
    )
]
ai_factories = {
    ind.type_name(): make_ai
    for ind in initial_population
}
evolution.run_evolution(
    population=initial_population,
    population_size=10,
    ai_factories=ai_factories,
    max_generations=10,
)
