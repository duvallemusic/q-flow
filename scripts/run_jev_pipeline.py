#!/usr/bin/env python3
"""Prova Jev + Qiskit: contexto da rota -> Jev -> QUBO -> classico e QAOA -> IBM Quantum (opcional).

Rodar na raiz do projeto:
  python scripts/run_jev_pipeline.py                  chama o Jev, monta o QUBO e roda o simulador
  python scripts/run_jev_pipeline.py --reuse-jev      refaz QUBO e simulador com as respostas ja salvas (nao gasta credito)
  python scripts/run_jev_pipeline.py --ibm-dry-run    confere conta IBM, backend e circuito, sem enviar job
  python scripts/run_jev_pipeline.py --ibm-execute    envia 1 job pro hardware (pede para digitar EXECUTE)
  python scripts/run_jev_pipeline.py --ibm-job-id ID  busca o resultado de um job ja enviado

Chaves na pasta credentials/ (ignorada pelo git):
  credentials/jev_apikey.json   {"apikey": "..."}
  credentials/ibm_apikey.json   {"apikey": "..."}
  credentials/ibm_crn.json      {"crn": "..."}   opcional, sem ele a IBM escolhe a instancia
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.cdc.ising import cost_operator_without_identity, qubo_to_ising  # noqa: E402
from src.cdc.qubo import QuboModel, two_truck_example  # noqa: E402
from src.credentials import CredentialError, read_secret  # noqa: E402
from src.optimization.classical import enumerate_exact  # noqa: E402
from src.optimization.metrics import summarize_counts, total_variation_distance  # noqa: E402
from src.optimization.qaoa import _counts_to_x_endian  # noqa: E402
from src.optimization.simulator import run_ideal_qaoa_sweep  # noqa: E402
from src.results_io import environment_snapshot, utc_now, write_json  # noqa: E402
from src.scoring.jev_client import (  # noqa: E402
    JEV_PROVIDERS,
    JevError,
    ask_jev,
    parse_answers,
)
from src.scoring.jev_logistics import (  # noqa: E402
    CONGESTION_BOTH_A_BRL,
    DEFAULT_DELAY_PENALTY_BRL,
    QUESTIONS,
    ROUTE_STATES,
    build_two_truck_qubo,
    describe_bitstring,
    route_costs,
    route_signals,
)

try:
    from scipy.sparse import SparseEfficiencyWarning

    # aviso interno do simulador, nao muda resultado, so suja o terminal
    warnings.filterwarnings("ignore", category=SparseEfficiencyWarning)
except ImportError:  # pragma: no cover
    pass

DEFAULT_RESULTS = ROOT / "results" / "jev_poc_v0.1"
DEFAULT_CREDENTIALS = ROOT / "credentials"


class PipelineError(RuntimeError):
    """Erro do fluxo com mensagem pronta pra mostrar."""


# ---------------------------------------------------------------- utilidades


def brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def num(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "-"
    return f"{value:.{digits}f}".replace(".", ",")


def pct(value: float | None) -> str:
    return "-" if value is None else f"{value * 100:.2f}%".replace(".", ",")


def load_json(path: Path, what: str) -> dict[str, Any]:
    if not path.exists():
        raise PipelineError(f"nao achei {path}. {what}")
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise PipelineError(f"{path} esta corrompido (JSON invalido). {what}") from exc


def jev_usage(saved: dict[str, Any]) -> dict[str, Any]:
    """Pega versao do modelo, tokens e creditos da resposta (os dois formatos de API)."""
    resp = saved.get("response") or {}
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    result = data.get("result") if isinstance(data.get("result"), dict) else {}
    usage = resp.get("usage") or result.get("usage") or {}
    return {
        "model": resp.get("model") or result.get("model"),
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "credits": data.get("creditsUsed"),
    }


def usage_text(u: dict[str, Any]) -> str:
    parts = []
    if u["input_tokens"] is not None:
        parts.append(f"{u['input_tokens']}/{u['output_tokens']}")
    if u["credits"] is not None:
        parts.append(f"{u['credits']} cred.")
    return " | ".join(parts) if parts else "-"


def qubo_formula(model: QuboModel) -> str:
    def term(c: float, var: str) -> str:
        sign = "-" if c < 0 else "+"
        return f" {sign} {abs(c):g}{var}"

    text = f"F = {model.offset:g}"
    for i, c in sorted(model.linear.items()):
        text += term(c, f" x{i + 1}")
    for (i, j), c in sorted(model.quadratic.items()):
        text += term(c, f" x{i + 1}x{j + 1}")
    return text


def qubo_payload(model: QuboModel) -> dict[str, Any]:
    return {
        "offset": model.offset,
        "linear": {str(k): v for k, v in model.linear.items()},
        "quadratic": {f"{i},{j}": v for (i, j), v in model.quadratic.items()},
        "formula": qubo_formula(model),
        "values_brl": model.metadata["expected_values"],
        "optimal_bitstrings": model.metadata["optimal_bitstrings"],
        "encoding": "x=0 -> rota A, x=1 -> rota B",
    }


# ---------------------------------------------------------------- fase 1: Jev


def call_jev_for_routes(
    api_key: str,
    *,
    model: str,
    url: str,
    provider: str,
    timeout: float,
    out: Path,
    run_id: str,
    ask: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Uma chamada por rota (A e B), com as mesmas 3 perguntas. Salva tudo em jev_responses.json."""
    ask = ask or ask_jev
    record: dict[str, Any] = {
        "run_id": run_id,
        "created_at_utc": utc_now(),
        "provider": provider,
        "endpoint": url,
        "model": model,
        "synthetic_scenario": True,
        "complete": False,
        "routes": {},
    }
    for route, state in ROUTE_STATES.items():
        print(f"  chamando o Jev para a rota {route}...")
        result = ask(state, QUESTIONS, api_key=api_key, model=model, url=url, timeout=timeout)
        record["routes"][route] = result
        write_json(out / "jev_responses.json", record)  # salva a cada rota pra nao perder o que ja veio
    record["complete"] = True
    write_json(out / "jev_responses.json", record)
    return record


