"""Cliente da API do Jev (thejevai.com).

Manda um state + perguntas tipadas (choice, score, noul) e devolve as respostas
ja conferidas. Formato da API: https://thejevai.com/docs
"""

from __future__ import annotations

import json
import time
from typing import Any, Callable

import requests

# o Jev tem dois lugares pra chamar, cada um com a sua chave:
# jevai = app thejevai.com (resposta vem dentro de code/data) | typesafe = API oficial da TypeSafe
JEV_PROVIDERS: dict[str, dict[str, str]] = {
    "jevai": {
        "url": "https://thejevai.com/v1/systemone",
        "model": "typesafe/jev-1.14",
        "keys_page": "https://thejevai.com/settings/apikeys",
    },
    "typesafe": {
        "url": "https://api.typesafe.ai/v1/systemone",
        "model": "jev-latest",
        "keys_page": "https://console.typesafe.ai/keys",
    },
}
JEV_URL = JEV_PROVIDERS["jevai"]["url"]
JEV_DEFAULT_MODEL = JEV_PROVIDERS["jevai"]["model"]
MAX_QUESTIONS = 8  # limite da API por chamada
MAX_PAYLOAD_BYTES = 32 * 1024  # limite da API: 32 KiB de JSON
RETRY_STATUS = {429, 500, 502, 503, 504, 529}  # vale tentar de novo


class JevError(RuntimeError):
    """Erro na chamada do Jev, com mensagem pronta pra mostrar no terminal."""


def validate_questions(questions: dict[str, dict[str, Any]]) -> None:
    """Confere as perguntas antes de gastar credito."""
    if not isinstance(questions, dict) or not questions:
        raise JevError("precisa de pelo menos 1 pergunta")
    if len(questions) > MAX_QUESTIONS:
        raise JevError(f"a API aceita no maximo {MAX_QUESTIONS} perguntas por chamada")
    for qid, q in questions.items():
        if not isinstance(q, dict):
            raise JevError(f"pergunta {qid}: formato invalido")
        qtype = q.get("type")
        if not str(q.get("instructions", "")).strip():
            raise JevError(f"pergunta {qid}: faltou 'instructions'")
        criteria = q.get("criteria")
        if qtype == "choice":
            if not isinstance(criteria, dict) or len(criteria) < 2:
                raise JevError(f"pergunta {qid}: choice precisa de pelo menos 2 opcoes em 'criteria'")
        elif qtype == "score":
            if not isinstance(criteria, list) or not 2 <= len(criteria) <= 10:
                raise JevError(f"pergunta {qid}: score precisa de 2 a 10 niveis em 'criteria'")
        elif qtype == "noul":
            if criteria is not None and (
                not isinstance(criteria, dict) or set(criteria) - {"true", "false"}
            ):
                raise JevError(f"pergunta {qid}: criteria do noul so aceita 'true' e 'false'")
        else:
            raise JevError(f"pergunta {qid}: tipo {qtype!r} nao existe (use choice, score ou noul)")


def _prob(value: Any, where: str) -> float:
    try:
        p = float(value)
    except (TypeError, ValueError) as exc:
        raise JevError(f"{where}: valor {value!r} nao e numero") from exc
    if not -1e-9 <= p <= 1.0 + 1e-9:
        raise JevError(f"{where}: probabilidade fora de 0 a 1 ({p})")
    return min(max(p, 0.0), 1.0)


def _probs(raw: Any, where: str) -> dict[str, float]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise JevError(f"{where}: 'probabilities' deveria ser um objeto")
    return {str(k): _prob(v, f"{where}.{k}") for k, v in raw.items()}


