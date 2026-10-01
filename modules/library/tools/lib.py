# -*- coding: utf-8 -*-
"""库层。五个库统一读写接口。"""
import json, os, datetime, difflib
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB  = os.path.join(ROOT, "library")
CFG  = os.path.join(ROOT, "config")

def cfg(n): return json.load(open(os.path.join(CFG, n), encoding="utf-8"))
def _p(*a): return os.path.join(LIB, *a)

def read_jsonl(path):
    if not os.path.exists(path): return []
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]

def write_jsonl(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")

def append_jsonl(path, row):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

VAULTS = {
    "persona":  _p("personas", "roster.jsonl"),
    "location": _p("locations", "roster.jsonl"),
    "prop":     _p("props", "roster.jsonl"),
    "beat":     _p("beats", "beats.jsonl"),
    "codex":    _p("codex", "codex.jsonl"),
    "events":   _p("codex", "events.jsonl"),
}

def load(v):  return read_jsonl(VAULTS[v])
def save(v, rows): write_jsonl(VAULTS[v], rows)
def add(v, row): append_jsonl(VAULTS[v], row)

def aesthetics(): return json.load(open(_p("aesthetics", "templates.json"), encoding="utf-8"))

def sim(a, b): return difflib.SequenceMatcher(None, a or "", b or "").ratio()
def today(): return datetime.date.today().isoformat()

def next_id(v, prefix):
    rows = load(v)
    n = max([int(r["id"].split("-")[-1]) for r in rows if r.get("id","").startswith(prefix)] or [0])
    return f"{prefix}-{n+1:04d}"
