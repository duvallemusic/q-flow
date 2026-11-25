"""Ponte Jev -> QUBO no exemplo dos dois caminhoes do White Paper.

O Jev le o contexto de cada rota e devolve tres sinais: risco de atraso (noul),
condicao operacional (choice) e dificuldade de acesso (score). O risco vira custo
esperado (probabilidade x multa de atraso) e entra nos termos lineares do QUBO.

Cenario sintetico e ilustrativo: os textos das rotas sao inventados e as
probabilidades do Jev nao foram calibradas com dados reais.
"""

from __future__ import annotations

from itertools import product
from typing import Any

from src.cdc.qubo import QuboModel

# custos base do White Paper (R$): caminhao 1 e 2, rotas A e B
BASE_COSTS_BRL: dict[str, dict[str, float]] = {
    "truck_1": {"A": 300.0, "B": 320.0},
    "truck_2": {"A": 290.0, "B": 310.0},
}
CONGESTION_BOTH_A_BRL = 70.0  # custo extra se os dois caminhoes forem pela rota A
DEFAULT_DELAY_PENALTY_BRL = 500.0  # multa de atraso usada no slide 05 do deck

# contexto de cada rota, no formato de um registro vindo do TMS (dados sinteticos)
ROUTE_STATES: dict[str, dict[str, Any]] = {
    "A": {
        "rota": "A - via serra",
        "distancia_km": 96,
        "trecho_critico": "18 km de serra com aclive médio de 6%",
        "clima_previsto": "chuva forte a partir das 14h, com alerta da Defesa Civil",
        "obras": "pare-e-siga no km 42, espera média de 25 minutos",
        "historico": "lentidão recorrente nesse trecho em dias de chuva",
        "carga_t": 24,
        "saida_prevista": "12h30",
        "janela_entrega": "até 16h no CD de destino",
    },
    "B": {
        "rota": "B - rodovia plana",
        "distancia_km": 118,
        "trecho_critico": "nenhum, pista duplicada e plana",
        "clima_previsto": "tempo seco",
        "obras": "nenhuma registrada",
        "historico": "fluxo normal nesse horário",
        "carga_t": 24,
        "saida_prevista": "12h30",
        "janela_entrega": "até 16h no CD de destino",
    },
}

# as tres perguntas tipadas do Jev (mesmas do slide 05: Choice, Score e Noul)
QUESTIONS: dict[str, dict[str, Any]] = {
    "risco_atraso": {
        "type": "noul",
        "instructions": (
            "Considerando o contexto da rota, o caminhão corre risco relevante "
            "de perder a janela de entrega?"
        ),
        "criteria": {
            "true": (
                "Há fatores concretos que tornam provável perder a janela "
                "(clima, obras, aclive com carga pesada, lentidão recorrente)."
            ),
            "false": "Não há fatores concretos de atraso; a viagem tende a cumprir a janela.",
        },
    },
    "condicao_operacional": {
        "type": "choice",
        "instructions": "Qual é a condição operacional desta rota para a viagem descrita?",
        "criteria": {
            "normal": "Sem restrições relevantes; operação dentro do padrão.",
            "atencao": "Há fatores que pedem cuidado ou podem gerar algum atraso.",
            "critica": "Há fatores graves que colocam a entrega ou a segurança em risco.",
            "indefinida": "O contexto não traz informação suficiente para avaliar.",
        },
    },
    "dificuldade_acesso": {
        "type": "score",
        "instructions": "Qual é a dificuldade de acesso e de tráfego desta rota para um caminhão carregado?",
        "criteria": [
            "Baixa: via plana, bem conservada e com fluxo livre.",
            "Média: alguns trechos lentos ou aclives moderados.",
            "Alta: aclives fortes, obras ou pista em más condições.",
            "Muito alta: trecho perigoso ou quase intransitável para caminhão pesado.",
        ],
    },
}


