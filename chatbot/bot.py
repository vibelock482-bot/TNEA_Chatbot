import re
import config
from database import db
from recommendation import engine
from chatbot.parser import parse

ASK = {"maths": "What is your Maths mark (0-100)?", "physics": "What is your Physics mark (0-100)?",
       "chemistry": "What is your Chemistry mark (0-100)?",
       "community": "Which community are you? (" + ", ".join(config.COMMUNITIES) + ")",
       "branch": "Which branch do you prefer? Say a branch like CSE or ECE, or 'any'.",
       "district": "Which district do you prefer? Say a district, or 'any'."}
ORDER = ["maths", "physics", "chemistry", "community", "branch", "district"]

def new_state():
    return {k: None for k in ORDER} | {"ctype": None, "chance": None, "offset": 0, "pending": "maths"}

def _word(t, w):
    return re.search(rf"\b{w}\b", t) is not None

def handle(msg, state):
    s = new_state() | (state or {})
    t = msg.lower().strip()
    c = db.conn(); opts = db.options(c)
    try:
        if re.search(r"\b(reset|start over|restart)\b", t):
            return "Okay, starting over. " + ASK["maths"], new_state(), None
        p = parse(msg, opts, s["pending"])
        if p["errors"]:
            return " ".join(p["errors"]), s, None
        for k in ORDER + ["ctype"]:
            if k in p: s[k] = p[k]; s["offset"] = 0
        for band in ("safe", "target", "ambitious"):
            if _word(t, band): s["chance"] = band.capitalize(); s["offset"] = 0
        if re.search(r"around my cutoff|moderate", t): s["chance"] = "Target"; s["offset"] = 0
        if re.search(r"clear filters|show all", t): s["chance"] = s["ctype"] = None; s["offset"] = 0
        more = _word(t, "more")
        show = more or bool(re.search(r"\b(show|list|recommend|colleges?|suggest)\b", t))
        need = next((k for k in ORDER if s[k] is None), None)
        if need and not (show and need in ("branch", "district") and s["community"]):
            s["pending"] = need
            head = ""
            if need != "maths" and None not in (s["maths"], s["physics"], s["chemistry"]) and need in ("community", "branch", "district"):
                head = f"Your cutoff is {engine.calc_cutoff(s['maths'], s['physics'], s['chemistry']):g}/200. "
            return head + ASK[need], s, None
        s["pending"] = None
        if more: s["offset"] += config.PAGE_SIZE
        cut = engine.calc_cutoff(s["maths"], s["physics"], s["chemistry"])
        f = lambda v: None if v in (None, "any") else v
        args = (cut, s["community"], f(s["branch"]), f(s["district"]), f(s["ctype"]))
        res = engine.recommend(c, *args, chance=s["chance"])
        if not res:
            tips = engine.explain_empty(c, *args, s["chance"])
            return (f"No colleges matched your cutoff of {cut:g} with the current filters. You can try:\n- " + "\n- ".join(tips)), s, {"cards": [], "total": 0}
        page = res[s["offset"]: s["offset"] + config.PAGE_SIZE]
        if not page:
            return f"That was all {len(res)} matches. Say 'clear filters' or try another branch or district.", s, {"cards": [], "total": len(res)}
        filt = ", ".join(x for x in [f(s["branch"]), f(s["district"]), s["ctype"], s["chance"]] if x) or "none"
        return (f"Your cutoff is {cut:g}/200 ({s['community']}). Showing {s['offset']+1}-{s['offset']+len(page)} of {len(res)}. "
                f"Filters: {filt}. Say 'show more' for the next set."), s, {"cards": page, "total": len(res), "disclaimer": config.DISCLAIMER}
    finally:
        c.close()
