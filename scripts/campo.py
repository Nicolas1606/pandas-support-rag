"""Facilitated study. All individual records stay under the ignored data directory."""
import argparse
import csv
import hashlib
import json
import random
import re
import secrets
from contextlib import closing
import sqlite3
import time
import unicodedata
from pathlib import Path

from pilot import ROOT, load_csv, quality, run, utility

BASE = ROOT / "data" / "campo"
SCHEDULES = (
    ("A1m", "B2a", "A2a", "B1m"), ("A1a", "B2m", "A2m", "B1a"),
    ("B1a", "A2m", "B2m", "A1a"), ("B1m", "A2a", "B2a", "A1m"),
)


def tasks():
    text = (ROOT / "docs/piloto_campo/SESSAO.md").read_text(encoding="utf-8-sig")
    return dict(re.findall(r"^\| ([AB][12]) \| (.*?) \|$", text, re.M))


def csv_new(path, fields, rows):
    with path.open("x", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def session(db, person):
    if not re.fullmatch(r"P[0-9]{2}", person) or person == "P00":
        raise ValueError("Use P01 a P99.")
    if input("Consentimento registrado pelo facilitador? [sim] ").strip().lower() != "sim":
        return
    schedule = SCHEDULES[(int(person[1:]) - 1) % len(SCHEDULES)]
    for slot in schedule:
        task, mode = slot[:2], {"m":"manual", "a":"assisted"}[slot[-1]]
        if db.execute("select 1 from trials where person=? and task=?", (person,task)).fetchone():
            continue
        input(f"Condição {mode}. Prepare a documentação e pressione Enter para iniciar.")
        token = secrets.token_hex(8)
        # An interrupted trial keeps the predeclared timeout outcome.
        with db:
            db.execute("insert into trials values (?,?,?,?,?,?,?)", (token,person,task,mode,300,"",0))
        start = time.perf_counter()
        print(tasks()[task], flush=True)
        answer = input("Cole código e explicação em uma linha e pressione Enter: ").strip()
        seconds = time.perf_counter() - start
        if answer and seconds < 300:
            with db:
                db.execute("update trials set seconds=?,answer=?,submitted=1 where token=?",
                           (seconds,answer,token))


def blind(db):
    rows = [{"id":token,"task":tasks()[task],"answer":answer,"correct":"","notes":""}
            for token,task,answer in db.execute("select token,task,answer from trials")]
    if not rows:
        raise ValueError("Ainda não há entregas.")
    random.SystemRandom().shuffle(rows)
    csv_new(BASE/"correcao_cega.csv", list(rows[0]), rows)


def signature(question):
    decomposed = unicodedata.normalize("NFKD", question.casefold())
    return " ".join(re.findall(r"[a-z0-9]+", "".join(c for c in decomposed if not unicodedata.combining(c))))


def strings(obj):
    if isinstance(obj,str):
        yield obj
    elif isinstance(obj,(list,dict)):
        for value in (obj.values() if isinstance(obj,dict) else obj):
            yield from strings(value)


def reserved(path, author):
    raw = path.read_bytes()
    cases = [json.loads(line) for line in raw.decode("utf-8-sig").splitlines() if line.strip()]
    public = set()
    for f in (ROOT/"evaluation").rglob("*"):
        if f.suffix in (".json",".jsonl"):
            text = f.read_text(encoding="utf-8-sig")
            contents = json.loads(text) if f.suffix == ".json" else [json.loads(x) for x in text.splitlines() if x.strip()]
            public.update(signature(x) for x in strings(contents))
    keys = [signature(c["question"]) for c in cases]
    actions = [c["expected_action"] for c in cases]
    if not all(keys) or len(set(keys)) != len(keys) or public.intersection(keys):
        raise ValueError("Pergunta vazia, repetida ou já publicada. Envie casos inéditos.")
    if actions.count("answer") < 20 or len(actions)-actions.count("answer") < 10 or not {"clarify","handoff"} <= set(actions):
        raise ValueError("Inclua 20 respondíveis e 10 de triagem, cobrindo ambas as ações.")
    dest = BASE/"reservado"
    run(path,dest)
    digest = hashlib.sha256((dest/"responses.json").read_bytes()).hexdigest()
    (dest/"origem.json").write_text(json.dumps(dict(author=author.strip().casefold(),responses_sha256=digest)),encoding="utf8")


def report(db):
    review = {"status":"pending_cases"}
    dest = BASE/"reservado"
    if dest.exists():
        meta = json.loads((dest/"origem.json").read_text())
        if hashlib.sha256((dest/"responses.json").read_bytes()).hexdigest()!=meta["responses_sha256"]:
            raise ValueError("Respostas alteradas após a execução.")
        if any(r["reviewer"].strip().casefold()==meta["author"] for r in load_csv(dest/"review.csv")):
            raise ValueError("Use revisores distintos do autor dos casos.")
        review = quality(dest)
    trials = list(db.execute("select token,person,task,mode,seconds,submitted from trials"))
    study = {"status":"pending_participants","attempts":len(trials)}
    sheet = BASE/"correcao_cega.csv"
    if sheet.exists():
        rows = load_csv(sheet)
        grades = {row["id"]:row["correct"] for row in rows}
        if len(rows)!=len(grades) or set(grades)!={row[0] for row in trials}:
            raise ValueError("A ficha precisa conter todas as tentativas, uma vez cada.")
        if all(grade in ("0","1") for grade in grades.values()):
            import tempfile
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder)/"study.csv"
                measurements = [dict(participant=p,task_pair=t[0],method=m,seconds=s,correct=grades[k] if ok else "0")
                                for k,p,t,m,s,ok in trials]
                csv_new(path, ["participant","task_pair","method","seconds","correct"], measurements)
                study = utility(path)
                complete = len(trials)==4*len({r[1] for r in trials})
                study["pilot_gate"] = bool(study.get("pilot_gate") and complete)
        else:
            study["status"]="pending_grades"
    return dict(review=review, study=study, passed=bool(review.get("pilot_gate") and study.get("pilot_gate")))


def main():
    parser=argparse.ArgumentParser()
    sub=parser.add_subparsers(dest="command",required=True)
    sub.add_parser("sessao").add_argument("participant")
    reserved_parser=sub.add_parser("reservado")
    reserved_parser.add_argument("cases",type=Path)
    reserved_parser.add_argument("author")
    sub.add_parser("cegar")
    sub.add_parser("resultado")
    args=parser.parse_args()
    BASE.mkdir(parents=True,exist_ok=True)
    with closing(sqlite3.connect(BASE/"campo.db")) as db, db:
        db.execute("create table if not exists trials(token text primary key,person text,task text,mode text,seconds real,answer text,submitted integer,unique(person,task))")
        if args.command=="sessao": session(db,args.participant)
        elif args.command=="cegar": blind(db)
        elif args.command=="reservado":
            if not args.author.strip(): parser.error("Identifique o autor por pseudônimo.")
            reserved(args.cases,args.author)
        else: print(json.dumps(report(db),indent=2))


if __name__=="__main__":
    main()
