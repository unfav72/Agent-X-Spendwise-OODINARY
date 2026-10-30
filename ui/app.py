"""
Spendwise AI - Web Application Backend (Flask)
Serves the dark-mode financial audit dashboard and REST APIs.
"""

import os
import sys

# Ensure root directory is in sys.path when running `python ui/app.py` directly
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import json
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

from database.repository import Repository
from services.transaction_service import TransactionService
from services.recovery_service import RecoveryService
from services.report_service import ReportService
from agent.core import AgentExecutor
from agent.llm import LLM, DryRunLLM
from tools import build_tools
from tools.spending_analytics import execute as run_analytics
from tools.anomaly_detector import execute as run_anomalies
from tools.duplicate_finder import execute as run_duplicates
from tools.recurring_detector import execute as run_recurring
from tools.budget_simulator import execute as run_budget

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32MB max upload
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

repo = Repository()
tx_service = TransactionService(repo)
recovery_service = RecoveryService(repo)
report_service = ReportService(repo)

# Ensure database is seeded on startup
if repo.count_transactions() == 0:
    sample_csv = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sample_transactions.csv")
    if os.path.exists(sample_csv):
        tx_service.ingest_statement(sample_csv)
        recovery_service.scan_for_potential_recoveries()
        run_anomalies(repository=repo)

@app.route("/")
def index():
    return render_template("index.html")

# --- Overview & Dashboard API ---

@app.route("/api/overview", methods=["GET"])
def get_overview():
    overview = repo.get_spending_overview()
    recoveries = recovery_service.get_summary()
    anomalies_list = repo.get_anomalies(status="flagged")
    duplicates = run_duplicates(repository=repo)
    recurring = run_recurring(repository=repo)

    return jsonify({
        "status": "success",
        "overview": overview,
        "recovery_summary": recoveries,
        "anomaly_count": len(anomalies_list),
        "duplicate_count": duplicates.get("candidate_count", 0),
        "recurring_count": recurring.get("recurring_count", 0),
        "total_monthly_recurring": recurring.get("total_monthly_commitment", 0)
    })

# --- Transactions API ---

@app.route("/api/transactions", methods=["GET"])
def get_transactions():
    query = request.args.get("query")
    category = request.args.get("category")
    merchant = request.args.get("merchant")
    txn_type = request.args.get("type")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))

    txns = repo.query_transactions(
        query_text=query,
        category=category,
        merchant=merchant,
        txn_type=txn_type,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
    total_count = repo.count_transactions()
    return jsonify({
        "status": "success",
        "total_records": total_count,
        "transactions": txns
    })

@app.route("/api/transactions/category", methods=["POST"])
def update_category():
    data = request.json or {}
    tx_id = data.get("transaction_id")
    new_cat = data.get("category")
    if not (tx_id and new_cat):
        return jsonify({"status": "error", "message": "Missing transaction_id or category"}), 400

    success = repo.update_transaction_category(tx_id, new_cat)
    return jsonify({"status": "success" if success else "error"})

# --- AI Investigation API ---

@app.route("/api/investigate", methods=["POST"])
def investigate():
    data = request.json or {}
    query = data.get("query", "").strip()
    language = data.get("language", "English")

    if not query:
        return jsonify({"status": "error", "message": "Query cannot be empty"}), 400

    # Prefix language instruction if non-English
    agent_query = query
    if language != "English":
        agent_query = f"The user asks in {language}: '{query}'. Respond in {language} with exact financial calculations and numbers."

    # Select LLM
    has_keys = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GROQ_API_KEY"))
    llm = LLM() if has_keys else DryRunLLM()

    try:
        executor = AgentExecutor(llm, build_tools())
        answer, trace = executor.run(agent_query, verbose=True)

        inv_id = f"inv_{datetime_now_str()}"
        repo.log_investigation(inv_id, query, "completed", answer, language=language)
        for idx, step in enumerate(trace):
            repo.log_trace_step(
                inv_id,
                idx,
                step.get("thought", ""),
                step.get("tool", ""),
                step.get("args", {}),
                step.get("observation", ""),
                "Executed"
            )

        return jsonify({
            "status": "success",
            "investigation_id": inv_id,
            "answer": answer,
            "trace": trace,
            "language": language
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "trace": []
        }), 500

# --- Anomaly & Duplicates API ---

@app.route("/api/anomalies", methods=["GET"])
def get_anomalies():
    run_anomalies(repository=repo)
    anomalies = repo.get_anomalies()
    duplicates = run_duplicates(repository=repo)
    return jsonify({
        "status": "success",
        "anomalies": anomalies,
        "duplicates": duplicates.get("duplicate_candidates", [])
    })

# --- Recovery Center API ---

@app.route("/api/recoveries", methods=["GET"])
def get_recoveries():
    recovery_service.scan_for_potential_recoveries()
    records = recovery_service.get_all()
    summary = recovery_service.get_summary()
    return jsonify({
        "status": "success",
        "summary": summary,
        "records": records
    })

@app.route("/api/recoveries/claim", methods=["POST"])
def manual_claim():
    data = request.json or {}
    tx_id = data.get("transaction_id")
    notes = data.get("notes", "User requested refund investigation")
    if not tx_id:
        return jsonify({"status": "error", "message": "Missing transaction_id"}), 400

    res = recovery_service.register_manual_recovery_claim(tx_id, notes=notes)
    if res:
        return jsonify({"status": "success", "record": res})
    return jsonify({"status": "error", "message": "Transaction not found or not a debit"}), 404

# --- Budget Simulator API ---

@app.route("/api/budget/simulate", methods=["POST"])
def simulate_budget():
    data = request.json or {}
    reductions = data.get("reductions", {})
    flat_caps = data.get("flat_caps", {})
    result = run_budget(reductions=reductions, flat_caps=flat_caps, repository=repo)
    return jsonify(result)

# --- Upload Statement API ---

@app.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file part in request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"status": "error", "message": "No selected file"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    try:
        count, report = tx_service.ingest_statement(filepath)
        # Scan for recoveries & anomalies on newly ingested records
        recovery_service.scan_for_potential_recoveries()
        run_anomalies(repository=repo)

        return jsonify({
            "status": "success",
            "filename": filename,
            "transactions_ingested": count,
            "report": report
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# --- Report Download API ---

@app.route("/api/report/download", methods=["GET"])
def download_report():
    try:
        pdf_path = report_service.generate_pdf_report()
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=os.path.basename(pdf_path),
            mimetype="application/pdf"
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Demo Reset API ---

@app.route("/api/demo/reset", methods=["POST"])
def reset_demo():
    repo.reset_all()
    sample_csv = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sample_transactions.csv")
    if os.path.exists(sample_csv):
        tx_service.ingest_statement(sample_csv)
        recovery_service.scan_for_potential_recoveries()
        run_anomalies(repository=repo)
    return jsonify({"status": "success", "message": "Demo data refreshed with 168 synthetic transactions."})

def datetime_now_str():
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d%H%M%S")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Spendwise AI on http://127.0.0.1:{port}", file=sys.stderr)
    app.run(host="0.0.0.0", port=port, debug=False)

