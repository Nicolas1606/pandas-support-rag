import csv
import json
from contextlib import closing
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import campo


class FieldTest(unittest.TestCase):
    def test_full_synthetic_workflow(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(campo,"BASE",Path(tmp)):
            base=Path(tmp)
            def cli(*args):
                with patch.object(sys,"argv",["campo",*args]):
                    campo.main()
            for i in range(1,6):
                with patch("builtins.input",side_effect=["sim"]+["","fixture"]*4):
                    cli("sessao",f"P{i:02}")
            cli("cegar")
            sheet=base/"correcao_cega.csv"
            rows=campo.load_csv(sheet)
            self.assertEqual(len(rows),20)
            self.assertEqual(set(rows[0]),{"id","task","answer","correct","notes"})
            for row in rows: row["correct"]="1"
            with sheet.open("w",newline="",encoding="utf8") as file:
                writer=csv.DictWriter(file,fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            with closing(sqlite3.connect(base/"campo.db")) as db, db:
                db.execute("update trials set seconds=case when mode='manual' then 100 else 75 end")
                summary=campo.report(db)
                self.assertTrue(summary["study"]["pilot_gate"])
                self.assertFalse(summary["passed"])
                db.execute("update trials set submitted=0 where mode='assisted'")
                self.assertFalse(campo.report(db)["study"]["pilot_gate"])
            public=campo.ROOT/"evaluation/auditoria_publica/casos.jsonl"
            with self.assertRaisesRegex(ValueError,"publicada"):
                campo.reserved(public,"Autor")
            cases=[json.loads(s) for s in public.read_text(encoding="utf-8-sig").splitlines()]
            for c in cases: c["question"]="Cenário sintético para integração. "+c["question"]
            path=base/"fixtures.jsonl"
            path.write_text("\n".join(json.dumps(c) for c in cases),encoding="utf8")
            campo.reserved(path,"Autor")
            with closing(sqlite3.connect(base/"campo.db")) as db, db:
                self.assertEqual(campo.report(db)["review"]["status"],"pending_review")
                dest=base/"reservado/review.csv"
                dest.write_text(dest.read_text().replace("A1,,,,,","A1,autor,1,1,0,ok"),encoding="utf8")
                with self.assertRaisesRegex(ValueError,"distintos"): campo.report(db)
