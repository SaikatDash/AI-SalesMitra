"""Parsing and persistence helpers for user supplied sales datasets."""

import base64
import csv
import hashlib
import json
import math
import os
import re
from io import BytesIO
from typing import Any

import pandas as pd
import requests
from fastapi import HTTPException
from sqlalchemy import Column, Integer, MetaData, String, Table, insert, select
from sqlalchemy.orm import Session

from backend.database import engine
from backend.database_model import UploadedDataset

MAX_UPLOAD_MB = 40
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
MAX_ROWS = 50_000
MAX_COLUMNS = 100
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")


def _gemini_api_key() -> str | None:
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def gemini_generate(
    prompt: str,
    *,
    pdf_bytes: bytes | None = None,
    image_bytes: bytes | None = None,
    image_mime_type: str = "image/png",
    max_output_tokens: int | None = None,
    thinking_level: str | None = None,
    request_timeout: tuple[int, int] = (10, 180),
) -> str:
    api_key = _gemini_api_key()
    if not api_key:
        raise HTTPException(status_code=503, detail="Gemini is not configured. Set GEMINI_API_KEY on the backend.")
    parts: list[dict[str, Any]] = [{"text": prompt}]
    if pdf_bytes is not None:
        parts.append({"inline_data": {"mime_type": "application/pdf", "data": base64.b64encode(pdf_bytes).decode("ascii")}})
    if image_bytes is not None:
        parts.append({"inline_data": {"mime_type": image_mime_type, "data": base64.b64encode(image_bytes).decode("ascii")}})
    generation_config: dict[str, Any] = {"temperature": 0.2}
    if max_output_tokens is not None:
        generation_config["maxOutputTokens"] = max_output_tokens
    if thinking_level is not None:
        generation_config["thinkingConfig"] = {"thinkingLevel": thinking_level}
    try:
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
            headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
            json={
                "contents": [{"parts": parts}],
                "generationConfig": generation_config,
            },
            timeout=request_timeout,
        )
        response.raise_for_status()
        payload = response.json()
        candidates = payload.get("candidates") or []
        parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
        answer_parts = [
            part["text"]
            for part in parts
            if isinstance(part, dict) and part.get("text") and not part.get("thought")
        ]
        answer = "\n".join(answer_parts).strip()
        if not answer:
            raise HTTPException(status_code=502, detail="Gemini returned an empty answer. Check the model response and backend Gemini configuration.")
        return answer
    except HTTPException:
        raise
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else 502
        try:
            provider_message = exc.response.json().get("error", {}).get("message", "") if exc.response is not None else ""
        except ValueError:
            provider_message = ""
        lower_message = provider_message.casefold()
        if status == 403 and "leaked" in lower_message:
            detail = "Google rejected the Gemini API key because it was reported as leaked. Replace it with a newly generated key in the backend environment, then restart or redeploy the backend."
        elif status in {401, 403}:
            detail = "Google rejected the Gemini API key or its project permissions. Check the backend GEMINI_API_KEY and Google AI API access."
        elif status == 429:
            detail = "Gemini rate limit or quota reached. Check the Google AI project quota and retry later."
        elif status == 404:
            detail = f"Gemini model '{GEMINI_MODEL}' was not found or is not enabled for this API key. Check GEMINI_MODEL."
        else:
            detail = f"Gemini returned HTTP {status}. Check the backend Gemini configuration and try again."
        raise HTTPException(status_code=502, detail=detail) from exc
    except requests.Timeout as exc:
        raise HTTPException(
            status_code=504,
            detail="Gemini took too long to respond. Retry with a shorter question or a smaller file/image.",
        ) from exc
    except (requests.RequestException, KeyError, IndexError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"Gemini request failed ({type(exc).__name__}). Check backend connectivity and configuration.") from exc


def _pdf_to_frame(content: bytes) -> pd.DataFrame:
    prompt = (
        "Extract every sales table from this PDF and return ONLY valid JSON with shape "
        '{"columns":["column name"],"rows":[["cell value"]]}. Keep one row per record, '
        "preserve dates and numeric values, ignore page headers/footers, and use empty strings for missing cells. "
        "If there is no tabular sales data, return {\"columns\":[],\"rows\":[]}."
    )
    raw = gemini_generate(prompt, pdf_bytes=content).strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE)
    try:
        payload = json.loads(raw)
        frame = pd.DataFrame(payload.get("rows", []), columns=payload.get("columns", []))
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail="Gemini could not convert the PDF tables into structured rows.") from exc
    if frame.empty:
        raise HTTPException(status_code=422, detail="No tabular data was found in the PDF.")
    return frame


