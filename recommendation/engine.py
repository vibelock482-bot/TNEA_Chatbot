import config


def calc_cutoff(maths, physics, chemistry):
    for name, v in (("Maths", maths), ("Physics", physics), ("Chemistry", chemistry)):
        if not isinstance(v, (int, float)) or isinstance(v, bool) or not 0 <= v <= 100:
            raise ValueError(f"{name} mark must be a number between 0 and 100.")

    return round(maths + physics / 2 + chemistry / 2, 2)


def classify(diff):
    if diff >= config.SAFE_MIN:
        return "Safe"

    if diff >= config.TARGET_MIN:
        return "Target"

    if diff >= config.AMBITIOUS_MIN:
        return "Ambitious"

    return "Reach"


def _query(c, community, branch=None, district=None, ctype=None):
    sql = """SELECT c.*
             FROM colleges c
             JOIN (
                 SELECT college_code, branch, community, MAX(year) y
                 FROM colleges
                 WHERE cutoff IS NOT NULL
                 GROUP BY college_code, branch, community
             ) m
             ON c.college_code=m.college_code
             AND c.branch=m.branch
             AND c.community=m.community
             AND c.year=m.y
             WHERE c.community=?"""

    args = [community]

    if branch:
        sql += " AND LOWER(c.branch)=LOWER(?)"
        args.append(branch)

    if district:
        sql += " AND LOWER(c.district)=LOWER(?)"
        args.append(district)

    if ctype:
        sql += " AND LOWER(c.college_type)=LOWER(?)"
        args.append(ctype)

    return c.execute(sql, args).fetchall()


def _make_result(r, cutoff):
    diff = round(cutoff - r["cutoff"], 2)
    band = classify(diff)

    if diff >= 0:
        rel = f"{abs(diff):g} marks above"
    else:
        rel = f"{abs(diff):g} marks below"

    return {
        "college_code": r["college_code"],
        "college_name": r["college_name"],
        "district": r["district"],
        "college_type": r["college_type"],
        "branch": r["branch"],
        "community": r["community"],
        "historical_cutoff": r["cutoff"],
        "year": r["year"],
        "student_cutoff": cutoff,
        "chance": band,
        "reason": (
            f"Your cutoff is {rel} the "
            f"{r['year']} {r['community']} cutoff of "
            f"{r['cutoff']:g} for this branch."
        )
    }


def recommend(c, cutoff, community, branch=None, district=None,
              ctype=None, chance=None):

    # 1. First try the student's exact filters.
    rows = _query(c, community, branch, district, ctype)

    # 2. If nothing is found, remove district.
    if not rows and district:
        rows = _query(c, community, branch, None, ctype)

    # 3. If still nothing, remove college type.
    if not rows and ctype:
        rows = _query(c, community, branch, None, None)

    # 4. If still nothing, search all branches in Tamil Nadu.
    if not rows and branch:
        rows = _query(c, community, None, None, None)

    out = []

    for r in rows:
        result = _make_result(r, cutoff)

        if chance and result["chance"] != chance:
            continue

        out.append(result)

    # Closest colleges first.
    order = {
        "Target": 0,
        "Safe": 1,
        "Ambitious": 2,
        "Reach": 3
    }

    out.sort(
        key=lambda x: (
            order[x["chance"]],
            abs(x["student_cutoff"] - x["historical_cutoff"])
        )
    )

    # Keep the response useful instead of flooding the chatbot.
    return out[:10]


def explain_empty(c, cutoff, community, branch, district, ctype, chance):
    """Explain why nothing matched."""

    # Check whether the community has any cutoff data.
    if len(_query(c, community)) == 0:
        return [
            f"No historical cutoff data is loaded for the {community} community yet."
        ]

    # If data exists, tell the student that broader matching can be used.
    return [
        "No exact match was found with all your selected filters.",
        "Try removing the district or branch preference to see more Tamil Nadu colleges."
    ]