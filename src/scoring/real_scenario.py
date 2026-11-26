"""Cenario v0.2 com dados reais de fontes publicas (OSRM, Open-Meteo, ANP e ANTT).

Monta ROUTE_STATES, custos base por caminhao e o registro sources.json com
rastreabilidade completa (valor, unidade, URL exata, data/hora e resposta bruta).
Se qualquer fonte falhar ou vier incompleta, levanta RealScenarioError e para.
Nunca usa valores padrao inventados para substituir dados externos.
"""

from __future__ import annotations

import csv
import io
import unicodedata
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

import requests

from src.results_io import utc_now, write_json
from src.scoring.jev_logistics import CONGESTION_BOTH_A_BRL, DEFAULT_DELAY_PENALTY_BRL

# corredor padrao escolhido para a v0.2: Sao Paulo (inicio da Anchieta) -> Porto de Santos (SP)
# o OSRM devolve as alternativas reais; o nome das vias vem do proprio OSRM (steps=true)
DEFAULT_CORRIDOR: dict[str, Any] = {
    "name": "Sao Paulo (Sacoma, SP) -> Santos (Porto de Santos, SP)",
    "state_uf": "SP",
    "origin_name": "Sao Paulo (Sacoma, SP)",
    "origin_lon": -46.6025,
    "origin_lat": -23.6012,
    "destination_name": "Santos (Porto de Santos, SP)",
    "destination_lon": -46.3225,
    "destination_lat": -23.9540,
}

OSRM_BASE_URL = "https://router.project-osrm.org/route/v1/driving"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
ANP_DIESEL_CSV_URL = (
    "https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/"
    "arquivos/shpc/qus/ultimas-4-semanas-diesel-gnv.csv"
)

# ANTT - Portaria SUROC n. 22, de 28/09/2026 (DOU 29/09/2026, vigente desde 30/09/2026)
# Reajusta o Anexo II da Resolucao ANTT n. 5.867/2020 (diesel S10 de referencia: R$ 7,33/L)
# Tabela A (carga lotacao, composicao veicular ou caminhao simples), Carga Geral
ANTT_NORMA = (
    "Portaria SUROC n. 22, de 28/09/2026 (vigente desde 30/09/2026; "
    "Anexo II da Resolucao ANTT n. 5.867/2020; diesel S10 ref. R$ 7,33/L)"
)
ANTT_OFFICIAL_URL = (
    "https://www.gov.br/antt/pt-br/assuntos/ultimas-noticias-antt/"
    "antt-atualiza-coeficientes-do-piso-minimo-do-frete-e-divulga-novo-preco-de-referencia-do-diesel"
)
ANTT_TABLE_URL = "https://www.legisweb.com.br/legislacao/?legislacao=502245"

ANTT_CCD_CARGA_GERAL_BRL_KM: dict[int, float] = {
    5: 6.8284,  # 5 eixos, Tabela A, Carga Geral (R$/km)
    6: 7.5347,  # 6 eixos, Tabela A, Carga Geral (R$/km)
}
ANTT_CC_CARGA_GERAL_BRL: dict[int, float] = {
    5: 657.56,  # coeficiente fixo de carga e descarga (referencia da norma)
    6: 671.93,
}

# os dois caminhoes usam configuracoes diferentes (5 e 6 eixos) para os custos nao ficarem iguais
TRUCK_AXLES: dict[str, int] = {
    "truck_1": 5,
    "truck_2": 6,
}

DEFAULT_HTTP_HEADERS = {
    "User-Agent": "Q-Flow/0.2 (Qiskit Fall Fest 2026; Python requests)",
}


class RealScenarioError(RuntimeError):
    """Erro ao coletar ou validar dados reais das fontes externas."""


def _normalize_text(text: str) -> str:
    """Remove acentos, espacos extras e passa pra minusculo pra comparar cabecalhos."""
    norm = unicodedata.normalize("NFKD", str(text).strip())
    return "".join(ch for ch in norm if not unicodedata.combining(ch)).lower()


