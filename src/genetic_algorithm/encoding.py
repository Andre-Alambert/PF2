from typing import Dict, List, Any


def decode_solution(solution) -> Dict[str, float]:
    """
    Converte o vetor do AG em variáveis físicas.

    solution = [P_g, V_g]

    P_g -> potência ativa do gerador
    V_g -> tensão da fonte
    """
    return {
        "P_g": float(solution[0]),
        "V_g": float(solution[1]),
    }


def get_gene_space(config: Dict[str, Any]) -> List[Dict[str, float]]:
    """
    Espaço dos genes no formato esperado pelo pygad.
    """
    return [
        {"low": config["pg_min_kw"], "high": config["pg_max_kw"]},
        {"low": config["vg_min_pu"], "high": config["vg_max_pu"]},
    ]


def get_gene_names() -> List[str]:
    """
    Apenas para debug/documentação.
    """
    return ["P_g", "V_g"]