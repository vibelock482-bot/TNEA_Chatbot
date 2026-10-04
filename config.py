import os
BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DB_PATH", os.path.join(BASE, "tnea.db"))
CSV_PATH = os.path.join(BASE, "data", "colleges.csv")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")   # set on Render to enable /admin
# Chance bands: diff = student_cutoff - historical_cutoff (marks out of 200)
SAFE_MIN = 3.0          # diff >= 3          -> Safe
TARGET_MIN = -3.0       # -3 <= diff < 3     -> Target
AMBITIOUS_MIN = -10.0   # -10 <= diff < -3   -> Ambitious (below that: not shown)
PAGE_SIZE = 5
COMMUNITIES = ["OC", "BC", "BCM", "MBC", "SC", "SCA", "ST"]
DISCLAIMER = ("Recommendations are based on historical cutoff data and are not a guarantee of admission. "
              "Actual TNEA counselling/allotment depends on the official counselling process, rank, category, "
              "seat availability and applicable rules.")
