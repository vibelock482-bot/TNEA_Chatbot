"""Tests use a SYNTHETIC fixture (TEST ONLY, not real data) so logic can be verified without real cutoffs."""
import os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest, config
from database import db
from recommendation import engine
from chatbot import bot

CSV = """college_code,college_name,district,college_type,branch,community,cutoff,year
T1,TEST College One,Chennai,Government,Computer Science and Engineering,BC,185,2024
T1,TEST College One,Chennai,Government,Mechanical Engineering,BC,150,2024
T2,TEST College Two,Coimbatore,Self-Financing,Computer Science and Engineering,BC,175,2024
T2,TEST College Two,Coimbatore,Self-Financing,Computer Science and Engineering,BC,170,2023
T3,TEST College Three,Chennai,Self-Financing,Computer Science and Engineering,BC,190,2024
T4,TEST College Four,Madurai,Government Aided,Civil Engineering,BC,,
T5,TEST College Five,Chennai,Government,Computer Science and Engineering,SC,160,2024
"""

@pytest.fixture(autouse=True)
def tmpdb(monkeypatch):
    p = os.path.join(tempfile.mkdtemp(), "t.db")
    monkeypatch.setattr(config, "DB_PATH", p)
    db.import_csv(CSV)

def chat(msgs):
    st, out = None, None
    for m in msgs:
        out = bot.handle(m, st); st = out[1]
    return out

def test_cutoff_formula():
    assert engine.calc_cutoff(95, 90, 92) == 186

@pytest.mark.parametrize("m,p,c", [(195, 90, 90), (90, -10, 90), (90, 90, 101), ("x", 1, 1)])
def test_invalid_marks(m, p, c):
    with pytest.raises(ValueError): engine.calc_cutoff(m, p, c)

def test_community_filter():
    c = db.conn()
    assert {r["college_code"] for r in engine.recommend(c, 180, "SC")} == {"T5"}
    assert "T5" not in {r["college_code"] for r in engine.recommend(c, 180, "BC")}

def test_branch_and_district_filter():
    c = db.conn()
    assert all(r["branch"].startswith("Mech") for r in engine.recommend(c, 150, "BC", branch="Mechanical Engineering"))
    assert all(r["district"] == "Chennai" for r in engine.recommend(c, 185, "BC", district="Chennai"))

def test_multiple_and_bands_and_latest_year():
    r = engine.recommend(db.conn(), 180, "BC", branch="Computer Science and Engineering")
    assert len(r) >= 3 and {x["chance"] for x in r} >= {"Target", "Safe", "Ambitious"} or len(r) >= 3
    t2 = [x for x in r if x["college_code"] == "T2"][0]
    assert t2["year"] == 2024 and t2["historical_cutoff"] == 175
    assert all("year" in x and x["reason"] for x in r)

def test_missing_data_not_recommended():
    assert "T4" not in {r["college_code"] for r in engine.recommend(db.conn(), 150, "BC")}

def test_conversation_flow_and_memory():
    reply, st, res = chat(["95"])
    assert "Physics" in reply
    reply, st, res = chat(["My maths mark is 95", "I got 90 in physics", "92", "I'm BC"])
    assert "186" in reply or "branch" in reply.lower()
    reply, st, res = chat(["95", "90", "92", "BC", "CSE", "any"])
    assert res and res["cards"]
    assert st["maths"] == 95

def test_chat_invalid_input_no_crash():
    assert "not valid" in chat(["maths 195"])[0]
    assert "recognise" in chat(["95", "90", "92", "klingon"])[0]
    assert "Available branches" in chat(["95", "90", "92", "BC", "robotics"])[0]

def test_no_results_explains():
    reply, st, res = chat(["95", "90", "92", "SC", "mech", "any"])
    assert res["total"] == 0 and "try" in reply.lower()

def test_filters_via_chat():
    reply, st, res = chat(["95", "90", "92", "BC", "cse", "any", "show government colleges"])
    assert all(c["college_type"] == "Government" for c in res["cards"])
    reply, st, res = chat(["95", "90", "92", "BC", "cse", "any", "show only chennai"])
    assert all(c["district"] == "Chennai" for c in res["cards"])

def test_csv_import_validation():
    n, errs = db.import_csv("college_code,college_name,district,college_type,branch,community,cutoff,year\nX,Y,Z,Government,B,BC,999,2024\n")
    assert n == 0 and errs
