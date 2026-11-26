"""Testes offline da integracao Jev + QUBO + IBM (sem internet e sem chave de verdade)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
import requests

from src.cdc.qubo import two_truck_example
from src.credentials import CredentialError, read_secret
from src.scoring.jev_client import JEV_PROVIDERS, JevError, ask_jev, parse_answers
from src.scoring.jev_logistics import (
    QUESTIONS,
    build_two_truck_qubo,
    describe_bitstring,
    route_costs,
    route_signals,
)

ROOT = Path(__file__).resolve().parents[1]


def load_pipeline():
    spec = importlib.util.spec_from_file_location("run_jev_pipeline", ROOT / "scripts" / "run_jev_pipeline.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fake_body(noul: float, choice: str = "atencao", score: float = 1.0) -> dict:
    # mesmo formato do exemplo da documentacao do Jev
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "result": {
                "answers": {
                    "risco_atraso": {"type": "noul", "noul": noul},
                    "condicao_operacional": {
                        "type": "choice",
                        "choice": choice,
                        "probabilities": {"normal": 0.1, "atencao": 0.6, "critica": 0.3, "indefinida": 0.0},
                        "confidence": 0.7,
                    },
                    "dificuldade_acesso": {
                        "type": "score",
                        "score": score,
                        "legend": {"0": "Baixa", "1": "Media", "2": "Alta", "3": "Muito alta"},
                        "probabilities": {"0": 0.1, "1": 0.8, "2": 0.1, "3": 0.0},
                        "confidence": 0.8,
                    },
                },
                "usage": {"input_tokens": 300, "output_tokens": 30},
                "elapsedMs": 250,
            },
            "creditsUsed": 3,
        },
    }


class FakeResponse:
    def __init__(self, status: int, body=None, text: str | None = None, headers=None):
        self.status_code = status
        self._body = body
        self.text = text if text is not None else json.dumps(body)
        self.headers = headers or {}

    def json(self):
        if self._body is None:
            raise ValueError("not json")
        return self._body


# ------------------------------------------------------------ credenciais


def test_read_secret_formats(tmp_path):
    f = tmp_path / "k.json"
    f.write_text('{"apikey": "abc123"}', encoding="utf-8")
    assert read_secret(f, ("apikey",), label="t") == "abc123"

    f.write_bytes(b'\xef\xbb\xbf{"apikey": "comBOM"}')  # BOM do Windows
    assert read_secret(f, ("apikey",), label="t") == "comBOM"

    f.write_text("  so-a-chave \n", encoding="utf-8")
    assert read_secret(f, ("apikey",), label="t") == "so-a-chave"

    f.write_text('{"apikey": "Bearer xyz"}', encoding="utf-8")
    assert read_secret(f, ("apikey",), label="t") == "xyz"

    f.write_text('{"apikey": "utf16"}', encoding="utf-16")
    assert read_secret(f, ("apikey",), label="t") == "utf16"


@pytest.mark.parametrize(
    "content",
    ["", '{"apikey": ', '{"outro": "x"}', '{"apikey": "COLE_AQUI"}', '{"apikey": 123}', "duas palavras"],
)
def test_read_secret_bad_files(tmp_path, content):
    f = tmp_path / "k.json"
    f.write_text(content, encoding="utf-8")
    with pytest.raises(CredentialError):
        read_secret(f, ("apikey",), label="t")


def test_read_secret_missing_and_optional(tmp_path):
    with pytest.raises(CredentialError):
        read_secret(tmp_path / "nao_existe.json", ("apikey",), label="t")
    assert read_secret(tmp_path / "nao_existe.json", ("crn",), label="t", required=False) is None
    f = tmp_path / "crn.json"
    f.write_text('{"crn": ""}', encoding="utf-8")  # crn vazio = IBM escolhe a instancia
    assert read_secret(f, ("crn",), label="t", required=False) is None


# ------------------------------------------------------------ respostas do Jev


def test_parse_answers_ok():
    parsed = parse_answers(fake_body(0.87, "critica", 2.4), QUESTIONS)
    assert parsed["risco_atraso"]["noul"] == pytest.approx(0.87)
    assert parsed["condicao_operacional"]["choice"] == "critica"
    assert parsed["dificuldade_acesso"]["score_normalized"] == pytest.approx(0.8)


def test_parse_answers_errors():
    body = fake_body(0.5)
    del body["data"]["result"]["answers"]["risco_atraso"]
    with pytest.raises(JevError):
        parse_answers(body, QUESTIONS)
    with pytest.raises(JevError):
        parse_answers(fake_body(1.7), QUESTIONS)  # noul fora de 0 a 1
    with pytest.raises(JevError):
        parse_answers(fake_body(0.5, choice="inventada"), QUESTIONS)
    with pytest.raises(JevError):
        parse_answers(fake_body(0.5, score=7.0), QUESTIONS)  # score fora de 0 a 3
    with pytest.raises(JevError):
        parse_answers({"code": 1001, "message": "sem creditos"}, QUESTIONS)


def test_ask_jev_retry_then_ok():
    calls = []

    def post(url, headers, json, timeout):
        calls.append(headers)
        if len(calls) == 1:
            return FakeResponse(429, {"code": 429}, headers={"Retry-After": "1"})
        return FakeResponse(200, fake_body(0.3))

    sleeps = []
    out = ask_jev({"rota": "x"}, QUESTIONS, api_key="k", http_post=post, sleep=sleeps.append)
    assert out["attempts"] == 2 and sleeps == [1.0]
    assert calls[0]["Authorization"] == "Bearer k"
    assert "k" not in json.dumps(out["request"])  # a chave nao vai pro arquivo salvo


def test_ask_jev_errors():
    with pytest.raises(JevError, match="401"):
        ask_jev("x", QUESTIONS, api_key="k", http_post=lambda *a, **kw: FakeResponse(401, {"code": 401}))

    def no_net(*a, **kw):
        raise requests.exceptions.ConnectionError("sem rede")

    with pytest.raises(JevError, match="internet"):
        ask_jev("x", QUESTIONS, api_key="k", http_post=no_net, sleep=lambda s: None)

    with pytest.raises(JevError, match="JSON"):
        ask_jev("x", QUESTIONS, api_key="k", http_post=lambda *a, **kw: FakeResponse(200, None, text="<html>"))

    with pytest.raises(JevError):
        ask_jev("", QUESTIONS, api_key="k", http_post=lambda *a, **kw: FakeResponse(200, fake_body(0.1)))


# ------------------------------------------------------------ QUBO


def test_qubo_without_jev_is_whitepaper():
    model = build_two_truck_qubo(route_costs(None))
    ref = two_truck_example()
    for bits in ([0, 0], [0, 1], [1, 0], [1, 1]):
        assert model.evaluate(bits) == pytest.approx(ref.evaluate(bits))
    assert model.metadata["optimal_bitstrings"] == ["01", "10"]


def test_qubo_with_jev_risk():
    answers = {
        "A": parse_answers(fake_body(0.8), QUESTIONS),
        "B": parse_answers(fake_body(0.1), QUESTIONS),
    }
    costs = route_costs(route_signals(answers), delay_penalty_brl=500)
    model = build_two_truck_qubo(costs)
    # caminhao 1: A = 300 + 400, B = 320 + 50 | caminhao 2: A = 290 + 400, B = 310 + 50
    assert model.metadata["expected_values"]["11"] == pytest.approx(370 + 360)
    assert model.metadata["expected_values"]["00"] == pytest.approx(700 + 690 + 70)
    assert model.metadata["optimal_bitstrings"] == ["11"]
    assert describe_bitstring("01") == "caminhão 1 rota A, caminhão 2 rota B"


# ------------------------------------------------------------ fluxo inteiro offline


def test_pipeline_offline_with_fake_backend(tmp_path, monkeypatch):
    pipeline = load_pipeline()
    creds = tmp_path / "credentials"
    creds.mkdir()
    (creds / "jev_apikey.json").write_text('{"apikey": "chave-falsa"}', encoding="utf-8")
    out = tmp_path / "results"

    def fake_ask(state, questions, **kwargs):
        p = 0.85 if "serra" in state["rota"] else 0.05
        body = fake_body(p, "critica" if p > 0.5 else "normal", 2.5 if p > 0.5 else 0.3)
        return {"request": {"model": kwargs["model"], "state": state, "questions": questions}, "response": body,
                "answers": parse_answers(body, questions), "http_status": 200, "attempts": 1}

    monkeypatch.setattr(pipeline, "ask_jev", fake_ask)
    base = ["--credentials-dir", str(creds), "--results-dir", str(out), "--shots", "1024"]
    assert pipeline.main(base) == 0
    for name in ("jev_responses.json", "qubo_jev.json", "simulator_results.json", "REPORT.md"):
        assert (out / name).exists()
    qubo = json.loads((out / "qubo_jev.json").read_text(encoding="utf-8"))
    assert qubo["qubo_with_jev"]["optimal_bitstrings"] == ["11"]
    assert qubo["decision_changed"] is True
    assert "chave-falsa" not in (out / "jev_responses.json").read_text(encoding="utf-8")

    # reaproveita sem chamar o Jev
    monkeypatch.setattr(pipeline, "ask_jev", lambda *a, **kw: pytest.fail("nao era pra chamar o Jev"))
    assert pipeline.main(base + ["--reuse-jev"]) == 0

    # IBM com backend falso local (FakeKingston roda no Aer, sem conta)
    from qiskit_ibm_runtime.fake_provider import FakeKingston

    args = pipeline.parse_args(base + ["--ibm-dry-run"])
    assert pipeline.run_ibm_phase(args, out, backend_override=FakeKingston()) == 0
    assert (out / "ibm_dry_run.json").exists()

    monkeypatch.setattr("builtins.input", lambda prompt="": "EXECUTE")
    args = pipeline.parse_args(base + ["--ibm-execute", "--ibm-wait-minutes", "2"])
    assert pipeline.run_ibm_phase(args, out, backend_override=FakeKingston()) == 0
    ibm = json.loads((out / "ibm_results.json").read_text(encoding="utf-8"))
    assert ibm["status"] == "completed"
    assert sum(ibm["counts"].values()) == 1024
    assert ibm["optimal_probability"] > 0.5
    assert "IBM Quantum" in (out / "REPORT.md").read_text(encoding="utf-8")

    # sem digitar EXECUTE nada e enviado
    monkeypatch.setattr("builtins.input", lambda prompt="": "nao")
    assert pipeline.run_ibm_phase(args, out, backend_override=FakeKingston()) == 1


def test_ibm_phase_needs_previous_run(tmp_path):
    pipeline = load_pipeline()
    args = pipeline.parse_args(["--results-dir", str(tmp_path / "vazio"), "--ibm-dry-run"])
    assert pipeline.main(["--results-dir", str(tmp_path / "vazio"), "--ibm-dry-run"]) == 1
    _ = args


# ------------------------------------------------------------ API oficial da TypeSafe


def test_parse_answers_typesafe_format():
    # a API oficial devolve answers no topo, sem code/data
    wrapped = fake_body(0.42)
    body = {"model": "jev-1.13.0", "answers": wrapped["data"]["result"]["answers"], "usage": {"input_tokens": 1}}
    parsed = parse_answers(body, QUESTIONS)
    assert parsed["risco_atraso"]["noul"] == pytest.approx(0.42)
    with pytest.raises(JevError):
        parse_answers({"model": "x", "usage": {}}, QUESTIONS)


def test_401_message_points_to_other_provider():
    with pytest.raises(JevError, match="--jev-provider"):
        ask_jev(
            "x", QUESTIONS, api_key="k", url=JEV_PROVIDERS["typesafe"]["url"],
            http_post=lambda *a, **kw: FakeResponse(401, {"detail": "unauthorized"}),
        )


def test_pipeline_uses_typesafe_endpoint(tmp_path, monkeypatch):
    pipeline = load_pipeline()
    creds = tmp_path / "credentials"
    creds.mkdir()
    (creds / "jev_apikey.json").write_text('{"apikey": "apikey_teste"}', encoding="utf-8")
    seen = {}

    def fake_ask(state, questions, **kwargs):
        seen["url"], seen["model"] = kwargs["url"], kwargs["model"]
        answers = fake_body(0.2)["data"]["result"]["answers"]
        body = {"model": "jev-1.13.0", "answers": answers, "usage": {}}
        return {"request": {"model": kwargs["model"], "state": state, "questions": questions}, "response": body,
                "answers": parse_answers(body, questions), "http_status": 200, "attempts": 1}

    monkeypatch.setattr(pipeline, "ask_jev", fake_ask)
    out = tmp_path / "results"
    args = ["--credentials-dir", str(creds), "--results-dir", str(out), "--shots", "512", "--jev-provider", "typesafe"]
    assert pipeline.main(args) == 0
    assert seen == {"url": "https://api.typesafe.ai/v1/systemone", "model": "jev-1.14.0"}
    saved = json.loads((out / "jev_responses.json").read_text(encoding="utf-8"))
    assert saved["provider"] == "typesafe"
    assert "api.typesafe.ai" in (out / "REPORT.md").read_text(encoding="utf-8")


def test_check_crn():
    pipeline = load_pipeline()
    good = "crn:v1:bluemix:public:quantum-computing:us-east:a/1a2b3c:7e8f9a::"
    assert pipeline.check_crn(good) == good
    assert pipeline.check_crn(None) is None
    assert pipeline.check_crn("open-instance") == "open-instance"
    for bad in (good[4:], good + "apikey.json", "v1:bluemix:public:quantum-computing:x::apikey.json", "a/b:c"):
        with pytest.raises(pipeline.PipelineError):
            pipeline.check_crn(bad)
