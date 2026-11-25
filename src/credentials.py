"""Leitura das chaves locais que ficam em credentials/ (pasta ignorada pelo git)."""

from __future__ import annotations

import json
from pathlib import Path

# textos de exemplo que a gente pode esquecer de trocar pela chave de verdade
PLACEHOLDERS = {
    "...",
    "cole_aqui",
    "sua_chave",
    "sua_chave_aqui",
    "your_token_here",
    "your-api-key",
    "<api_key>",
    "<your-api-key>",
}


class CredentialError(RuntimeError):
    """Problema com arquivo de credencial (faltando, vazio, corrompido ou com texto de exemplo)."""


def _read_text(path: Path, label: str) -> str:
    try:
        # utf-8-sig tira o BOM que o PowerShell/Notepad as vezes coloca no comeco
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        # Notepad antigo pode salvar como UTF-16
        try:
            return path.read_text(encoding="utf-16")
        except (UnicodeError, OSError) as exc:
            raise CredentialError(
                f"{label}: nao consegui ler {path}. Salve o arquivo como UTF-8."
            ) from exc
    except OSError as exc:
        raise CredentialError(f"{label}: nao consegui ler {path} ({exc})") from exc


def read_secret(
    path: Path | str,
    fields: tuple[str, ...],
    *,
    label: str,
    required: bool = True,
) -> str | None:
    """Le um segredo de um JSON tipo {"apikey": "..."} ou de um arquivo com so a chave.

    Se required=False, arquivo faltando, vazio ou com texto de exemplo devolve None.
    """
    path = Path(path)
    example = json.dumps({fields[0]: "COLE_AQUI"})

    if not path.exists():
        if required:
            raise CredentialError(
                f"{label}: arquivo nao encontrado em {path}. Crie ele com o conteudo {example}"
            )
        return None
    if path.is_dir():
        raise CredentialError(f"{label}: {path} e uma pasta, era pra ser um arquivo")

    text = _read_text(path, label).strip()
    if not text:
        if required:
            raise CredentialError(f"{label}: {path} esta vazio. Conteudo esperado: {example}")
        return None

    if text.startswith("{") or text.startswith("[") or text.startswith('"'):
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise CredentialError(
                f"{label}: {path} esta com JSON invalido (linha {exc.lineno}, coluna {exc.colno}). "
                f"Formato esperado: {example}"
            ) from exc
        if isinstance(data, str):
            value = data
        elif isinstance(data, dict):
            found = [data[f] for f in fields if f in data]
            if not found:
                raise CredentialError(
                    f"{label}: {path} nao tem o campo '{fields[0]}'. Formato esperado: {example}"
                )
            value = found[0]
            if value is None:
                value = ""
            if not isinstance(value, str):
                raise CredentialError(f"{label}: o campo '{fields[0]}' em {path} tem que ser texto")
        else:
            raise CredentialError(f"{label}: {path} tem que ser um objeto JSON. Formato: {example}")
    else:
        # arquivo so com a chave, sem JSON
        if len(text.split()) != 1:
            raise CredentialError(
                f"{label}: {path} tem mais de uma palavra/linha. Deixe so a chave ou use {example}"
            )
        value = text

    value = value.strip()
    if value.lower().startswith("bearer "):
        value = value[7:].strip()

    if not value or value.lower() in PLACEHOLDERS:
        if required:
            raise CredentialError(
                f"{label}: troque o texto de exemplo pela chave de verdade em {path}"
            )
        return None
    if any(ch.isspace() for ch in value):
        raise CredentialError(f"{label}: a chave em {path} tem espaco no meio, confere se colou certo")
    return value