def route_signals(answers_by_route: dict[str, dict[str, dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    """Resume as respostas do Jev de cada rota nos sinais que a gente usa."""
    signals: dict[str, dict[str, Any]] = {}
    for route in ("A", "B"):
        if route not in answers_by_route:
            raise ValueError(f"faltou a resposta do Jev para a rota {route}")
        ans = answers_by_route[route]
        missing = [q for q in QUESTIONS if q not in ans]
        if missing:
            raise ValueError(f"rota {route}: faltou a resposta de {', '.join(missing)}")
        cond = ans["condicao_operacional"]
        signals[route] = {
            "delay_probability": float(ans["risco_atraso"]["noul"]),
            "condition": cond["choice"],
            "condition_confidence": cond.get("confidence"),
            "access_difficulty_score": float(ans["dificuldade_acesso"]["score"]),
            "access_difficulty_normalized": float(ans["dificuldade_acesso"]["score_normalized"]),
            # regra fixa nossa: condicao critica vai pra revisao humana, o Jev so sinaliza
            "human_review": cond["choice"] == "critica",
        }
    return signals


def route_costs(
    signals: dict[str, dict[str, Any]] | None,
    *,
    delay_penalty_brl: float = DEFAULT_DELAY_PENALTY_BRL,
    base_costs: dict[str, dict[str, float]] | None = None,
) -> dict[str, dict[str, dict[str, float]]]:
    """Custo de cada caminhao em cada rota: base + probabilidade de atraso x multa.

    signals=None monta o caso sem Jev (risco zero), igual ao White Paper.
    """
    if delay_penalty_brl < 0:
        raise ValueError("a multa de atraso nao pode ser negativa")
    base_costs = base_costs or BASE_COSTS_BRL
    costs: dict[str, dict[str, dict[str, float]]] = {}
    for truck, by_route in base_costs.items():
        costs[truck] = {}
        for route, base in by_route.items():
            p = 0.0 if signals is None else float(signals[route]["delay_probability"])
            risk = p * delay_penalty_brl
            costs[truck][route] = {
                "base_brl": float(base),
                "delay_probability": p,
                "risk_cost_brl": risk,
                "total_brl": float(base) + risk,
            }
    return costs


def build_two_truck_qubo(
    costs: dict[str, dict[str, dict[str, float]]],
    *,
    congestion_brl: float = CONGESTION_BOTH_A_BRL,
    instance_id: str = "two_truck_jev",
) -> QuboModel:
    """Monta o QUBO de 2 caminhoes. x=0 e rota A, x=1 e rota B (mesma convencao do White Paper).

    F = a1(1-x1) + b1 x1 + a2(1-x2) + b2 x2 + c(1-x1)(1-x2)
      = (a1 + a2 + c) + (b1 - a1 - c) x1 + (b2 - a2 - c) x2 + c x1 x2
    """
    a1 = costs["truck_1"]["A"]["total_brl"]
    b1 = costs["truck_1"]["B"]["total_brl"]
    a2 = costs["truck_2"]["A"]["total_brl"]
    b2 = costs["truck_2"]["B"]["total_brl"]
    c = float(congestion_brl)

    model = QuboModel(
        n_vars=2,
        linear={0: b1 - a1 - c, 1: b2 - a2 - c},
        quadratic={(0, 1): c},
        offset=a1 + a2 + c,
        variable_names=["x1", "x2"],
        metadata={
            "instance_id": instance_id,
            "currency": "BRL",
            "synthetic": True,
            "description": "Dois caminhoes, rotas A/B, +congestionamento se os dois forem por A; risco do Jev nos termos lineares",
            "encoding": "x=0 -> rota A, x=1 -> rota B",
        },
    )
    values = {"".join(map(str, bits)): model.evaluate(bits) for bits in product([0, 1], repeat=2)}
    best = min(values.values())
    model.metadata["expected_values"] = values
    model.metadata["optimal_bitstrings"] = sorted(b for b, v in values.items() if abs(v - best) < 1e-9)
    return model


def describe_bitstring(bitstring: str) -> str:
    """Traduz '01' para 'caminhao 1 rota A, caminhao 2 rota B'."""
    routes = ["A" if b == "0" else "B" for b in bitstring]
    return ", ".join(f"caminhão {i + 1} rota {r}" for i, r in enumerate(routes))