def parse_answers(
    body: Any, questions: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    """Tira as respostas do JSON do Jev e confere o tipo e a faixa de cada uma."""
    if not isinstance(body, dict):
        raise JevError("resposta do Jev nao e um objeto JSON")
    if body.get("code", 0) != 0:
        raise JevError(f"Jev respondeu com erro (code={body.get('code')}): {body.get('message')}")
    if "data" in body:
        # formato do thejevai.com: {"code": 0, "data": {"result": {"answers": ...}}}
        try:
            answers = body["data"]["result"]["answers"]
        except (KeyError, TypeError) as exc:
            raise JevError("resposta do Jev veio sem data.result.answers") from exc
    elif "answers" in body:
        # formato da API oficial da TypeSafe: {"model": ..., "answers": ..., "usage": ...}
        answers = body["answers"]
    else:
        raise JevError("resposta do Jev veio sem as respostas (answers)")
    if not isinstance(answers, dict):
        raise JevError("data.result.answers deveria ser um objeto")

    parsed: dict[str, dict[str, Any]] = {}
    for qid, q in questions.items():
        a = answers.get(qid)
        if not isinstance(a, dict):
            raise JevError(f"a resposta veio sem a pergunta '{qid}'")
        qtype = q["type"]
        if a.get("type") not in (None, qtype):
            raise JevError(f"{qid}: esperava tipo {qtype}, veio {a.get('type')}")

        if qtype == "noul":
            if "noul" not in a:
                raise JevError(f"{qid}: faltou o campo 'noul'")
            parsed[qid] = {"type": "noul", "noul": _prob(a["noul"], qid)}

        elif qtype == "choice":
            choice = a.get("choice")
            if choice not in q["criteria"]:
                raise JevError(f"{qid}: opcao {choice!r} nao esta entre as opcoes enviadas")
            conf = a.get("confidence")
            parsed[qid] = {
                "type": "choice",
                "choice": choice,
                "probabilities": _probs(a.get("probabilities"), qid),
                "confidence": None if conf is None else _prob(conf, f"{qid}.confidence"),
            }

        else:  # score
            n_levels = len(q["criteria"])
            try:
                score = float(a.get("score"))
            except (TypeError, ValueError) as exc:
                raise JevError(f"{qid}: faltou o campo 'score' ou ele nao e numero") from exc
            if not -1e-9 <= score <= (n_levels - 1) + 1e-9:
                raise JevError(f"{qid}: score {score} fora da faixa 0 a {n_levels - 1}")
            score = min(max(score, 0.0), float(n_levels - 1))
            conf = a.get("confidence")
            parsed[qid] = {
                "type": "score",
                "score": score,
                "score_normalized": score / (n_levels - 1),
                "legend": a.get("legend"),
                "probabilities": _probs(a.get("probabilities"), qid),
                "confidence": None if conf is None else _prob(conf, f"{qid}.confidence"),
            }
    return parsed


def _short_body(resp: Any) -> str:
    try:
        text = resp.text
    except Exception:  # noqa: BLE001
        return "(sem corpo)"
    text = " ".join(str(text).split())
    return text[:300] if text else "(sem corpo)"


def ask_jev(
    state: str | dict[str, Any] | list[str],
    questions: dict[str, dict[str, Any]],
    *,
    api_key: str,
    model: str = JEV_DEFAULT_MODEL,
    url: str = JEV_URL,
    timeout: float = 30.0,
    max_retries: int = 3,
    http_post: Callable[..., Any] | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Faz a chamada no Jev e devolve request (sem a chave), resposta bruta e respostas conferidas."""
    validate_questions(questions)
    if not api_key or not api_key.strip():
        raise JevError("chave do Jev vazia")
    if not model or not model.strip():
        raise JevError("nome do modelo vazio")
    if state is None or (isinstance(state, (str, list, dict)) and not state):
        raise JevError("state vazio: o Jev precisa de contexto pra responder")

    payload = {"model": model, "state": state, "questions": questions}
    size = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    if size > MAX_PAYLOAD_BYTES:
        raise JevError(f"request com {size} bytes, o limite da API e {MAX_PAYLOAD_BYTES}")

    post = http_post or requests.post
    headers = {"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json"}

    last_problem = ""
    for attempt in range(max_retries + 1):
        wait = float(min(2**attempt, 20))
        try:
            resp = post(url, headers=headers, json=payload, timeout=timeout)
        except requests.exceptions.SSLError as exc:
            raise JevError(
                "erro de SSL falando com o Jev. Rede com proxy ou antivirus interceptando? "
                "Tenta outra rede (ex: 4G do celular)."
            ) from exc
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
            last_problem = f"sem conexao ou timeout ({exc.__class__.__name__})"
            if attempt < max_retries:
                sleep(wait)
                continue
            raise JevError(
                f"nao consegui falar com o Jev depois de {max_retries + 1} tentativas: "
                f"{last_problem}. Confere a internet."
            ) from exc

        status = int(getattr(resp, "status_code", 0))
        if status in RETRY_STATUS and attempt < max_retries:
            retry_after = str(resp.headers.get("Retry-After", "")).strip()
            if retry_after.isdigit():
                wait = float(min(int(retry_after), 30))
            last_problem = f"HTTP {status}"
            sleep(wait)
            continue
        if status in (401, 403):
            host = url.split("/")[2] if "//" in url else url
            hint = next((f" A chave pra esse endereco e criada em {v['keys_page']}." for v in JEV_PROVIDERS.values() if v["url"] == url), "")
            raise JevError(
                f"{host} recusou a chave (HTTP {status}).{hint} Se a sua chave veio do outro site, "
                "troque com --jev-provider (jevai = thejevai.com, typesafe = console.typesafe.ai)."
            )
        if status == 402:
            raise JevError(f"Jev diz que faltam creditos (HTTP 402): {_short_body(resp)}")
        if status in (429, 529):
            raise JevError(f"Jev continua ocupado (HTTP {status}). Espera um minuto e roda de novo.")
        if status >= 400 or status == 0:
            raise JevError(f"Jev devolveu HTTP {status}: {_short_body(resp)}")

        try:
            body = resp.json()
        except ValueError as exc:
            raise JevError(f"Jev devolveu algo que nao e JSON: {_short_body(resp)}") from exc

        answers = parse_answers(body, questions)
        return {
            "request": payload,  # sem a chave, ela so vai no header
            "response": body,
            "answers": answers,
            "http_status": status,
            "attempts": attempt + 1,
        }

    raise JevError(f"Jev nao respondeu depois de {max_retries + 1} tentativas ({last_problem})")
