"""Testes offline do cenario real v0.2 (OSRM, Open-Meteo, ANP e ANTT).

Usa respostas gravadas em memoria como fixture para nao depender de internet.
Cobre: fluxo completo, fonte fora do ar, JSON quebrado, rota sem alternativa,
preco faltando e integracao com o pipeline.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
import requests

from src.scoring.real_scenario import (
    ANTT_CCD_CARGA_GERAL_BRL_KM,
    RealScenarioError,
    build_real_scenario,
    compute_antt_base_costs,
    fetch_anp_diesel_s10,
    fetch_open_meteo_weather,
    fetch_osrm_routes,
    save_sources,
)

ROOT = Path(__file__).resolve().parents[1]


# ------------------------------------------------------------ fixtures offline


FIXTURE_OSRM_TWO_ROUTES = {
    "code": "Ok",
    "routes": [
        {
            "distance": 71400.0,
            "duration": 4680.0,
            "legs": [{"summary": "Via Anchieta (SP-150)"}],
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [-46.6025, -23.6012],
                    [-46.4810, -23.8120],
                    [-46.3225, -23.9540],
                ],
            },
        },
        {
            "distance": 79800.0,
            "duration": 4320.0,
            "legs": [{"summary": "Rodovia dos Imigrantes (SP-160)"}],
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [-46.6025, -23.6012],
                    [-46.5300, -23.8400],
                    [-46.3225, -23.9540],
                ],
            },
        },
    ],
}

FIXTURE_OPEN_METEO_ROUTE_A = {
    "latitude": -23.8125,
    "longitude": -46.4812,
    "timezone": "America/Sao_Paulo",
    "hourly_units": {"time": "iso8601", "precipitation": "mm", "wind_speed_10m": "km/h"},
    "hourly": {
        "time": ["2026-11-25T13:00", "2026-11-25T14:00", "2026-11-25T15:00"],
        "precipitation": [4.2, 12.6, 8.0],
        "wind_speed_10m": [18.5, 29.4, 22.1],
    },
}

FIXTURE_OPEN_METEO_ROUTE_B = {
    "latitude": -23.8400,
    "longitude": -46.5300,
    "timezone": "America/Sao_Paulo",
    "hourly_units": {"time": "iso8601", "precipitation": "mm", "wind_speed_10m": "km/h"},
    "hourly": {
        "time": ["2026-11-25T13:00", "2026-11-25T14:00", "2026-11-25T15:00"],
        "precipitation": [0.0, 0.2, 0.0],
        "wind_speed_10m": [10.0, 11.5, 9.8],
    },
}

FIXTURE_ANP_CSV = (
    "Regiao - Sigla;Estado - Sigla;Municipio;Revenda;CNPJ da Revenda;Nome da Rua;"
    "Numero Rua;Complemento;Bairro;Cep;Produto;Data da Coleta;Valor de Venda;"
    "Valor de Compra;Unidade de Medida;Bandeira\n"
    "SE;SP;SAO PAULO;POSTO ALPHA;00.000.000/0001-01;AV A;10;;CENTRO;01000-000;DIESEL S10;09/11/2026;7,10;;R$ / litro;VIBRA\n"
    "SE;SP;SAO PAULO;POSTO BETA;00.000.000/0001-02;AV B;20;;CENTRO;01000-000;DIESEL S10;16/11/2026;7,20;;R$ / litro;IPIRANGA\n"
    "SE;SP;SANTOS;POSTO GAMA;00.000.000/0001-03;AV C;30;;PORTO;11000-000;DIESEL S10;18/11/2026;7,40;;R$ / litro;RAIZEN\n"
    "SE;SP;SANTOS;POSTO DELTA;00.000.000/0001-04;AV D;40;;PORTO;11000-000;DIESEL;18/11/2026;6,90;;R$ / litro;BRANCA\n"
    "SE;RJ;RIO DE JANEIRO;POSTO RJ;00.000.000/0001-05;AV E;50;;CENTRO;20000-000;DIESEL S10;18/11/2026;7,60;;R$ / litro;BRANCA\n"
)


class FakeHttpResponse:
    def __init__(self, status_code: int = 200, *, json_body=None, text: str | None = None):
        self.status_code = status_code
        self._json_body = json_body
        if text is not None:
            self.text = text
            self.content = text.encode("utf-8")
        elif json_body is not None:
            self.text = json.dumps(json_body)
            self.content = self.text.encode("utf-8")
        else:
            self.text = ""
            self.content = b""

    def json(self):
        if self._json_body is None:
            raise ValueError("nao e JSON")
        return self._json_body


def _make_router_http_get():
    """Responde OSRM, Open-Meteo e ANP offline conforme a URL consultada."""

    def fake_get(url: str, headers=None, timeout=20.0):
        if "router.project-osrm.org" in url:
            return FakeHttpResponse(200, json_body=FIXTURE_OSRM_TWO_ROUTES)
        if "api.open-meteo.com" in url:
            if "-23.81200" in url:
                return FakeHttpResponse(200, json_body=FIXTURE_OPEN_METEO_ROUTE_A)
            return FakeHttpResponse(200, json_body=FIXTURE_OPEN_METEO_ROUTE_B)
        if "gov.br/anp" in url:
            return FakeHttpResponse(200, text=FIXTURE_ANP_CSV)
        raise AssertionError(f"URL inesperada no teste offline: {url}")

    return fake_get


def _load_pipeline():
    spec = importlib.util.spec_from_file_location("run_jev_pipeline", ROOT / "scripts" / "run_jev_pipeline.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ------------------------------------------------------------ fluxo feliz


def test_build_real_scenario_full_and_sources_json(tmp_path):
    result = build_real_scenario(
        departure_hour="2026-11-25T14:00",
        http_get=_make_router_http_get(),
    )

    states = result["route_states"]
    assert states["A"]["distancia_km"] == pytest.approx(71.4)
    assert states["A"]["duracao_estimada_min"] == pytest.approx(78.0)
    assert states["B"]["distancia_km"] == pytest.approx(79.8)
    assert states["B"]["duracao_estimada_min"] == pytest.approx(72.0)
    assert states["A"]["precipitacao_mm_h"] == pytest.approx(12.6)
    assert states["A"]["vento_km_h"] == pytest.approx(29.4)
    assert states["B"]["precipitacao_mm_h"] == pytest.approx(0.2)
    assert states["B"]["vento_km_h"] == pytest.approx(11.5)

    # ANP: pega so a semana mais recente de SP (16/11 e 18/11 -> media de 7.20 e 7.40 = 7.30)
    assert states["A"]["diesel_s10_estado_brl_l"] == pytest.approx(7.30)

    # ANTT: truck_1 (5 eixos) e truck_2 (6 eixos) tem custos diferentes
    costs = result["base_costs_brl"]
    assert costs["truck_1"]["A"] == pytest.approx(round(71.4 * ANTT_CCD_CARGA_GERAL_BRL_KM[5], 2))
    assert costs["truck_2"]["A"] == pytest.approx(round(71.4 * ANTT_CCD_CARGA_GERAL_BRL_KM[6], 2))
    assert costs["truck_1"]["A"] != costs["truck_2"]["A"]

    # sources.json salvo com valor, unidade, url, consultado_em_utc e resposta_bruta
    out_file = save_sources(tmp_path, result["sources"])
    saved = json.loads(out_file.read_text(encoding="utf-8"))
    items = saved["items"]
    for key in (
        "rota_A_distancia",
        "rota_B_distancia",
        "clima_rota_A_chuva",
        "clima_rota_B_vento",
        "diesel_s10_anp",
        "antt_ccd_5_eixos_carga_geral",
        "antt_ccd_6_eixos_carga_geral",
    ):
        assert "valor" in items[key]
        assert "unidade" in items[key]
        assert items[key]["url"]
        assert items[key]["consultado_em_utc"]
        assert items[key]["resposta_bruta"]

    # parametros da equipe marcados explicitamente como nao medidos
    assert items["multa_atraso"]["origem"] == "parametro da equipe, nao medido"
    assert items["congestionamento_ambos_rota_A"]["origem"] == "parametro da equipe, nao medido"


def test_compute_antt_base_costs_invalid_axles():
    with pytest.raises(RealScenarioError, match="eixos"):
        compute_antt_base_costs({"A": 80.0, "B": 95.0}, truck_axles={"truck_1": 8, "truck_2": 6})


# ------------------------------------------------------------ fonte fora do ar


def test_source_down_connection_error_and_http_503():
    def no_network(*a, **kw):
        raise requests.exceptions.ConnectionError("sem internet")

    with pytest.raises(RealScenarioError, match="OSRM"):
        fetch_osrm_routes(-46.60, -23.60, -46.32, -23.95, http_get=no_network)

    with pytest.raises(RealScenarioError, match="Open-Meteo"):
        fetch_open_meteo_weather(-23.81, -46.48, "2026-11-25T14:00", http_get=no_network)

    with pytest.raises(RealScenarioError, match="ANP"):
        fetch_anp_diesel_s10("SP", http_get=no_network)

    def http_503(*a, **kw):
        return FakeHttpResponse(503, text="Service Unavailable")

    with pytest.raises(RealScenarioError, match="HTTP 503"):
        fetch_osrm_routes(-46.60, -23.60, -46.32, -23.95, http_get=http_503)

    with pytest.raises(RealScenarioError, match="HTTP 503"):
        fetch_open_meteo_weather(-23.81, -46.48, "2026-11-25T14:00", http_get=http_503)

    with pytest.raises(RealScenarioError, match="HTTP 503"):
        fetch_anp_diesel_s10("SP", http_get=http_503)


# ------------------------------------------------------------ JSON quebrado


def test_broken_json_osrm_and_open_meteo():
    broken = lambda *a, **kw: FakeHttpResponse(200, json_body=None, text="<html>erro</html>")

    with pytest.raises(RealScenarioError, match="JSON invalido"):
        fetch_osrm_routes(-46.60, -23.60, -46.32, -23.95, http_get=broken)

    with pytest.raises(RealScenarioError, match="JSON invalido"):
        fetch_open_meteo_weather(-23.81, -46.48, "2026-11-25T14:00", http_get=broken)

    missing_hourly = lambda *a, **kw: FakeHttpResponse(200, json_body={"latitude": -23.8})
    with pytest.raises(RealScenarioError, match="hourly"):
        fetch_open_meteo_weather(-23.81, -46.48, "2026-11-25T14:00", http_get=missing_hourly)


# ------------------------------------------------------------ rota sem alternativa


def test_osrm_route_without_alternative():
    single_route = {
        "code": "Ok",
        "routes": [FIXTURE_OSRM_TWO_ROUTES["routes"][0]],
    }
    only_one = lambda *a, **kw: FakeHttpResponse(200, json_body=single_route)

    with pytest.raises(RealScenarioError, match="pelo menos 2 rotas"):
        fetch_osrm_routes(-46.60, -23.60, -46.32, -23.95, http_get=only_one)

    empty_routes = lambda *a, **kw: FakeHttpResponse(200, json_body={"code": "Ok", "routes": []})
    with pytest.raises(RealScenarioError, match="pelo menos 2 rotas"):
        fetch_osrm_routes(-46.60, -23.60, -46.32, -23.95, http_get=empty_routes)


# ------------------------------------------------------------ preco faltando


def test_anp_missing_price_or_state():
    # estado sem registro no CSV
    ok_csv = lambda *a, **kw: FakeHttpResponse(200, text=FIXTURE_ANP_CSV)
    with pytest.raises(RealScenarioError, match="MG"):
        fetch_anp_diesel_s10("MG", http_get=ok_csv)

    # CSV com DIESEL S10 mas valor de venda vazio
    blank_price_csv = (
        "Regiao - Sigla;Estado - Sigla;Municipio;Revenda;CNPJ da Revenda;Nome da Rua;"
        "Numero Rua;Complemento;Bairro;Cep;Produto;Data da Coleta;Valor de Venda;"
        "Valor de Compra;Unidade de Medida;Bandeira\n"
        "SE;SP;SAO PAULO;POSTO X;00.000.000/0001-01;AV A;10;;CENTRO;01000-000;DIESEL S10;18/11/2026;;;R$ / litro;VIBRA\n"
    )
    with pytest.raises(RealScenarioError, match="DIESEL S10"):
        fetch_anp_diesel_s10("SP", http_get=lambda *a, **kw: FakeHttpResponse(200, text=blank_price_csv))

    # CSV sem coluna obrigatoria
    bad_header_csv = "Estado;Combustivel;Preco\nSP;DIESEL S10;7,30\n"
    with pytest.raises(RealScenarioError, match="colunas obrigatorias"):
        fetch_anp_diesel_s10("SP", http_get=lambda *a, **kw: FakeHttpResponse(200, text=bad_header_csv))


# ------------------------------------------------------------ integracao CLI --scenario real


def test_pipeline_cli_scenario_real_and_rebuild_without_flag(tmp_path, monkeypatch):
    pipeline = _load_pipeline()
    creds = tmp_path / "credentials"
    creds.mkdir()
    (creds / "jev_apikey.json").write_text('{"apikey": "chave-teste"}', encoding="utf-8")
    out = tmp_path / "jev_poc_v0.2"

    # injeta o http_get offline dentro do build_real_scenario usado pelo pipeline
    orig_build = pipeline.build_real_scenario
    monkeypatch.setattr(
        pipeline,
        "build_real_scenario",
        lambda **kw: orig_build(**{**kw, "http_get": _make_router_http_get()}),
    )

    from src.scoring.jev_client import parse_answers
    from src.scoring.jev_logistics import QUESTIONS

    def fake_ask(state, questions, **kwargs):
        p = 0.82 if state["precipitacao_mm_h"] >= 10.0 else 0.12
        body = {
            "model": "jev-1.14.0",
            "answers": {
                "risco_atraso": {"type": "noul", "noul": p},
                "condicao_operacional": {
                    "type": "choice",
                    "choice": "critica" if p > 0.5 else "normal",
                    "probabilities": {"normal": 0.1, "atencao": 0.2, "critica": 0.7, "indefinida": 0.0},
                    "confidence": 0.8,
                },
                "dificuldade_acesso": {
                    "type": "score",
                    "score": 2.4 if p > 0.5 else 0.4,
                    "probabilities": {"0": 0.1, "1": 0.1, "2": 0.6, "3": 0.2},
                    "confidence": 0.8,
                },
            },
            "usage": {"input_tokens": 250, "output_tokens": 25},
        }
        return {
            "request": {"model": kwargs["model"], "state": state, "questions": questions},
            "response": body,
            "answers": parse_answers(body, questions),
            "http_status": 200,
            "attempts": 1,
        }

    monkeypatch.setattr(pipeline, "ask_jev", fake_ask)

    # simula o run_ideal_qaoa_sweep para rodar rapido e sem exigir qiskit neste teste unitario
    monkeypatch.setattr(
        pipeline,
        "run_ideal_qaoa_sweep",
        lambda model, **kw: {
            "selected_parameters": {"p": 1, "seed": 42, "optimal_probability": 0.95, "final_parameters": [0.5, 0.5]},
            "uniform_baseline": {"optimal_probability": 0.25},
            "runs": [{"shots": 512, "optimal_probability": 0.95, "expected_energy": 0.0, "counts": {"11": 486, "01": 26}}],
        },
    )

    rc = pipeline.main(
        [
            "--scenario",
            "real",
            "--departure",
            "2026-11-25T14:00",
            "--credentials-dir",
            str(creds),
            "--results-dir",
            str(out),
            "--shots",
            "512",
        ]
    )
    assert rc == 0
    for fname in ("sources.json", "jev_responses.json", "qubo_jev.json", "simulator_results.json", "REPORT.md"):
        assert (out / fname).exists()

    qubo = json.loads((out / "qubo_jev.json").read_text(encoding="utf-8"))
    assert qubo["scenario"] == "real"
    assert qubo["synthetic_scenario"] is False
    assert qubo["team_parameters_note"] == "parametro da equipe, nao medido"

    # garante que rebuild_jev_model funciona sem passar --scenario real (igual ao --ibm-dry-run/--ibm-execute)
    model, _jev, _qubo, _sim = pipeline.rebuild_jev_model(out)
    assert model.metadata["optimal_bitstrings"] == qubo["qubo_with_jev"]["optimal_bitstrings"]