def load_saved_jev(out: Path) -> dict[str, Any]:
    record = load_json(out / "jev_responses.json", "Rode antes: python scripts/run_jev_pipeline.py")
    if not record.get("complete"):
        raise PipelineError("jev_responses.json esta incompleto (uma das rotas falhou). Rode sem --reuse-jev.")
    for route in ROUTE_STATES:
        saved = record.get("routes", {}).get(route)
        if not saved:
            raise PipelineError(f"jev_responses.json nao tem a rota {route}. Rode sem --reuse-jev.")
        questions = saved.get("request", {}).get("questions") or QUESTIONS
        # confere de novo a resposta salva, se alguem editou o arquivo a mao da erro aqui
        saved["answers"] = parse_answers(saved.get("response"), questions)
    return record


def run_jev_phase(args: argparse.Namespace, out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    print("\n[1/4] Jev")
    if args.reuse_jev:
        jev = load_saved_jev(out)
        print(f"  usando respostas salvas de {jev['created_at_utc']} (nenhum credito gasto)")
    else:
        key = read_secret(
            Path(args.credentials_dir) / "jev_apikey.json", ("apikey", "api_key"), label="Chave do Jev"
        )
        provider = JEV_PROVIDERS[args.jev_provider]
        model = args.jev_model or provider["model"]
        print(f"  endereco: {provider['url']} | modelo: {model}")
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        jev = call_jev_for_routes(
            key,
            model=model,
            url=provider["url"],
            provider=args.jev_provider,
            timeout=args.jev_timeout,
            out=out,
            run_id=run_id,
        )

    answers_by_route = {r: jev["routes"][r]["answers"] for r in ROUTE_STATES}
    signals = route_signals(answers_by_route)
    for route in ("A", "B"):
        s = signals[route]
        u = jev_usage(jev["routes"][route])
        print(
            f"  rota {route}: risco de atraso {num(s['delay_probability'])} | condicao {s['condition']}"
            f" | dificuldade {num(s['access_difficulty_score'])} de 3 | tokens {usage_text(u)}"
        )
    resolved = jev_usage(jev["routes"]["A"])["model"]
    if resolved:
        print(f"  modelo que respondeu: {resolved}")
        if s["human_review"]:
            print(f"  rota {route}: condicao critica, pela nossa regra vai pra revisao humana")

    print("\n[2/4] Custos e QUBO")
    penalty = float(args.delay_penalty)
    costs_base = route_costs(None, delay_penalty_brl=penalty)
    costs_jev = route_costs(signals, delay_penalty_brl=penalty)
    model_base = build_two_truck_qubo(costs_base, instance_id="two_truck_whitepaper")
    model_jev = build_two_truck_qubo(costs_jev, instance_id="two_truck_jev")

    # sanidade: sem Jev tem que dar exatamente o exemplo do White Paper
    ref = two_truck_example()
    for bits in ("00", "01", "10", "11"):
        b = [int(c) for c in bits]
        if abs(model_base.evaluate(b) - ref.evaluate(b)) > 1e-9:
            raise PipelineError("QUBO sem Jev nao bate com o White Paper, algo mudou nos custos base")

    print(f"  sem Jev: {qubo_formula(model_base)}")
    print(f"  com Jev: {qubo_formula(model_jev)}  (multa de atraso {brl(penalty)})")
    print("  estado | significado                          | sem Jev     | com Jev")
    for bits in ("00", "01", "10", "11"):
        print(
            f"  {bits}     | {describe_bitstring(bits):36s} | {brl(model_base.metadata['expected_values'][bits]):11s}"
            f" | {brl(model_jev.metadata['expected_values'][bits])}"
        )

    exact_base = enumerate_exact(model_base)
    exact_jev = enumerate_exact(model_jev)
    opt_base = model_base.metadata["optimal_bitstrings"]
    opt_jev = model_jev.metadata["optimal_bitstrings"]
    print(f"  otimo sem Jev: {', '.join(opt_base)} | otimo com Jev: {', '.join(opt_jev)}")
    changed = set(opt_base) != set(opt_jev)
    print("  o sinal do Jev mudou a decisao" if changed else "  o sinal do Jev nao mudou a decisao")

    write_json(
        out / "qubo_jev.json",
        {
            "run_id": jev["run_id"],
            "created_at_utc": utc_now(),
            "synthetic_scenario": True,
            "delay_penalty_brl": penalty,
            "congestion_both_a_brl": CONGESTION_BOTH_A_BRL,
            "signals": signals,
            "costs_without_jev": costs_base,
            "costs_with_jev": costs_jev,
            "qubo_without_jev": qubo_payload(model_base),
            "qubo_with_jev": qubo_payload(model_jev),
            "decision_changed": changed,
            "classical": {
                "without_jev": {"optimal_cost": exact_base["optimal_cost"], "optima": opt_base},
                "with_jev": {"optimal_cost": exact_jev["optimal_cost"], "optima": opt_jev},
            },
        },
    )

    print("\n[3/4] QAOA no simulador ideal (pode levar uns 30 s)")
    sim = run_ideal_qaoa_sweep(
        model_jev,
        p_values=[1, 2],
        seeds=[42, 123],
        shots=args.shots,
        cost_fn=model_jev.evaluate,
        optimal_bitstrings=set(opt_jev),
    )
    sel = sim["selected_parameters"]
    best_run = max(sim["runs"], key=lambda r: (r["optimal_probability"], -r["expected_energy"]))
    print(
        f"  melhor config: p={sel['p']}, seed={sel['seed']} | P(otimo) = {pct(sel['optimal_probability'])}"
        f" | uniforme = {pct(sim['uniform_baseline']['optimal_probability'])}"
    )
    write_json(
        out / "simulator_results.json",
        {
            "run_id": jev["run_id"],
            "created_at_utc": utc_now(),
            "environment": environment_snapshot(ROOT),
            "selected_counts": best_run["counts"],
            **sim,
        },
    )

    print("\n[4/4] Relatorio")
    write_report(out)
    print(f"  salvo em {out}")
    print("\nPronto. Proximo passo opcional: python scripts/run_jev_pipeline.py --ibm-dry-run")
    return 0


# ---------------------------------------------------------------- fase 2: IBM Quantum


def rebuild_jev_model(out: Path) -> tuple[QuboModel, dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Remonta o QUBO com Jev a partir dos arquivos salvos, sem chamar o Jev de novo."""
    jev = load_saved_jev(out)
    qubo = load_json(out / "qubo_jev.json", "Rode antes: python scripts/run_jev_pipeline.py")
    sim = load_json(out / "simulator_results.json", "Rode antes: python scripts/run_jev_pipeline.py")
    if qubo.get("run_id") != jev["run_id"] or sim.get("run_id") != jev["run_id"]:
        raise PipelineError(
            "os arquivos de results/ sao de rodadas diferentes. Rode: python scripts/run_jev_pipeline.py --reuse-jev"
        )
    signals = route_signals({r: jev["routes"][r]["answers"] for r in ROUTE_STATES})
    model = build_two_truck_qubo(
        route_costs(signals, delay_penalty_brl=float(qubo["delay_penalty_brl"])), instance_id="two_truck_jev"
    )
    if model.metadata["optimal_bitstrings"] != qubo["qubo_with_jev"]["optimal_bitstrings"]:
        raise PipelineError("QUBO remontado nao bate com qubo_jev.json. Rode de novo com --reuse-jev.")
    return model, jev, qubo, sim


def check_crn(crn: str | None) -> str | None:
    """Confere o CRN antes de mandar pra IBM. Nome de instancia simples tambem vale."""
    if not crn:
        return None
    crn = crn.strip()
    if crn.startswith("v1:bluemix:"):
        raise PipelineError(
            "o CRN em credentials/ibm_crn.json esta sem o comeco 'crn:'. Ele tem que comecar com crn:v1:bluemix:..."
        )
    if crn.startswith("crn:"):
        if ":quantum-computing:" not in crn:
            raise PipelineError("esse CRN nao e de uma instancia do IBM Quantum (falta ':quantum-computing:').")
        if not crn.endswith("::"):
            raise PipelineError(
                f"o CRN tem que terminar com '::'. Parece que sobrou texto no fim: '...{crn[-16:]}'. "
                "Copie de novo em quantum.cloud.ibm.com/instances"
            )
        return crn
    if ":" in crn or "/" in crn:
        raise PipelineError(
            "o valor em credentials/ibm_crn.json nao parece CRN nem nome de instancia. "
            "Copie de novo em quantum.cloud.ibm.com/instances"
        )
    return crn  # nome da instancia, ex: open-instance


def connect_ibm(credentials_dir: Path):
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
    except ImportError as exc:
        raise PipelineError(
            "qiskit-ibm-runtime nao esta instalado. Rode: python -m pip install -r requirements.lock.txt"
        ) from exc

    token = read_secret(credentials_dir / "ibm_apikey.json", ("apikey", "token", "api_key"), label="Chave IBM")
    crn = check_crn(read_secret(credentials_dir / "ibm_crn.json", ("crn", "instance"), label="CRN IBM", required=False))
    if len(token) != 44:
        print(f"  aviso: a chave da IBM costuma ter 44 caracteres e a sua tem {len(token)}. Confere se copiou inteira.")
    print("  conectando na IBM Quantum" + (" (instancia do ibm_crn.json)" if crn else " (sem CRN, a IBM escolhe a instancia)"))
    try:
        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token, instance=crn)
    except Exception as exc:  # noqa: BLE001
        raise PipelineError(
            f"nao consegui entrar na IBM Quantum: {exc}. Confere a chave, o CRN e a internet."
        ) from exc
    return service


def pick_backend(service, name: str | None, n_qubits: int):
    try:
        if name:
            return service.backend(name)
        return service.least_busy(operational=True, min_num_qubits=n_qubits)
    except Exception as exc:  # noqa: BLE001
        raise PipelineError(
            f"nao achei backend disponivel ({exc}). Tenta passar um nome com --ibm-backend, ex: ibm_kingston"
        ) from exc


def build_isa_circuit(model: QuboModel, parameters: list[float], p: int, backend) -> tuple[Any, dict[str, Any]]:
    """Mesmo circuito QAOA do simulador, com os parametros treinados, transpilado pro backend."""
    from qiskit.circuit.library import QAOAAnsatz
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

    ising = qubo_to_ising(model)
    circuit = QAOAAnsatz(cost_operator=cost_operator_without_identity(ising), reps=p)
    if len(parameters) != circuit.num_parameters:
        raise PipelineError(
            f"parametros salvos ({len(parameters)}) nao batem com o circuito ({circuit.num_parameters}). "
            "Rode de novo com --reuse-jev."
        )
    measured = circuit.assign_parameters(parameters)
    measured.measure_all()
    pm = generate_preset_pass_manager(optimization_level=1, backend=backend)
    isa = pm.run(measured)
    # conta so porta de verdade: a barreira do measure_all tambem ocupa 2 qubits e nao e porta
    gates_2q: dict[str, int] = {}
    for inst in isa.data:
        op = inst.operation
        if op.num_qubits == 2 and not getattr(op, "_directive", False) and op.name != "barrier":
            gates_2q[op.name] = gates_2q.get(op.name, 0) + 1
    info = {
        "backend": backend.name,
        "logical_depth": measured.decompose(reps=3).depth(),
        "transpiled_depth": isa.depth(),
        "transpiled_two_qubit_gates": sum(gates_2q.values()),
        "transpiled_two_qubit_gate_names": gates_2q,
        "p": p,
        "parameters": parameters,
    }
    return isa, info


def job_status(job) -> str:
    status = job.status()
    return str(getattr(status, "name", status)).upper()


def summarize_job(job, model: QuboModel, sim: dict[str, Any], shots: int | None = None) -> dict[str, Any]:
    try:
        result = job.result()
        bit_array = result[0].data.meas
    except Exception as exc:  # noqa: BLE001
        raise PipelineError(f"o job terminou mas nao consegui ler o resultado ({exc})") from exc
    if getattr(bit_array, "num_bits", model.n_vars) != model.n_vars:
        raise PipelineError(
            f"esse job mediu {bit_array.num_bits} bits e o nosso circuito mede {model.n_vars}. Confere o job id."
        )
    counts = _counts_to_x_endian(bit_array.get_counts(), model.n_vars)
    summary = summarize_counts(
        counts,
        optimal_bitstrings=set(model.metadata["optimal_bitstrings"]),
        cost_fn=model.evaluate,
    )
    ideal = sim.get("selected_counts") or {}
    total_ideal = sum(ideal.values())
    tvd = None
    if total_ideal:
        tvd = total_variation_distance(summary["distribution"], {k: v / total_ideal for k, v in ideal.items()})
    return {"status": "completed", "counts": counts, "shots": shots or summary["shots"], "tvd_vs_ideal": tvd, **summary}


def wait_job(job, minutes: float, poll_seconds: float = 10.0, sleep: Callable[[float], None] = time.sleep) -> str:
    deadline = time.monotonic() + minutes * 60
    while True:
        try:
            status = job_status(job)
        except Exception as exc:  # noqa: BLE001
            # oscilacao de rede nao pode perder o job, so tenta de novo
            status = f"SEM_RESPOSTA ({exc.__class__.__name__})"
        if "DONE" in status or "COMPLETED" in status:
            return "done"
        if any(s in status for s in ("ERROR", "CANCEL", "FAIL")):
            return status
        if time.monotonic() >= deadline:
            return "pending"
        print(f"  status: {status}, esperando...")
        sleep(poll_seconds)


def run_ibm_phase(args: argparse.Namespace, out: Path, backend_override=None) -> int:
    print("\n[IBM] remontando o QUBO com as respostas salvas do Jev")
    model, jev, _qubo, sim = rebuild_jev_model(out)
    opt = model.metadata["optimal_bitstrings"]
    print(f"  {qubo_formula(model)} | otimo {', '.join(opt)}")
    sel = sim["selected_parameters"]

    service = None if backend_override is not None else connect_ibm(Path(args.credentials_dir))

    if args.ibm_job_id:
        if service is None:
            raise PipelineError("buscar job precisa da conexao com a IBM")
        print(f"  buscando o job {args.ibm_job_id}")
        try:
            job = service.job(args.ibm_job_id)
        except Exception as exc:  # noqa: BLE001
            raise PipelineError(f"nao achei o job {args.ibm_job_id} ({exc})") from exc
        try:
            status = job_status(job)
        except Exception as exc:  # noqa: BLE001
            raise PipelineError(f"nao consegui ver o status do job ({exc}). Tenta de novo em instantes.") from exc
        record: dict[str, Any] = {"run_id": jev["run_id"], "mode": "fetch", "job_id": args.ibm_job_id, "fetched_at_utc": utc_now()}
        if "DONE" in status or "COMPLETED" in status:
            record.update(summarize_job(job, model, sim))
            try:
                record["backend"] = job.backend().name
            except Exception:  # noqa: BLE001
                record["backend"] = None
        else:
            record.update({"status": status.lower()})
        write_json(out / "ibm_results.json", record)
        print_ibm_record(record, opt)
        write_report(out)
        return 0

    backend = backend_override or pick_backend(service, args.ibm_backend, model.n_vars)
    print(f"  backend: {backend.name}")
    isa, info = build_isa_circuit(model, sel["final_parameters"], int(sel["p"]), backend)
    names = ", ".join(f"{v} {k.upper()}" for k, v in info["transpiled_two_qubit_gate_names"].items()) or "nenhuma"
    print(
        f"  circuito transpilado: profundidade {info['transpiled_depth']},"
        f" portas de 2 qubits: {names} | p={info['p']} | shots {args.shots}"
    )

    if args.ibm_dry_run:
        write_json(
            out / "ibm_dry_run.json",
            {"run_id": jev["run_id"], "created_at_utc": utc_now(), "submitted": False, "shots": args.shots, **info},
        )
        print("\nDry-run ok, nenhum job enviado. Pra mandar de verdade: python scripts/run_jev_pipeline.py --ibm-execute")
        return 0

    # execute: confirmacao manual igual ao run_ibm_quantum.py
    try:
        confirm = input("Digite EXECUTE para enviar 1 job para a IBM: ").strip()
    except EOFError:
        confirm = ""
    if confirm != "EXECUTE":
        print("Cancelado, nada foi enviado.")
        return 1

    from qiskit_ibm_runtime import SamplerV2

    try:
        job = SamplerV2(mode=backend).run([isa], shots=args.shots)
        job_id = job.job_id()
    except Exception as exc:  # noqa: BLE001
        raise PipelineError(
            f"a IBM recusou o envio ({exc}). Pode ser falta de minutos na instancia ou backend em manutencao."
        ) from exc

    submitted = {"run_id": jev["run_id"], "job_id": job_id, "submitted_at_utc": utc_now(), "shots": args.shots, **info}
    write_json(out / "ibm_job_submitted.json", submitted)
    print(f"  job enviado: {job_id} (salvo em ibm_job_submitted.json)")

    try:
        state = wait_job(job, args.ibm_wait_minutes)
    except KeyboardInterrupt:
        print(f"\nParou de esperar. Depois rode: python scripts/run_jev_pipeline.py --ibm-job-id {job_id}")
        return 130

    record = {"run_id": jev["run_id"], "mode": "execute", "job_id": job_id, "backend": backend.name, "fetched_at_utc": utc_now()}
    if state == "done":
        record.update(summarize_job(job, model, sim, shots=args.shots))
    elif state == "pending":
        record["status"] = "pending"
        print(f"  ainda na fila. Depois rode: python scripts/run_jev_pipeline.py --ibm-job-id {job_id}")
    else:
        record["status"] = state.lower()
        try:
            record["error"] = str(job.error_message())
        except Exception:  # noqa: BLE001
            pass
    write_json(out / "ibm_results.json", record)
    print_ibm_record(record, opt)
    write_report(out)
    return 0


def print_ibm_record(record: dict[str, Any], optimal_bitstrings: list[str]) -> None:
    if record.get("status") != "completed":
        print(f"  status do job: {record.get('status')}")
        return
    counts = record["counts"]
    opt_shots = sum(counts.get(b, 0) for b in optimal_bitstrings)
    print(f"  contagens: {counts}")
    print(f"  {opt_shots} de {sum(counts.values())} shots no otimo ({pct(record['optimal_probability'])})")


# ---------------------------------------------------------------- relatorio


def write_report(out: Path) -> None:
    jev = json.loads((out / "jev_responses.json").read_text(encoding="utf-8"))
    qubo = json.loads((out / "qubo_jev.json").read_text(encoding="utf-8"))
    sim_path = out / "simulator_results.json"
    sim = json.loads(sim_path.read_text(encoding="utf-8")) if sim_path.exists() else None
    if sim and sim.get("run_id") != jev["run_id"]:
        sim = None
    ibm = None
    for name in ("ibm_results.json", "ibm_dry_run.json"):
        path = out / name
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("run_id") == jev["run_id"]:
                ibm = (name, data)
                break

    lines = [
        "# Prova Jev + Qiskit (PoC v0.1)",
        "",
        f"Gerado em {utc_now()} (rodada {jev['run_id']}).",
        "",
        "Cenário sintético e ilustrativo. As probabilidades do Jev não foram calibradas com dados reais. "
        "Não demonstra vantagem quântica nem economia operacional real.",
        "",
        f"## 1. Jev ({jev['model']}, {str(jev.get('endpoint', '-')).split('/')[2] if '//' in str(jev.get('endpoint', '')) else '-'})",
        "",
        "| Rota | Risco de atraso (noul) | Condição (choice) | Dificuldade (score 0 a 3) | Tokens entrada/saída |",
        "|---|---:|---|---:|---:|",
    ]
    for route in ("A", "B"):
        s = qubo["signals"][route]
        u = jev_usage(jev["routes"][route])
        conf = s.get("condition_confidence")
        cond = s["condition"] + (f" (confiança {num(conf)})" if conf is not None else "")
        lines.append(
            f"| {route} | {num(s['delay_probability'])} | {cond} | {num(s['access_difficulty_score'])} | {usage_text(u)} |"
        )
    resolved = jev_usage(jev["routes"]["A"])["model"]
    if resolved:
        lines += ["", f"Modelo pedido: `{jev['model']}`. Modelo que respondeu: `{resolved}`."]
    penalty = qubo["delay_penalty_brl"]
    lines += [
        "",
        f"## 2. Custos por rota: base + risco de atraso x multa de {brl(penalty)}",
        "",
        "| Caminhão | Rota A | Rota B |",
        "|---|---:|---:|",
    ]
    for truck, label in (("truck_1", "1"), ("truck_2", "2")):
        c = qubo["costs_with_jev"][truck]
        lines.append(
            f"| {label} | {brl(c['A']['base_brl'])} + {brl(c['A']['risk_cost_brl'])} = {brl(c['A']['total_brl'])} | "
            f"{brl(c['B']['base_brl'])} + {brl(c['B']['risk_cost_brl'])} = {brl(c['B']['total_brl'])} |"
        )
    q0, q1 = qubo["qubo_without_jev"], qubo["qubo_with_jev"]
    lines += [
        "",
        "## 3. QUBO (x = 0 rota A, x = 1 rota B)",
        "",
        f"- Sem Jev (White Paper): `{q0['formula']}`",
        f"- Com Jev: `{q1['formula']}`",
        "",
        "| Estado | Significado | Sem Jev | Com Jev |",
        "|---|---|---:|---:|",
    ]
    for bits in ("00", "01", "10", "11"):
        lines.append(
            f"| {bits} | {describe_bitstring(bits)} | {brl(q0['values_brl'][bits])} | {brl(q1['values_brl'][bits])} |"
        )
    lines += [
        "",
        f"Ótimo sem Jev: {', '.join(q0['optimal_bitstrings'])}. Ótimo com Jev: {', '.join(q1['optimal_bitstrings'])}. "
        + ("O sinal do Jev mudou a decisão." if qubo["decision_changed"] else "O sinal do Jev não mudou a decisão."),
        "",
    ]
    if sim:
        sel = sim["selected_parameters"]
        lines += [
            "## 4. QAOA no simulador ideal",
            "",
            f"Melhor configuração: p = {sel['p']}, seed = {sel['seed']}. "
            f"P(ótimo) = {pct(sel['optimal_probability'])} em {sim['runs'][0]['shots']} shots "
            f"(amostragem uniforme: {pct(sim['uniform_baseline']['optimal_probability'])}).",
            "",
        ]
    lines += ["## 5. IBM Quantum", ""]
    if ibm is None:
        lines.append("Não executado nesta rodada.")
    else:
        name, data = ibm
        if name == "ibm_dry_run.json":
            lines.append(
                f"Dry-run no backend {data['backend']}: profundidade transpilada {data['transpiled_depth']}, "
                f"{data['transpiled_two_qubit_gates']} portas de 2 qubits. Nenhum job enviado."
            )
        elif data.get("status") == "completed":
            counts = data["counts"]
            opt_shots = sum(counts.get(b, 0) for b in q1["optimal_bitstrings"])
            lines.append(
                f"Job {data['job_id']} no backend {data.get('backend') or '-'}: {opt_shots} de {sum(counts.values())} "
                f"shots no ótimo ({pct(data['optimal_probability'])}). Contagens: {counts}."
            )
        else:
            lines.append(f"Job {data.get('job_id')}: status {data.get('status')}.")
    lines += [
        "",
        "Arquivos: jev_responses.json (request e resposta bruta do Jev, sem a chave), qubo_jev.json, "
        "simulator_results.json e, se rodou, ibm_*.json.",
        "",
    ]
    (out / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------- main


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prova Jev + Qiskit do Q-Flow")
    parser.add_argument("--reuse-jev", action="store_true", help="usa as respostas do Jev ja salvas")
    ibm = parser.add_mutually_exclusive_group()
    ibm.add_argument("--ibm-dry-run", action="store_true", help="confere conta, backend e circuito sem enviar job")
    ibm.add_argument("--ibm-execute", action="store_true", help="envia 1 job pro hardware da IBM")
    ibm.add_argument("--ibm-job-id", type=str, default=None, help="busca o resultado de um job ja enviado")
    parser.add_argument("--ibm-backend", type=str, default=None, help="ex: ibm_kingston (padrao: o menos ocupado)")
    parser.add_argument("--ibm-wait-minutes", type=float, default=10.0, help="quanto tempo esperar o job (padrao 10)")
    parser.add_argument(
        "--jev-provider",
        choices=sorted(JEV_PROVIDERS),
        default="typesafe",
        help="typesafe = chave do console.typesafe.ai (padrao) | jevai = chave do thejevai.com",
    )
    parser.add_argument("--jev-model", type=str, default=None, help="padrao: o modelo do provedor escolhido")
    parser.add_argument("--jev-timeout", type=float, default=30.0, help="timeout de cada chamada ao Jev, em segundos")
    parser.add_argument("--delay-penalty", type=float, default=DEFAULT_DELAY_PENALTY_BRL, help="multa de atraso em R$")
    parser.add_argument("--shots", type=int, default=4096)
    parser.add_argument("--credentials-dir", type=str, default=str(DEFAULT_CREDENTIALS))
    parser.add_argument("--results-dir", type=str, default=str(DEFAULT_RESULTS))
    args = parser.parse_args(argv)
    if args.shots <= 0:
        parser.error("--shots tem que ser maior que zero")
    if args.delay_penalty < 0:
        parser.error("--delay-penalty nao pode ser negativa")
    if args.jev_timeout <= 0:
        parser.error("--jev-timeout tem que ser maior que zero")
    if args.ibm_wait_minutes < 0:
        parser.error("--ibm-wait-minutes nao pode ser negativo")
    return args


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(errors="replace")  # terminal do Windows nao quebra com acento
    except Exception:  # noqa: BLE001
        pass
    args = parse_args(argv)
    out = Path(args.results_dir)
    try:
        if args.ibm_dry_run or args.ibm_execute or args.ibm_job_id:
            return run_ibm_phase(args, out)
        return run_jev_phase(args, out)
    except (CredentialError, JevError, PipelineError, ValueError) as exc:
        print(f"\nERRO: {exc}")
        return 1
    except KeyboardInterrupt:
        print("\nInterrompido.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
