from src.config import CONFIG
from src.opendss.opendss_interface import create_dss, compile_circuit
from src.fitness.evaluation import evaluate_solution

dss = create_dss(allow_forms=CONFIG["allow_forms"])
compile_circuit(dss, CONFIG["circuit_path"])

test_solutions = [
    [0.0, 1.00],
    [300.0, 1.00],
    [600.0, 1.00],
    [600.0, 0.98],
    [600.0, 1.02],
]

for sol in test_solutions:
    result = evaluate_solution(dss, sol, CONFIG)
    print(f"Solução: {sol}")
    print(result)
    print("-" * 50)