def parse_upload(filename: str, content: bytes) -> pd.DataFrame:
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"Upload limit is {MAX_UPLOAD_MB} MB.")
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    try:
        if suffix == "csv":
            try:
                sample = content[:8192].decode("utf-8-sig")
                encoding = "utf-8-sig"
            except UnicodeDecodeError:
                sample = content[:8192].decode("latin-1")
                encoding = "latin-1"
            try:
                delimiter = csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
            except csv.Error:
                # A one-column CSV has no delimiter to sniff; use the standard comma.
                delimiter = ","
            frame = pd.read_csv(BytesIO(content), sep=delimiter, encoding=encoding)
        elif suffix in {"xlsx", "xlsm"}:
            sheets = pd.read_excel(BytesIO(content), engine="openpyxl", sheet_name=None)
            nonempty_sheets = [(name, sheet.dropna(how="all")) for name, sheet in sheets.items() if not sheet.dropna(how="all").empty]
            if not nonempty_sheets:
                frame = pd.DataFrame()
            elif len(nonempty_sheets) == 1:
                frame = nonempty_sheets[0][1]
            else:
                sheet_column = "source_sheet"
                while sheet_column in {str(column).strip().lower() for _, sheet in nonempty_sheets for column in sheet.columns}:
                    sheet_column = f"_{sheet_column}"
                frame = pd.concat(
                    [sheet.assign(**{sheet_column: name}) for name, sheet in nonempty_sheets],
                    ignore_index=True,
                    sort=False,
                )
        elif suffix == "xls":
            sheets = pd.read_excel(BytesIO(content), engine="xlrd", sheet_name=None)
            nonempty_sheets = [(name, sheet.dropna(how="all")) for name, sheet in sheets.items() if not sheet.dropna(how="all").empty]
            if not nonempty_sheets:
                frame = pd.DataFrame()
            elif len(nonempty_sheets) == 1:
                frame = nonempty_sheets[0][1]
            else:
                sheet_column = "source_sheet"
                while sheet_column in {str(column).strip().lower() for _, sheet in nonempty_sheets for column in sheet.columns}:
                    sheet_column = f"_{sheet_column}"
                frame = pd.concat(
                    [sheet.assign(**{sheet_column: name}) for name, sheet in nonempty_sheets],
                    ignore_index=True,
                    sort=False,
                )
        elif suffix == "pdf":
            frame = _pdf_to_frame(content)
        else:
            raise HTTPException(status_code=415, detail="Supported formats are CSV, XLS, XLSX, XLSM, and PDF.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not read this file: {exc}") from exc

    frame = frame.dropna(how="all").reset_index(drop=True)
    if frame.empty:
        raise HTTPException(status_code=422, detail="The file does not contain any data rows.")
    if len(frame) > MAX_ROWS or len(frame.columns) > MAX_COLUMNS:
        raise HTTPException(status_code=413, detail=f"Files are limited to {MAX_ROWS:,} rows and {MAX_COLUMNS} columns.")
    columns = [str(column).strip() or f"column_{index + 1}" for index, column in enumerate(frame.columns)]
    if len({column.casefold() for column in columns}) != len(columns):
        raise HTTPException(status_code=422, detail="Column names must be unique (ignoring letter case).")
    frame.columns = columns
    return frame


def _column_name(name: str, index: int) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", name.strip().lower()).strip("_") or f"column_{index}"
    if safe[0].isdigit():
        safe = f"c_{safe}"
    return safe[:55]


