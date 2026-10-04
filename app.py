from flask import Flask, jsonify, render_template, request, Response
import config
from database import db
from chatbot import bot

app = Flask(__name__)
db.ensure_db()

@app.get("/")
def index():
    return render_template("index.html", disclaimer=config.DISCLAIMER)

@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    msg = str(data.get("message", ""))[:300]
    if not msg.strip():
        return jsonify(reply="Type a message to continue.", state=data.get("state") or bot.new_state(), results=None)
    try:
        reply, state, results = bot.handle(msg, data.get("state"))
    except Exception:
        app.logger.exception("chat error")
        return jsonify(reply="Something went wrong. Say 'reset' to start again.", state=bot.new_state(), results=None)
    return jsonify(reply=reply, state=state, results=results)

@app.get("/api/college/<code>")
def college(code):
    community = request.args.get("community", "OC")
    c = db.conn()
    rows = c.execute("SELECT * FROM colleges WHERE college_code=? ORDER BY branch, year DESC", (code,)).fetchall()
    c.close()
    if not rows:
        return jsonify(error="College not found"), 404
    r0 = rows[0]
    return jsonify(college_code=code, college_name=r0["college_name"], district=r0["district"], college_type=r0["college_type"],
                   branches=[{"branch": r["branch"], "community": r["community"], "cutoff": r["cutoff"], "year": r["year"]} for r in rows
                             if r["community"] == community] or "Historical data unavailable")

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not config.ADMIN_TOKEN:
        return "Admin disabled. Set ADMIN_TOKEN to enable.", 403
    msg = ""
    if request.method == "POST":
        if request.form.get("token") != config.ADMIN_TOKEN:
            return "Wrong token.", 403
        f = request.files.get("file")
        if f:
            n, errs = db.import_csv(f.read().decode("utf-8-sig"))
            msg = f"Loaded {n} rows. " + (f"{len(errs)} skipped: " + "; ".join(errs[:5]) if errs else "No errors.")
    return Response(f"""<h2>Update college data</h2><p>{msg}</p>
    <form method=post enctype=multipart/form-data>Token <input type=password name=token><br><br>
    CSV <input type=file name=file accept=.csv><br><br><button>Upload and replace data</button></form>
    <p>Columns: {', '.join(db.COLS)}. Leave cutoff blank if unavailable.</p>""", mimetype="text/html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
