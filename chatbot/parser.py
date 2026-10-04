import re
import config

MARK_WORDS = {"maths": ["maths", "math", "mathematics"], "physics": ["physics", "phy"], "chemistry": ["chemistry", "chem"]}
COMM_ALIAS = {"OC": ["oc", "gc", "general", "open"], "BC": ["bc", "backward"], "BCM": ["bcm", "bc muslim"],
              "MBC": ["mbc", "dnc", "mbc/dnc"], "SC": ["sc"], "SCA": ["sca", "arunthathiyar"], "ST": ["st"]}
BRANCH_ALIAS = {"computer science": ["cse", "cs", "computer science", "computer"], "information technology": ["it", "information technology"],
                "electronics and communication": ["ece", "electronics and communication", "electronics"],
                "electrical and electronics": ["eee", "electrical"], "mechanical": ["mech", "mechanical"], "civil": ["civil"],
                "artificial intelligence": ["ai", "aiml", "ai&ds", "aids", "artificial intelligence", "data science"],
                "chemical": ["chemical"], "biotechnology": ["biotech", "biotechnology"]}
TYPE_ALIAS = {"Government": ["government", "govt", "gov"], "Government Aided": ["aided"],
              "Self-Financing": ["private", "self financing", "self-financing"], "University": ["university", "anna university"]}
NUM = r"(-?\d+(?:\.\d+)?)"

def _has(text, word):
    return re.search(r"(?<![a-z0-9])" + re.escape(word) + r"(?![a-z0-9])", text) is not None

def _match(text, table):
    best, blen = None, 0
    for key, words in table.items():
        for w in words:
            if _has(text, w) and len(w) > blen:
                best, blen = key, len(w)
    return best

def _mark(out, field, raw):
    v = float(raw)
    if 0 <= v <= 100: out[field] = v
    else: out["errors"].append(f"{field.capitalize()} mark {raw} is not valid. Enter a mark between 0 and 100.")

def parse(msg, opts, pending=None):
    t = msg.lower().strip()
    out = {"errors": []}
    for field, words in MARK_WORDS.items():
        alt = "|".join(words)
        m = re.search(rf"(?:{alt})\D{{0,15}}?{NUM}", t) or re.search(rf"{NUM}\s*(?:marks?\s*)?(?:in|for|on)\s*(?:{alt})", t)
        if m: _mark(out, field, m.group(1))
    if pending in MARK_WORDS and pending not in out and not out["errors"]:
        m = re.fullmatch(NUM, t)
        if m: _mark(out, pending, m.group(1))
    wants_any = re.search(r"\b(any|no preference|none|skip|anything)\b", t) is not None
    c = _match(t, COMM_ALIAS)
    if c: out["community"] = c
    elif pending == "community" and not wants_any and re.fullmatch(r"[a-z/() ]{1,12}", t):
        out["errors"].append("I don't recognise that community. Choose one of: " + ", ".join(config.COMMUNITIES) + ".")
    kw = _match(t, BRANCH_ALIAS)
    if kw:
        hits = [b for b in opts["branches"] if kw in b.lower()]
        if hits: out["branch"] = hits[0]
        else: out["errors"].append(f"No data for that branch yet. Available branches: {', '.join(opts['branches']) or 'none loaded'}.")
    elif pending == "branch" and t and not wants_any:
        hits = [b for b in opts["branches"] if t in b.lower()]
        if hits: out["branch"] = hits[0]
        else: out["errors"].append(f"I couldn't find that branch. Available branches: {', '.join(opts['branches'])}.")
    for d in opts["districts"]:
        if _has(t, d.lower()): out["district"] = d; break
    ty = _match(t, TYPE_ALIAS)
    if ty and ty in opts["types"]: out["ctype"] = ty
    if wants_any and pending in ("branch", "district"): out[pending] = "any"
    return out
