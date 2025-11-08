from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Dict, List

BASE_LISTING_URL_TEMPLATE = "https://www.airbnb.com.ar/rooms/{listing_id}"


def parse_establecimientos_csv(csv_path: Path) -> List[Dict[str, str]]:
    listings: List[Dict[str, str]] = []
    with csv_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            airbnb_url = (row.get("Airbnb") or "").strip()
            if not airbnb_url or "/rooms/" not in airbnb_url:
                continue
            listing_id = airbnb_url.split("/rooms/")[-1].split("?")[0].split("/")[0]
            listing_id = listing_id.strip()
            if not listing_id:
                continue
            listing_url = airbnb_url or BASE_LISTING_URL_TEMPLATE.format(
                listing_id=listing_id
            )
            listings.append(
                {
                    "listing_id": listing_id,
                    "Establecimiento": (row.get("Establecimiento") or "").strip(),
                    "Airbnb": listing_url,
                }
            )
    return listings


def _select_token_indices(token: str, total: int) -> List[int]:
    if "-" in token:
        start_str, end_str = token.split("-", 1)
        if not (start_str.isdigit() and end_str.isdigit()):
            raise ValueError(f"Rango inválido: '{token}'")
        start = int(start_str)
        end = int(end_str)
        if start < 1 or end < start or end > total:
            raise ValueError(f"Rango fuera de límites: '{token}'")
        return list(range(start, end + 1))
    if token.isdigit():
        idx = int(token)
        if idx < 1 or idx > total:
            raise ValueError(f"Índice fuera de límites: '{token}'")
        return [idx]
    return []


essential_stopwords = {"de", "la", "el", "los", "las", "y", "del"}


def select_listings_by_tokens(
    listings: List[Dict[str, str]], selector: str
) -> List[Dict[str, str]]:
    tokens = [tok.strip() for tok in re.split(r"[\s,]+", selector) if tok.strip()]
    if not tokens:
        raise ValueError("No se especificaron selecciones válidas.")

    if any(tok.lower() in {"all", "todos"} for tok in tokens):
        return list(listings)

    selected: List[Dict[str, str]] = []
    seen_ids = set()

    for token in tokens:
        # Ignorar stopwords muy frecuentes para reducir ambigüedad
        if token.lower() in essential_stopwords:
            continue
        matched_items: List[Dict[str, str]] = []

        idx_list = _select_token_indices(token, len(listings))
        if idx_list:
            for idx in idx_list:
                item = listings[idx - 1]
                if item["listing_id"] not in seen_ids:
                    matched_items.append(item)
            selected.extend(matched_items)
            seen_ids.update(item["listing_id"] for item in matched_items)
            continue

        # Coincidencia por ID exacto
        for item in listings:
            if item["listing_id"] == token:
                matched_items = [item]
                break

        # Coincidencia por nombre (subcadena, case-insensitive)
        if not matched_items:
            normalized = token.lower()
            candidates = [
                item
                for item in listings
                if normalized in item.get("Establecimiento", "").lower()
            ]
            if len(candidates) == 1:
                matched_items = candidates
            elif len(candidates) > 1:
                raise ValueError(
                    f"Selección ambigua '{token}': coincide con varios establecimientos"
                )

        if not matched_items:
            raise ValueError(
                f"No se encontró un establecimiento que coincida con '{token}'"
            )

        for item in matched_items:
            listing_id = item["listing_id"]
            if listing_id not in seen_ids:
                selected.append(item)
                seen_ids.add(listing_id)

    if not selected:
        raise ValueError("La selección no produjo resultados.")

    return selected