def _json_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def save_dataset(db: Session, user_id: int, filename: str, content: bytes, frame: pd.DataFrame | None = None) -> tuple[UploadedDataset, bool]:
    digest = hashlib.sha256(content).hexdigest()
    existing = db.query(UploadedDataset).filter_by(user_id=user_id, content_hash=digest).first()
    if existing:
        return existing, False
    frame = frame if frame is not None else parse_upload(filename, content)
    table_name = f"upload_{user_id}_{digest[:20]}"
    used: set[str] = set()
    column_map = []
    for index, original in enumerate(frame.columns, start=1):
        safe = _column_name(str(original), index)
        base = safe
        suffix = 2
        while safe in used or safe == "row_id":
            safe = f"{base[:48]}_{suffix}"
            suffix += 1
        used.add(safe)
        column_map.append({"original": str(original), "column": safe})

    metadata = MetaData()
    table = Table(table_name, metadata, Column("row_id", Integer, primary_key=True), *[
        Column(item["column"], String, nullable=True) for item in column_map
    ])
    table.create(bind=engine, checkfirst=True)
    records = []
    for values in frame.itertuples(index=False, name=None):
        records.append({item["column"]: (None if _json_value(value) is None else str(_json_value(value)))
                        for item, value in zip(column_map, values)})
    try:
        with engine.begin() as connection:
            if records:
                connection.execute(insert(table), records)
        dataset = UploadedDataset(
            user_id=user_id,
            source_name=filename[:255],
            table_name=table_name,
            content_hash=digest,
            columns_json=json.dumps(column_map),
            row_count=len(frame),
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        return dataset, True
    except Exception:
        db.rollback()
        table.drop(bind=engine, checkfirst=True)
        raise


def dataset_frame(db: Session, dataset: UploadedDataset) -> pd.DataFrame:
    columns = json.loads(dataset.columns_json)
    metadata = MetaData()
    table = Table(dataset.table_name, metadata, autoload_with=engine)
    with engine.connect() as connection:
        rows = connection.execute(select(table).order_by(table.c.row_id)).mappings().all()
    records = [{item["original"]: row[item["column"]] for item in columns} for row in rows]
    return pd.DataFrame(records, columns=[item["original"] for item in columns])


def dataset_summary(frame: pd.DataFrame) -> dict[str, Any]:
    numeric = frame.apply(pd.to_numeric, errors="coerce")
    numeric_stats = {}
    for column in frame.columns:
        values = numeric[column].dropna()
        values = values[values.map(math.isfinite)]
        if not values.empty:
            numeric_stats[str(column)] = {
                "sum": float(values.sum()), "mean": float(values.mean()), "min": float(values.min()), "max": float(values.max())
            }
    sample_rows = [
        {str(column): _json_value(value) for column, value in row.items()}
        for row in frame.head(5).to_dict(orient="records")
    ]
    date_ranges = {}
    for column in frame.columns:
        name = str(column).casefold()
        if any(token in name for token in ("date", "day", "month", "time", "period")):
            dates = pd.to_datetime(frame[column], errors="coerce", format="mixed").dropna()
            if not dates.empty:
                date_ranges[str(column)] = {"start": dates.min().date().isoformat(), "end": dates.max().date().isoformat()}
    category_profiles = {}
    for column in frame.columns:
        values = frame[column].dropna()
        if not values.empty and values.nunique() <= 100 and not pd.to_numeric(values, errors="coerce").notna().all():
            category_profiles[str(column)] = values.astype(str).value_counts().head(10).to_dict()
    return {
        "row_count": int(len(frame)),
        "column_count": int(len(frame.columns)),
        "columns": [str(column) for column in frame.columns],
        "numeric_stats": numeric_stats,
        "date_ranges": date_ranges,
        "category_profiles": category_profiles,
        "sample_rows": sample_rows,
    }


def gemini_dataset_insight(frame: pd.DataFrame) -> str:
    summary = dataset_summary(frame)
    summary.pop("sample_rows", None)
    if not _gemini_api_key():
        return "Dataset parsed and saved. Gemini analysis is unavailable until GEMINI_API_KEY is configured on the backend."
    prompt = (
        "You are the AI analyst in a sales analytics dashboard. Analyze the provided aggregate profile of an uploaded dataset. "
        "Explain the available sales KPIs and patterns, useful breakdowns, time coverage when present, and data-quality limitations. "
        "Use only values present below; do not invent values or claim causation. If there is no recognizable sales metric, "
        "say that and suggest which columns the user should inspect. Format as concise markdown.\n"
        + json.dumps(summary, default=str)
    )
    return gemini_generate(
        prompt,
        max_output_tokens=1536,
        thinking_level="low",
        request_timeout=(10, 90),
    )


def gemini_rag_answer(
    query: str,
    context: list[dict[str, str]],
    *,
    image_bytes: bytes | None = None,
    image_mime_type: str = "image/png",
) -> str:
    snippets = "\n\n".join(f"[{doc['title']}] {doc['content']}" for doc in context)
    image_instructions = (
        "The user attached an image. Inspect it for visible app UI, charts, or error messages. Explain what is visible and give concrete steps to fix any error. Do not claim to see information that is not visible.\n\n"
        if image_bytes is not None else ""
    )
    return gemini_generate(
        "You are SalesMitra's AI assistant. Answer the user's actual question directly, including general knowledge "
        "questions. When explaining SalesMitra features, use the retrieved context and never invent app behavior. "
        "Never invent values or conclusions from a user's sales data; ask them to upload/select data or name the "
        "missing column if needed. For data or runtime errors, state the likely cause, what to fix, and practical steps. "
        "If you are uncertain, say so clearly and still provide the most useful safe answer you can.\n\n"
        f"{image_instructions}"
        f"Retrieved context:\n{snippets}\n\nUser question: {query}",
        image_bytes=image_bytes,
        image_mime_type=image_mime_type,
        max_output_tokens=1024,
        thinking_level="low",
        request_timeout=(10, 90),
    )