def _http_get_checked(
    url: str,
    *,
    source_name: str,
    timeout: float = 20.0,
    http_get: Callable[..., Any] | None = None,
) -> Any:
    """Faz GET e converte falhas de rede ou HTTP ruim em RealScenarioError claro."""
    getter = http_get or requests.get
    try:
        resp = getter(url, headers=DEFAULT_HTTP_HEADERS, timeout=timeout)
    except requests.exceptions.SSLError as exc:
        raise RealScenarioError(
            f"{source_name} falhou por erro de SSL ({url}). Confere proxy, antivirus ou rede."
        ) from exc
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
        raise RealScenarioError(
            f"sem rede ou {source_name} fora do ar ({exc.__class__.__name__}) ao consultar {url}."
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise RealScenarioError(f"erro ao consultar {source_name} ({url}): {exc}") from exc

    status = int(getattr(resp, "status_code", 0))
    if status != 200:
        snippet = " ".join(str(getattr(resp, "text", "")).split())[:200]
        raise RealScenarioError(
            f"{source_name} devolveu HTTP {status} em {url}. Trecho: {snippet or '(sem corpo)'}"
        )
    return resp


def _parse_json_checked(resp: Any, *, source_name: str, url: str) -> dict[str, Any]:
    """Le JSON da resposta e falha com mensagem clara se vier quebrado."""
    try:
        data = resp.json()
    except ValueError as exc:
        snippet = " ".join(str(getattr(resp, "text", "")).split())[:200]
        raise RealScenarioError(
            f"{source_name} devolveu JSON invalido em {url}. Trecho: {snippet or '(sem corpo)'}"
        ) from exc
    if not isinstance(data, dict):
        raise RealScenarioError(f"{source_name} devolveu JSON em formato inesperado (esperava objeto) em {url}.")
    return data


def _route_midpoint(
    route_obj: dict[str, Any],
    origin_lon: float,
    origin_lat: float,
    dest_lon: float,
    dest_lat: float,
) -> tuple[float, float]:
    """Pega o ponto do meio da geometria da rota (ou ponto medio geografico se vier sem coordenadas)."""
    geom = route_obj.get("geometry")
    if isinstance(geom, dict):
        coords = geom.get("coordinates")
        if isinstance(coords, list) and coords:
            mid = coords[len(coords) // 2]
            if isinstance(mid, (list, tuple)) and len(mid) >= 2:
                return float(mid[0]), float(mid[1])
    return (origin_lon + dest_lon) / 2.0, (origin_lat + dest_lat) / 2.0


def _route_summary(route_obj: dict[str, Any], fallback_label: str) -> str:
    """Extrai o nome principal das vias devolvido pelo OSRM, se houver."""
    legs = route_obj.get("legs")
    if isinstance(legs, list) and legs and isinstance(legs[0], dict):
        summary = str(legs[0].get("summary", "")).strip()
        if summary:
            return summary
    return fallback_label


def fetch_osrm_routes(
    origin_lon: float,
    origin_lat: float,
    dest_lon: float,
    dest_lat: float,
    *,
    timeout: float = 20.0,
    http_get: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Consulta o OSRM publico com alternatives=true e exige pelo menos 2 rotas reais."""
    url = (
        f"{OSRM_BASE_URL}/{origin_lon:.6f},{origin_lat:.6f};{dest_lon:.6f},{dest_lat:.6f}"
        "?alternatives=true&overview=simplified&geometries=geojson&steps=true"
    )
    consulted_at = utc_now()
    resp = _http_get_checked(url, source_name="OSRM", timeout=timeout, http_get=http_get)
    body = _parse_json_checked(resp, source_name="OSRM", url=url)

    if body.get("code") != "Ok":
        raise RealScenarioError(f"OSRM retornou erro (code={body.get('code')!r}) em {url}.")

    raw_routes = body.get("routes")
    if not isinstance(raw_routes, list) or len(raw_routes) < 2:
        count = len(raw_routes) if isinstance(raw_routes, list) else 0
        raise RealScenarioError(
            f"OSRM retornou apenas {count} rota(s) em {url}; o cenario exige pelo menos 2 rotas "
            "(uma principal e uma alternativa)."
        )

    parsed: list[dict[str, Any]] = []
    for idx, r in enumerate(raw_routes[:2]):
        if not isinstance(r, dict):
            raise RealScenarioError(f"OSRM devolveu rota #{idx + 1} em formato invalido.")
        try:
            distance_m = float(r["distance"])
            duration_s = float(r["duration"])
        except (KeyError, TypeError, ValueError) as exc:
            raise RealScenarioError(
                f"OSRM devolveu rota #{idx + 1} sem 'distance' ou 'duration' validos."
            ) from exc
        if distance_m <= 0 or duration_s <= 0:
            raise RealScenarioError(
                f"OSRM devolveu distancia/duracao nao positiva na rota #{idx + 1} ({distance_m} m, {duration_s} s)."
            )
        mid_lon, mid_lat = _route_midpoint(r, origin_lon, origin_lat, dest_lon, dest_lat)
        parsed.append(
            {
                "distance_km": round(distance_m / 1000.0, 2),
                "duration_min": round(duration_s / 60.0, 1),
                "summary": _route_summary(r, f"alternativa {idx + 1}"),
                "critical_point": {"lon": round(mid_lon, 5), "lat": round(mid_lat, 5)},
                "raw_excerpt": {
                    "distance_m": distance_m,
                    "duration_s": duration_s,
                    "summary": _route_summary(r, ""),
                },
            }
        )

    # ordena pela menor distancia: rota A = mais curta, rota B = mais longa
    parsed.sort(key=lambda item: (item["distance_km"], item["duration_min"]))
    return {
        "url": url,
        "consultado_em_utc": consulted_at,
        "routes": {"A": parsed[0], "B": parsed[1]},
        "resposta_bruta": {
            "code": body.get("code"),
            "n_routes_returned": len(raw_routes),
            "route_A": parsed[0]["raw_excerpt"],
            "route_B": parsed[1]["raw_excerpt"],
        },
    }


def default_departure_iso_hour(now: datetime | None = None) -> str:
    """Devolve a proxima hora cheia no fuso de Brasilia (UTC-3) no formato YYYY-MM-DDTHH:00."""
    tz_brt = timezone(timedelta(hours=-3))
    current = (now or datetime.now(tz_brt)).astimezone(tz_brt)
    next_hour = (current.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))
    return next_hour.strftime("%Y-%m-%dT%H:00")


def fetch_open_meteo_weather(
    lat: float,
    lon: float,
    departure_hour: str,
    *,
    timeout: float = 20.0,
    http_get: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Consulta previsao de chuva (mm) e vento (km/h) no Open-Meteo para a hora de saida."""
    url = (
        f"{OPEN_METEO_URL}?latitude={lat:.5f}&longitude={lon:.5f}"
        "&hourly=precipitation,wind_speed_10m&timezone=America/Sao_Paulo&forecast_days=2"
    )
    consulted_at = utc_now()
    resp = _http_get_checked(url, source_name="Open-Meteo", timeout=timeout, http_get=http_get)
    body = _parse_json_checked(resp, source_name="Open-Meteo", url=url)

    hourly = body.get("hourly")
    if not isinstance(hourly, dict):
        raise RealScenarioError(f"Open-Meteo devolveu JSON sem bloco 'hourly' em {url}.")

    times = hourly.get("time")
    precip_list = hourly.get("precipitation")
    wind_list = hourly.get("wind_speed_10m")
    if not (isinstance(times, list) and isinstance(precip_list, list) and isinstance(wind_list, list)):
        raise RealScenarioError(
            f"Open-Meteo devolveu listas invalidas em 'hourly' (esperava time, precipitation e wind_speed_10m)."
        )
    if not (len(times) == len(precip_list) == len(wind_list)) or not times:
        raise RealScenarioError("Open-Meteo devolveu vetores 'hourly' vazios ou de tamanhos diferentes.")

    if departure_hour not in times:
        raise RealScenarioError(
            f"Open-Meteo nao trouxe previsao para a hora de saida '{departure_hour}' "
            f"(faixa recebida: {times[0]} ate {times[-1]})."
        )
    idx = times.index(departure_hour)
    raw_precip = precip_list[idx]
    raw_wind = wind_list[idx]
    if raw_precip is None or raw_wind is None:
        raise RealScenarioError(
            f"Open-Meteo retornou valor nulo para chuva ou vento em {departure_hour}."
        )
    try:
        precip_mm = float(raw_precip)
        wind_kmh = float(raw_wind)
    except (TypeError, ValueError) as exc:
        raise RealScenarioError(
            f"Open-Meteo retornou chuva/vento nao numerico em {departure_hour}: {raw_precip!r}, {raw_wind!r}."
        ) from exc

    units = body.get("hourly_units") if isinstance(body.get("hourly_units"), dict) else {}
    return {
        "url": url,
        "consultado_em_utc": consulted_at,
        "departure_hour": departure_hour,
        "precipitation_mm": round(precip_mm, 2),
        "precipitation_unit": str(units.get("precipitation", "mm")),
        "wind_speed_kmh": round(wind_kmh, 2),
        "wind_speed_unit": str(units.get("wind_speed_10m", "km/h")),
        "resposta_bruta": {
            "latitude": body.get("latitude"),
            "longitude": body.get("longitude"),
            "timezone": body.get("timezone"),
            "hourly_units": units,
            "matched_entry": {
                "time": times[idx],
                "precipitation": raw_precip,
                "wind_speed_10m": raw_wind,
            },
        },
    }


def _describe_weather(precip_mm: float, wind_kmh: float, departure_hour: str) -> str:
    """Transforma os numeros reais do Open-Meteo em descricao objetiva pro contexto do Jev."""
    if precip_mm >= 10.0:
        rain_label = "chuva forte"
    elif precip_mm >= 2.0:
        rain_label = "chuva moderada"
    elif precip_mm > 0.0:
        rain_label = "chuva fraca"
    else:
        rain_label = "sem chuva"
    return (
        f"{rain_label} ({precip_mm:.1f} mm/h) e vento de {wind_kmh:.1f} km/h "
        f"no trecho critico as {departure_hour} (Open-Meteo)"
    )


def _find_column(fieldnames: list[str], target_norm: str) -> str | None:
    for name in fieldnames:
        if _normalize_text(name) == target_norm:
            return name
    return None


def _parse_br_date(raw: str) -> date | None:
    text = raw.strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _parse_br_float(raw: str) -> float | None:
    text = raw.strip().replace(",", ".")
    if not text:
        return None
    try:
        val = float(text)
    except ValueError:
        return None
    return val if val > 0 else None


def fetch_anp_diesel_s10(
    state_uf: str,
    *,
    url: str = ANP_DIESEL_CSV_URL,
    timeout: float = 30.0,
    http_get: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Baixa o CSV aberto da ANP (ultimas 4 semanas) e calcula a media do diesel S10 no estado."""
    uf = state_uf.strip().upper()
    if len(uf) != 2:
        raise RealScenarioError(f"UF invalida para consulta na ANP: {state_uf!r}")

    consulted_at = utc_now()
    resp = _http_get_checked(url, source_name="ANP", timeout=timeout, http_get=http_get)

    raw_bytes = getattr(resp, "content", None)
    if isinstance(raw_bytes, (bytes, bytearray)):
        try:
            csv_text = bytes(raw_bytes).decode("utf-8-sig")
        except UnicodeDecodeError:
            csv_text = bytes(raw_bytes).decode("latin-1")
    else:
        csv_text = str(getattr(resp, "text", "")).lstrip("\ufeff")

    if not csv_text.strip():
        raise RealScenarioError(f"ANP devolveu CSV vazio em {url}.")

    reader = csv.DictReader(io.StringIO(csv_text), delimiter=";")
    if not reader.fieldnames:
        raise RealScenarioError(f"ANP devolveu CSV sem cabecalho valido em {url}.")

    col_uf = _find_column(reader.fieldnames, "estado - sigla")
    col_prod = _find_column(reader.fieldnames, "produto")
    col_date = _find_column(reader.fieldnames, "data da coleta")
    col_price = _find_column(reader.fieldnames, "valor de venda")
    col_muni = _find_column(reader.fieldnames, "municipio")

    missing_cols = [
        label
        for label, col in (
            ("Estado - Sigla", col_uf),
            ("Produto", col_prod),
            ("Data da Coleta", col_date),
            ("Valor de Venda", col_price),
        )
        if col is None
    ]
    if missing_cols:
        raise RealScenarioError(
            f"CSV da ANP veio sem colunas obrigatorias ({', '.join(missing_cols)}) em {url}."
        )

    by_week: dict[tuple[int, int], list[tuple[date, float, dict[str, str]]]] = {}
    for row in reader:
        row_uf = str(row.get(col_uf, "")).strip().upper()
        row_prod = _normalize_text(row.get(col_prod, ""))
        if row_uf != uf or row_prod != "diesel s10":
            continue
        dt = _parse_br_date(str(row.get(col_date, "")))
        price = _parse_br_float(str(row.get(col_price, "")))
        if dt is None or price is None:
            continue
        iso = dt.isocalendar()
        week_key = (iso[0], iso[1])
        sample = {
            "estado": row_uf,
            "municipio": str(row.get(col_muni, "")).strip() if col_muni else "",
            "produto": str(row.get(col_prod, "")).strip(),
            "data_coleta": dt.isoformat(),
            "valor_venda_brl": price,
        }
        by_week.setdefault(week_key, []).append((dt, price, sample))

    if not by_week:
        raise RealScenarioError(
            f"CSV da ANP nao tem precos validos de DIESEL S10 para o estado {uf} em {url}."
        )

    latest_week = max(by_week.keys())
    entries = by_week[latest_week]
    prices = [p for _, p, _ in entries]
    dates = [d for d, _, _ in entries]
    avg_price = round(sum(prices) / len(prices), 4)
    week_start = min(dates).isoformat()
    week_end = max(dates).isoformat()

    return {
        "url": url,
        "consultado_em_utc": consulted_at,
        "state_uf": uf,
        "average_price_brl_l": avg_price,
        "week_iso": f"{latest_week[0]}-W{latest_week[1]:02d}",
        "week_range": f"{week_start} a {week_end}",
        "sample_count": len(prices),
        "resposta_bruta": {
            "semana_iso": f"{latest_week[0]}-W{latest_week[1]:02d}",
            "periodo_coleta": f"{week_start} a {week_end}",
            "n_amostras": len(prices),
            "amostra_linhas": [s for _, _, s in entries[:5]],
        },
    }


def compute_antt_base_costs(
    distances_km: dict[str, float],
    *,
    truck_axles: dict[str, int] | None = None,
) -> dict[str, dict[str, float]]:
    """Custo base por caminhao e rota: distancia_km x coeficiente CCD da ANTT (Tabela A, Carga Geral)."""
    axles_map = truck_axles or TRUCK_AXLES
    costs: dict[str, dict[str, float]] = {}
    for truck, axles in axles_map.items():
        if axles not in ANTT_CCD_CARGA_GERAL_BRL_KM:
            raise RealScenarioError(
                f"numero de eixos {axles} sem coeficiente ANTT cadastrado (use 5 ou 6)."
            )
        ccd = ANTT_CCD_CARGA_GERAL_BRL_KM[axles]
        costs[truck] = {}
        for route in ("A", "B"):
            dist = float(distances_km[route])
            if dist <= 0:
                raise RealScenarioError(f"distancia invalida para a rota {route}: {dist}")
            costs[truck][route] = round(dist * ccd, 2)
    return costs


def build_real_scenario(
    *,
    corridor: dict[str, Any] | None = None,
    departure_hour: str | None = None,
    delay_penalty_brl: float = DEFAULT_DELAY_PENALTY_BRL,
    congestion_both_a_brl: float = CONGESTION_BOTH_A_BRL,
    timeout: float = 20.0,
    http_get: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Consulta OSRM, Open-Meteo e ANP, aplica ANTT e monta route_states, base_costs e sources."""
    corr = corridor or DEFAULT_CORRIDOR
    dep_hour = departure_hour or default_departure_iso_hour()

    osrm = fetch_osrm_routes(
        float(corr["origin_lon"]),
        float(corr["origin_lat"]),
        float(corr["destination_lon"]),
        float(corr["destination_lat"]),
        timeout=timeout,
        http_get=http_get,
    )

    weather: dict[str, dict[str, Any]] = {}
    for route in ("A", "B"):
        pt = osrm["routes"][route]["critical_point"]
        weather[route] = fetch_open_meteo_weather(
            pt["lat"],
            pt["lon"],
            dep_hour,
            timeout=timeout,
            http_get=http_get,
        )

    anp = fetch_anp_diesel_s10(
        str(corr["state_uf"]),
        timeout=max(timeout, 30.0),
        http_get=http_get,
    )

    distances_km = {
        "A": osrm["routes"]["A"]["distance_km"],
        "B": osrm["routes"]["B"]["distance_km"],
    }
    base_costs = compute_antt_base_costs(distances_km)
    consulted_antt = utc_now()

    route_states: dict[str, dict[str, Any]] = {}
    # rotulo so com o que o OSRM devolveu: nome das vias e qual e a mais curta (nada de "serra" chutado)
    for route, role_label in (("A", "alternativa mais curta pelo OSRM"), ("B", "alternativa mais longa pelo OSRM")):
        r_info = osrm["routes"][route]
        w_info = weather[route]
        route_states[route] = {
            "rota": f"{route} - {r_info['summary']} ({role_label})",
            "corredor": corr["name"],
            "distancia_km": r_info["distance_km"],
            "duracao_estimada_min": r_info["duration_min"],
            "ponto_critico_coords": r_info["critical_point"],
            "clima_previsto": _describe_weather(
                w_info["precipitation_mm"], w_info["wind_speed_kmh"], dep_hour
            ),
            "precipitacao_mm_h": w_info["precipitation_mm"],
            "vento_km_h": w_info["wind_speed_kmh"],
            "diesel_s10_estado_brl_l": round(anp["average_price_brl_l"], 2),
            "diesel_s10_semana_anp": anp["week_range"],
            "saida_prevista": dep_hour,
            "tipo_carga": "carga geral (ANTT Tabela A, caminhoes de 5 e 6 eixos)",
        }

    sources: dict[str, Any] = {
        "scenario": "real",
        "corridor": corr,
        "departure_hour": dep_hour,
        "generated_at_utc": utc_now(),
        "items": {
            "rota_A_distancia": {
                "valor": osrm["routes"]["A"]["distance_km"],
                "unidade": "km",
                "url": osrm["url"],
                "consultado_em_utc": osrm["consultado_em_utc"],
                "resposta_bruta": osrm["resposta_bruta"]["route_A"],
            },
            "rota_A_duracao": {
                "valor": osrm["routes"]["A"]["duration_min"],
                "unidade": "min",
                "url": osrm["url"],
                "consultado_em_utc": osrm["consultado_em_utc"],
                "resposta_bruta": osrm["resposta_bruta"]["route_A"],
            },
            "rota_B_distancia": {
                "valor": osrm["routes"]["B"]["distance_km"],
                "unidade": "km",
                "url": osrm["url"],
                "consultado_em_utc": osrm["consultado_em_utc"],
                "resposta_bruta": osrm["resposta_bruta"]["route_B"],
            },
            "rota_B_duracao": {
                "valor": osrm["routes"]["B"]["duration_min"],
                "unidade": "min",
                "url": osrm["url"],
                "consultado_em_utc": osrm["consultado_em_utc"],
                "resposta_bruta": osrm["resposta_bruta"]["route_B"],
            },
            "clima_rota_A_chuva": {
                "valor": weather["A"]["precipitation_mm"],
                "unidade": weather["A"]["precipitation_unit"],
                "url": weather["A"]["url"],
                "consultado_em_utc": weather["A"]["consultado_em_utc"],
                "resposta_bruta": weather["A"]["resposta_bruta"],
            },
            "clima_rota_A_vento": {
                "valor": weather["A"]["wind_speed_kmh"],
                "unidade": weather["A"]["wind_speed_unit"],
                "url": weather["A"]["url"],
                "consultado_em_utc": weather["A"]["consultado_em_utc"],
                "resposta_bruta": weather["A"]["resposta_bruta"],
            },
            "clima_rota_B_chuva": {
                "valor": weather["B"]["precipitation_mm"],
                "unidade": weather["B"]["precipitation_unit"],
                "url": weather["B"]["url"],
                "consultado_em_utc": weather["B"]["consultado_em_utc"],
                "resposta_bruta": weather["B"]["resposta_bruta"],
            },
            "clima_rota_B_vento": {
                "valor": weather["B"]["wind_speed_kmh"],
                "unidade": weather["B"]["wind_speed_unit"],
                "url": weather["B"]["url"],
                "consultado_em_utc": weather["B"]["consultado_em_utc"],
                "resposta_bruta": weather["B"]["resposta_bruta"],
            },
            "diesel_s10_anp": {
                "valor": anp["average_price_brl_l"],
                "unidade": "R$/litro",
                "estado": anp["state_uf"],
                "semana_iso": anp["week_iso"],
                "semana_coleta": anp["week_range"],
                "url": anp["url"],
                "consultado_em_utc": anp["consultado_em_utc"],
                "resposta_bruta": anp["resposta_bruta"],
            },
            "antt_ccd_5_eixos_carga_geral": {
                "valor": ANTT_CCD_CARGA_GERAL_BRL_KM[5],
                "unidade": "R$/km",
                "norma": ANTT_NORMA,
                "url": ANTT_OFFICIAL_URL,
                "url_tabela": ANTT_TABLE_URL,
                "consultado_em_utc": consulted_antt,
                "resposta_bruta": (
                    "Tabela A, Carga Geral, 5 eixos: CCD = 6,8284 R$/km; CC = R$ 657,56 "
                    "(Portaria SUROC n. 22/2026)"
                ),
            },
            "antt_ccd_6_eixos_carga_geral": {
                "valor": ANTT_CCD_CARGA_GERAL_BRL_KM[6],
                "unidade": "R$/km",
                "norma": ANTT_NORMA,
                "url": ANTT_OFFICIAL_URL,
                "url_tabela": ANTT_TABLE_URL,
                "consultado_em_utc": consulted_antt,
                "resposta_bruta": (
                    "Tabela A, Carga Geral, 6 eixos: CCD = 7,5347 R$/km; CC = R$ 671,93 "
                    "(Portaria SUROC n. 22/2026)"
                ),
            },
            "custo_base_truck_1_rota_A": {
                "valor": base_costs["truck_1"]["A"],
                "unidade": "BRL",
                "formula": f"{distances_km['A']} km x {ANTT_CCD_CARGA_GERAL_BRL_KM[5]} R$/km (5 eixos)",
                "url": ANTT_OFFICIAL_URL,
                "consultado_em_utc": consulted_antt,
                "resposta_bruta": "derivado de distancia OSRM x CCD ANTT 5 eixos",
            },
            "custo_base_truck_1_rota_B": {
                "valor": base_costs["truck_1"]["B"],
                "unidade": "BRL",
                "formula": f"{distances_km['B']} km x {ANTT_CCD_CARGA_GERAL_BRL_KM[5]} R$/km (5 eixos)",
                "url": ANTT_OFFICIAL_URL,
                "consultado_em_utc": consulted_antt,
                "resposta_bruta": "derivado de distancia OSRM x CCD ANTT 5 eixos",
            },
            "custo_base_truck_2_rota_A": {
                "valor": base_costs["truck_2"]["A"],
                "unidade": "BRL",
                "formula": f"{distances_km['A']} km x {ANTT_CCD_CARGA_GERAL_BRL_KM[6]} R$/km (6 eixos)",
                "url": ANTT_OFFICIAL_URL,
                "consultado_em_utc": consulted_antt,
                "resposta_bruta": "derivado de distancia OSRM x CCD ANTT 6 eixos",
            },
            "custo_base_truck_2_rota_B": {
                "valor": base_costs["truck_2"]["B"],
                "unidade": "BRL",
                "formula": f"{distances_km['B']} km x {ANTT_CCD_CARGA_GERAL_BRL_KM[6]} R$/km (6 eixos)",
                "url": ANTT_OFFICIAL_URL,
                "consultado_em_utc": consulted_antt,
                "resposta_bruta": "derivado de distancia OSRM x CCD ANTT 6 eixos",
            },
            "multa_atraso": {
                "valor": float(delay_penalty_brl),
                "unidade": "BRL",
                "origem": "parametro da equipe, nao medido",
                "url": None,
                "consultado_em_utc": consulted_antt,
                "resposta_bruta": "parametro da equipe, nao medido",
            },
            "congestionamento_ambos_rota_A": {
                "valor": float(congestion_both_a_brl),
                "unidade": "BRL",
                "origem": "parametro da equipe, nao medido",
                "url": None,
                "consultado_em_utc": consulted_antt,
                "resposta_bruta": "parametro da equipe, nao medido",
            },
        },
    }

    return {
        "scenario": "real",
        "route_states": route_states,
        "base_costs_brl": base_costs,
        "truck_axles": dict(TRUCK_AXLES),
        "congestion_both_a_brl": float(congestion_both_a_brl),
        "delay_penalty_brl": float(delay_penalty_brl),
        "sources": sources,
    }


def save_sources(out_dir: Path, sources: dict[str, Any]) -> Path:
    """Grava sources.json na pasta de resultados da rodada."""
    path = out_dir / "sources.json"
    write_json(path, sources)
    return path
