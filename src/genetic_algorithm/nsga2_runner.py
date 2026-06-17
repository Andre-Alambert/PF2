import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import Problem
from pymoo.core.callback import Callback
from pymoo.operators.sampling.rnd import FloatRandomSampling
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.optimize import minimize

from src.genetic_algorithm.encoding import get_gene_space
from src.fitness.evaluation import evaluate_solution
from src.fitness.objective_functions import (
    objective_generation_cost,
    objective_voltage_deviation,
    objective_emissions,
)
from src.fitness.penalties import voltage_penalty


class OPFProblem(Problem):
    def __init__(self, config, dss, v_refs):
        gene_space = get_gene_space(config)
        xl = np.array([g["low"] for g in gene_space])
        xu = np.array([g["high"] for g in gene_space])
        super().__init__(
            n_var=len(gene_space),
            n_obj=3,           # f1=custo, f2=desvio tensão, f3=emissões
            n_ieq_constr=1,    # violação de banda de tensão (g <= 0 = factível)
            xl=xl,
            xu=xu,
        )
        self.config = config
        self.dss = dss
        self.v_refs = v_refs

    def _evaluate(self, X, out, *args, **kwargs):
        F, G = [], []
        for x in X:
            metrics = evaluate_solution(self.dss, x, self.config)
            if not metrics["converged"]:
                F.append([1e6, 1e6, 1e6])
                G.append([1e6])
                continue
            f1 = objective_generation_cost(metrics["generators_dispatched"], self.config["generators"])
            f2 = objective_voltage_deviation(metrics["voltages_pu"], self.v_refs)
            f3 = objective_emissions(metrics["generators_dispatched"], self.config["generators"])
            pen = voltage_penalty(
                metrics["voltages_pu"],
                lower=self.config["voltage_lower_limit"],
                upper=self.config["voltage_upper_limit"],
            )
            F.append([f1, f2, f3])
            G.append([pen])
        out["F"] = np.array(F, dtype=float)
        out["G"] = np.array(G, dtype=float)


class _SilentCallback(Callback):
    def notify(self, algorithm):
        pass


class _ProgressCallback(Callback):
    def notify(self, algorithm):
        gen = algorithm.n_gen
        F = algorithm.pop.get("F")
        feasible = algorithm.pop.get("feasible").flatten()
        if feasible.any():
            Ff = F[feasible]
            print(
                f"  Gen {gen:>3} | "
                f"custo_min={Ff[:, 0].min():>8.1f} $/h | "
                f"vdev_min={Ff[:, 1].min():>6.4f} pu | "
                f"emit_min={Ff[:, 2].min():>6.3f} ton/h | "
                f"factíveis={feasible.sum()}/{len(feasible)}"
            )
        else:
            print(f"  Gen {gen:>3} | nenhuma solução factível")


def run_nsga2(config, dss, v_refs, overrides=None, verbose=True):
    ov = overrides or {}
    pop_size = ov.get("pop_size", config["population_size"])
    num_gen  = ov.get("num_gen",  config["num_generations"])
    sbx_eta  = ov.get("sbx_eta", config.get("sbx_eta", 15))
    pm_eta   = ov.get("pm_eta",  config.get("pm_eta",  20))
    seed     = ov.get("seed",    None)

    problem = OPFProblem(config, dss, v_refs)
    algorithm = NSGA2(
        pop_size=pop_size,
        sampling=FloatRandomSampling(),
        crossover=SBX(prob=0.9, eta=sbx_eta),
        mutation=PM(prob=1.0 / problem.n_var, eta=pm_eta),
        eliminate_duplicates=True,
    )
    res = minimize(
        problem,
        algorithm,
        termination=("n_gen", num_gen),
        callback=_ProgressCallback() if verbose else _SilentCallback(),
        verbose=False,
        seed=seed,
    )
    return res
