# %%
from ldimbenchmark.methods import LILA, MNF, DUALMethod
from ldimbenchmark import LDIMBenchmark

methods = [MNF(), LILA(), DUALMethod()]

methods = [
    "ghcr.io/ldimbenchmark/test_complexity_constant:0.2.20",
    "ghcr.io/ldimbenchmark/test_complexity_linear:0.2.20",
    "ghcr.io/ldimbenchmark/test_complexity_polynomial:0.2.20",
    "ghcr.io/ldimbenchmark/test_complexity_exponential:0.2.20",
    # "ghcr.io/ldimbenchmark/dualmethod:0.2.2",
    # "ghcr.io/ldimbenchmark/lila:0.2.2",
    # "ghcr.io/ldimbenchmark/mnf:0.2.2",
]


benchmark = LDIMBenchmark(
    {}
    # {"lila": {"default_flow_sensor": "sum"}}
    ,
    [],
    results_dir="./benchmark-results",
)
benchmark.add_local_methods(methods)

benchmark.run_complexity_analysis(
    methods=methods, style="time", n_max=10, n_measures=6, n_repeats=1
)
# benchmark.run_complexity_analysis(6
#     methods=methods, style="junctions", n_max=181, n_measures=10, n_repeats=1
# )

# %%
