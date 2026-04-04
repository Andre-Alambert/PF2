from typing import Any, Dict, List, Optional


def decode_solution(solution, config: Dict[str, Any]) -> Dict:
    """
    Converte o vetor do AG em variáveis físicas.

    Estrutura dos genes:
      [P_gen0, P_gen1, ..., P_genN-1, (V_source se config tiver "vsource")]

    Retorna:
      {
        "generators": [{"name": str, "kw": float}, ...],
        "vsource_pu": float | None,
      }
    """
    n_gen = len(config["generators"])
    return {
        "generators": [
            {"name": g["name"], "kw": float(solution[i])}
            for i, g in enumerate(config["generators"])
        ],
        "vsource_pu": float(solution[n_gen]) if "vsource" in config else None,
    }


def get_gene_space(config: Dict[str, Any]) -> List[Dict[str, float]]:
    """
    Espaço dos genes no formato esperado pelo pygad.
    Um gene P por gerador, mais um gene V_source opcional.
    """
    space = [
        {"low": g["pg_min_kw"], "high": g["pg_max_kw"]}
        for g in config["generators"]
    ]
    if "vsource" in config:
        vs = config["vsource"]
        space.append({"low": vs["vg_min_pu"], "high": vs["vg_max_pu"]})
    return space


def get_gene_names(config: Dict[str, Any]) -> List[str]:
    """
    Nomes dos genes para debug/documentação.
    """
    names = [f"{g['name']}_kw" for g in config["generators"]]
    if "vsource" in config:
        names.append(f"{config['vsource']['name']}_pu")
    return names