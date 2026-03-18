from fitness.evaluation import evaluate_solution
from opendss.opendss_interface import create_dss, compile_circuit
from config import CONFIG

dss = create_dss()
compile_circuit(dss, CONFIG["circuit_path"])

solution = [500, 1.0]

print(evaluate_solution(dss, solution, CONFIG))