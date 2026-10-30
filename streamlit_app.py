"""
Spendwise AI - Streamlit Dashboard
Autonomous Financial Auditor & Anomaly Hunter
"""

import os
import sys
import tempfile
import pandas as pd
import streamlit as st
from datetime import datetime

# Ensure project root is in sys.path
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

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

# Page configuration
st.set_page_config(
    page_title="Spendwise AI — Financial Auditor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme polish
st.markdown("""
<style>
    .main { background-color: #0B0F19; color: #F8FAFC; }
    .stMetric { background-color: #131B2E; padding: 15px; border-radius: 10px; border: 1px solid #1E293B; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #131B2E; border-radius: 6px; padding: 8px 16px; color: #94A3B8; }
    .stTabs [aria-selected="true"] { background-color: #0284C7; color: white; }
</style>
""", unsafe_allow_html=True)

# Initialize Services
repo = Repository()
tx_service = TransactionService(repo)
recovery_service = RecoveryService(repo)
report_service = ReportService(repo)

# --- Sidebar ---
st.sidebar.title("🛡️ Spendwise AI")
st.sidebar.caption("Autonomous Financial Auditor & Anomaly Hunter")

tx_count = repo.count_transactions()
st.sidebar.metric("Audited Transactions", f"{tx_count:,}")

# LLM provider info
has_keys = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GROQ_API_KEY"))
provider_label = "Gemini / Groq Active" if has_keys else "Autonomous Engine"
st.sidebar.info(f"🧠 Intelligence: **{provider_label}**")

nav = st.sidebar.radio(
    "Navigation",
    [
        "📤 Upload Statement",
        "📊 Overview Dashboard",
        "🤖 AI Investigation",
        "🔄 Recovery Center",
        "⚠️ Anomaly & Duplicates",
        "🎚️ Budget Simulator",
        "📋 Transactions Explorer",
        "📑 Audit PDF Report"
    ]
)

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Clear Entire Ledger", help="Wipes all transactions and recovery records"):
    repo.reset_all()
    st.sidebar.success("Ledger wiped clean!")
    st.rerun()

# --- Helper Formatters ---
def fmt_inr(val):
    if val is None or pd.isna(val):
        return "₹0.00"
    return f"₹{float(val):,.2f}"

# =========================================================================
# 1. UPLOAD STATEMENT
# =========================================================================
if nav == "📤 Upload Statement":
    st.title("📤 Ingest Your Financial Statement")
    st.write("Upload your bank statement, credit card bill, or UPI export. Supported formats: **CSV, Excel (.xlsx, .xls), and PDF**.")

    uploaded_file = st.file_uploader(
        "Drag and drop your financial statement here",
        type=["csv", "xlsx", "xls", "pdf"],
        help="Spendwise AI extracts, normalizes, validates, and audits all transaction rows."
    )

    if uploaded_file is not None:
        if st.button("🚀 Process & Ingest Statement", type="primary"):
            with st.spinner("Extracting, normalizing dates & amounts, and auditing ledger..."):
                ext = os.path.splitext(uploaded_file.name)[1].lower()
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name

                try:
                    count, report = tx_service.ingest_statement(tmp_path)
                    os.remove(tmp_path)

                    # Trigger initial anomaly scan & recovery detection on new data
                    recovery_service.scan_for_potential_recoveries()
                    run_anomalies(repository=repo)

                    st.success(f"✅ Successfully ingested **{count}** transactions from `{uploaded_file.name}`!")
                    
                    # Metrics from validation report
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Valid Records Ingested", report.get("valid_records", count))
                    c2.metric("Rejected / Corrupted", report.get("rejected_records", 0))
                    c3.metric("Duplicate Ref IDs Flagged", report.get("duplicate_ref_count", 0))

                    if report.get("warnings"):
                        with st.expander("Inspection Warnings"):
                            for w in report["warnings"]:
                                st.warning(w)

                    st.info("👉 Switch to **Overview Dashboard** or **AI Investigation** to examine your transactions.")
                except Exception as e:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                    st.error(f"Failed to process statement: {e}")

# =========================================================================
# 2. OVERVIEW DASHBOARD
# =========================================================================
elif nav == "📊 Overview Dashboard":
    st.title("📊 Financial Telemetry & Spending Overview")

    if tx_count == 0:
        st.warning("No transactions currently loaded. Please go to **Upload Statement** to ingest your financial records.")
    else:
        ov = repo.get_spending_overview()
        rec = recovery_service.get_summary()

        # Top Metric Cards
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Income", fmt_inr(ov["total_income"]))
        m2.metric("Total Outlays", fmt_inr(ov["total_expense"]))
        m3.metric("Net Balance", fmt_inr(ov["net_balance"]), help="Ledger scope: Credits minus debits")
        m4.metric("Verified Recoveries", fmt_inr(rec["total_confirmed"]), delta=f"-{fmt_inr(rec['total_unresolved'])} unresolved")

        st.markdown("---")

        # Charts row
        c_left, c_right = st.columns([1.4, 1])

        with c_left:
            st.subheader("Monthly Spending Trajectory")
            trend_data = ov.get("monthly_trend", [])
            if trend_data:
                df_trend = pd.DataFrame(trend_data)
                df_trend = df_trend.rename(columns={"month": "Month", "debit_total": "Debits (Expenses)", "credit_total": "Credits (Income)"})
                df_trend = df_trend.set_index("Month")
                st.bar_chart(df_trend[["Debits (Expenses)", "Credits (Income)"]])
            else:
                st.info("Insufficient monthly intervals for trend charting.")

        with c_right:
            st.subheader("Category Breakdown")
            cat_data = ov.get("categories", [])
            if cat_data:
                df_cat = pd.DataFrame(cat_data).head(7)
                df_cat = df_cat.set_index("category")
                st.bar_chart(df_cat["total_spent"])

        # Recent transactions preview
        st.subheader("Recent Activity")
        recent = repo.query_transactions(limit=10)
        if recent:
            df_recent = pd.DataFrame(recent)[["transaction_date", "merchant", "description", "category", "debit", "credit", "reference_id"]]
            df_recent["debit"] = df_recent["debit"].apply(lambda v: fmt_inr(v) if v > 0 else "-")
            df_recent["credit"] = df_recent["credit"].apply(lambda v: fmt_inr(v) if v > 0 else "-")
            st.dataframe(df_recent, use_container_width=True, hide_index=True)

# =========================================================================
# 3. AI INVESTIGATION (GENUINE AGENTIC REACT)
# =========================================================================
elif nav == "🤖 AI Investigation":
    st.title("🤖 Autonomous AI Financial Auditor")
    st.write("Ask natural-language financial questions. The agent plans, executes genuine analytical tools against your ledger, observes the facts, and synthesizes evidence-backed answers.")

    # Multi-language selector
    lang_col, _ = st.columns([1, 2])
    with lang_col:
        lang = st.selectbox(
            "Language",
            ["English", "Tamil (தமிழ்)", "Hindi (हिन्दी)", "Telugu (తెలుగు)", "Malayalam (മലയാളം)"]
        )

    # Quick action prompt buttons
    st.write("##### Quick Audit Queries")
    q_cols = st.columns(5)
    sample_q = None
    if q_cols[0].button("📈 Why spending increased?"):
        sample_q = "Why did my spending increase this month?"
    if q_cols[1].button("👯 Duplicate charges?"):
        sample_q = "Did I pay the same merchant twice?"
    if q_cols[2].button("🔄 Refund status?"):
        sample_q = "Did I receive the refund for my payment?"
    if q_cols[3].button("🎚️ Simulate budget cuts"):
        sample_q = "What happens if I reduce food delivery by 15% and shopping by 20%?"
    if q_cols[4].button("🔁 Recurring payments"):
        sample_q = "What are my recurring subscriptions?"

    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display past messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "trace" in msg and msg["trace"]:
                with st.expander(f"🔍 Agent Activity Trace ({len(msg['trace'])} Tool Iterations)"):
                    for idx, step in enumerate(msg["trace"], 1):
                        st.markdown(f"**Iteration {idx}: Tool `{step.get('tool')}`**")
                        st.markdown(f"*Thought:* {step.get('thought')}")
                        st.code(f"Args: {step.get('args')}\nObservation:\n{step.get('observation')}")

    # Chat input
    user_query = st.chat_input("Enter your financial audit question...")
    if sample_q:
        user_query = sample_q

    if user_query:
        # Display user message
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        # Run autonomous agent
        with st.chat_message("assistant"):
            with st.spinner("Agent planning tool sequence and auditing ledger..."):
                target_lang = lang.split(" ")[0]
                agent_query = user_query
                if target_lang != "English":
                    agent_query = f"The user asks in {target_lang}: '{user_query}'. Respond in {target_lang} with exact numbers."

                has_keys = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GROQ_API_KEY"))
                llm = LLM() if has_keys else DryRunLLM()
                executor = AgentExecutor(llm, build_tools())

                try:
                    answer, trace = executor.run(agent_query, verbose=False)
                    st.markdown(answer)

                    # Show trace expander
                    if trace:
                        with st.expander(f"🔍 Live Agent Activity Trace ({len(trace)} Steps)"):
                            for idx, step in enumerate(trace, 1):
                                st.markdown(f"**Step {idx}: Executed Tool `{step.get('tool')}`**")
                                st.markdown(f"**Decision Rationale:** {step.get('thought')}")
                                st.code(f"Tool Args: {step.get('args')}\n\nActual Observation:\n{step.get('observation')}")

                    st.session_state.messages.append({"role": "assistant", "content": answer, "trace": trace})
                except Exception as e:
                    err_msg = f"Audit execution error: {type(e).__name__}: {e}"
                    st.error(err_msg)
                    st.session_state.messages.append({"role": "assistant", "content": err_msg})

# =========================================================================
# 4. RECOVERY CENTER (CORE NOVELTY)
# =========================================================================
elif nav == "🔄 Recovery Center":
    st.title("🔄 Recovery Center & Refund Verification Engine")
    st.markdown("""
    **Core Novelty:** Spendwise AI strictly enforces verifiable accounting rules.
    *Potential refunds are separated from verified recoveries. Only confirmed inbound credits received in your ledger count towards realized recovered money.*
    """)

    recovery_service.scan_for_potential_recoveries()
    summary = recovery_service.get_summary()
    records = recovery_service.get_all()

    # Recovery KPIs
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Tracked Cases", summary["total_cases"])
    r2.metric("Potential Claims", fmt_inr(summary["total_potential"]))
    r3.metric("Verified Credits Received", fmt_inr(summary["total_confirmed"]), delta="Confirmed Realized")
    r4.metric("Unresolved Risk", fmt_inr(summary["total_unresolved"]), delta="-Remaining Exposure")

    st.markdown("---")

    st.subheader("Recovery Cases & Audit Timeline")
    if not records:
        st.info("No disputed or failed transactions currently flagged for recovery.")
    else:
        for r in records:
            status_color = "🟢" if r["status"] == "confirmed_recovery" else ("🟡" if r["status"] == "partially_confirmed" else "🔴")
            with st.container():
                st.markdown(f"#### {status_color} {r['merchant']} — Status: `{r['status'].replace('_', ' ').upper()}`")
                
                c_a, c_b, c_c = st.columns(3)
                c_a.write(f"**Original Debit:** {fmt_inr(r['potential_amount'])}")
                c_b.write(f"**Verified Credit:** :green[{fmt_inr(r['confirmed_amount'])}]")
                c_c.write(f"**Remaining Unresolved:** :orange[{fmt_inr(r['unresolved_amount'])}]")

                st.caption(f"Original Date: {r['original_date']} | Original Ref: {r.get('original_reference') or 'N/A'}")
                if r.get("notes"):
                    st.write(f"*Audit Notes:* {r['notes']}")

                # Show linked credits
                links = r.get("links", [])
                if links:
                    st.write("**Linked Verified Credit Inflows:**")
                    df_links = pd.DataFrame(links)[["credit_date", "credit_desc", "linked_amount", "confidence_score"]]
                    df_links["linked_amount"] = df_links["linked_amount"].apply(fmt_inr)
                    df_links["confidence_score"] = df_links["confidence_score"].apply(lambda v: f"{int(v*100)}%")
                    st.dataframe(df_links, hide_index=True)
                else:
                    st.warning("⚠️ No matching inbound credit has arrived yet in your statement records.")

                st.markdown("---")

    # Manual Claim Registration
    with st.expander("➕ Register a Transaction for Refund/Dispute Investigation"):
        tx_id_input = st.text_input("Transaction ID to investigate (from Transactions Explorer)")
        dispute_notes = st.text_input("Dispute Description (e.g. Failed merchant payment, duplicate deduction)")
        if st.button("Submit for Recovery Tracking"):
            if tx_id_input:
                res = recovery_service.register_manual_recovery_claim(tx_id_input, notes=dispute_notes)
                if res:
                    st.success(f"Registered transaction `{tx_id_input}` for recovery audit!")
                    st.rerun()
                else:
                    st.error("Transaction not found or not a debit charge.")

# =========================================================================
# 5. ANOMALY & DUPLICATES
# =========================================================================
elif nav == "⚠️ Anomaly & Duplicates":
    st.title("⚠️ Anomaly Detection & Duplicate Charge Candidates")

    tab1, tab2 = st.tabs(["⚡ Statistical Spikes & Outliers", "👯 Duplicate Charge Candidates"])

    with tab1:
        run_anomalies(repository=repo)
        anomalies = repo.get_anomalies()
        st.subheader(f"Flagged Spending Anomalies ({len(anomalies)})")

        if not anomalies:
            st.info("No statistical outliers detected in current ledger.")
        else:
            for a in anomalies:
                amt = a.get("amount") if a.get("amount") is not None else a.get("debit", 0.0)
                conf = int(a.get("confidence", 1.0) * 100)
                with st.container():
                    col_m, col_amt = st.columns([3, 1])
                    col_m.markdown(f"**{a.get('merchant', 'Unknown')}** (`{a.get('category', 'Other')}`) — *{a.get('anomaly_type', 'anomaly').replace('_', ' ').title()}*")
                    col_amt.markdown(f"### :red[{fmt_inr(amt)}]")
                    st.write(f"**Reason:** {a.get('reason', '')}")
                    st.caption(f"Date: {a.get('transaction_date', 'N/A')} | Historical Category Mean: {fmt_inr(a.get('historical_baseline', 0))} | Delta: +{fmt_inr(a.get('delta_amount', 0))} | Confidence: {conf}%")
                    st.write(f"👉 *Action:* {a.get('recommended_action', 'Review invoice')}")
                    st.markdown("---")

    with tab2:
        duplicates = run_duplicates(repository=repo)
        candidates = duplicates.get("duplicate_candidates", [])
        st.subheader(f"Duplicate Charge Candidates ({len(candidates)})")

        if not candidates:
            st.info("No suspicious duplicate charge pairs identified.")
        else:
            for d in candidates:
                with st.container():
                    st.markdown(f"#### ⚠️ {d['merchant']} — Identical Charge of `{fmt_inr(d['amount'])}`")
                    st.write(f"**Confidence:** :orange[{int(d['confidence']*100)}% Match] | **Reason:** {d['reason']}")

                    p = d["primary_transaction"]
                    dup = d["duplicate_transaction"]

                    c1, c2 = st.columns(2)
                    with c1:
                        st.info(f"**Primary Transaction**\n\nDate: {p['date']}\n\nDesc: {p['description']}\n\nRef: {p.get('reference') or 'N/A'}")
                    with c2:
                        st.info(f"**Duplicate Candidate**\n\nDate: {dup['date']}\n\nDesc: {dup['description']}\n\nRef: {dup.get('reference') or 'N/A'}")

                    st.caption(f"Recommendation: {d.get('recommended_action')}")
                    st.markdown("---")

# =========================================================================
# 6. BUDGET SIMULATOR
# =========================================================================
elif nav == "🎚️ Budget Simulator":
    st.title("🎚️ Deterministic Budget Rebalancing Simulator")
    st.write("Adjust category expenditure cuts to simulate projected monthly and annual savings using deterministic mathematics.")

    col_sliders, col_results = st.columns([1, 1.2])

    with col_sliders:
        st.subheader("Spending Trimming Parameters")
        cut_food = st.slider("Food Delivery Reduction", 0, 60, 15, step=5, format="%d%%")
        cut_shop = st.slider("Shopping Reduction", 0, 60, 20, step=5, format="%d%%")
        cut_ent = st.slider("Entertainment Reduction", 0, 60, 10, step=5, format="%d%%")
        cut_trans = st.slider("Transport Optimization", 0, 50, 10, step=5, format="%d%%")
        cut_fuel = st.slider("Fuel Optimization", 0, 40, 5, step=5, format="%d%%")

    reductions = {
        "Food delivery": float(cut_food),
        "Shopping": float(cut_shop),
        "Entertainment": float(cut_ent),
        "Transport": float(cut_trans),
        "Fuel": float(cut_fuel)
    }

    sim = run_budget(reductions=reductions, repository=repo)

    with col_results:
        st.subheader("Projected Savings")

        b1, b2 = st.columns(2)
        b1.metric("Current Monthly Outlays", fmt_inr(sim["current_total_monthly_spend"]))
        b2.metric("Projected Monthly Outlays", fmt_inr(sim["projected_total_monthly_spend"]), delta=f"-{sim['overall_percentage_reduction']}%")

        b3, b4 = st.columns(2)
        b3.metric("Monthly Projected Savings", fmt_inr(sim["monthly_hypothetical_savings"]), delta="Hypothetical Savings")
        b4.metric("Annualized Projected Savings", fmt_inr(sim["annualized_hypothetical_savings"]), delta="12-Month Run-Rate")

        st.warning("⚠️ **Strict Accounting Rule:** Projected hypothetical savings do not constitute realized cash flow and explicitly exclude pending unverified refunds.")

        st.subheader("Category Rebalancing Detail")
        breakdown = sim.get("category_breakdown", [])
        if breakdown:
            df_sim = pd.DataFrame(breakdown)[["category", "current_monthly_spend", "proposed_monthly_spend", "percentage_reduction", "monthly_expected_saving"]]
            df_sim["current_monthly_spend"] = df_sim["current_monthly_spend"].apply(fmt_inr)
            df_sim["proposed_monthly_spend"] = df_sim["proposed_monthly_spend"].apply(fmt_inr)
            df_sim["monthly_expected_saving"] = df_sim["monthly_expected_saving"].apply(fmt_inr)
            df_sim["percentage_reduction"] = df_sim["percentage_reduction"].apply(lambda v: f"{v}%")
            st.dataframe(df_sim, hide_index=True, use_container_width=True)
        else:
            st.info("No categories available to rebalance. Ingest your statement to view budget projections.")

# =========================================================================
# 7. TRANSACTIONS EXPLORER
# =========================================================================
elif nav == "📋 Transactions Explorer":
    st.title("📋 Transactions Explorer & Category Editor")

    # Search & filters
    f1, f2, f3 = st.columns([2, 1, 1])
    search_q = f1.text_input("🔍 Search merchant, description, or reference...")
    cat_filter = f2.selectbox("Filter Category", ["All", "Food and groceries", "Food delivery", "Shopping", "Transport", "Fuel", "Bills and utilities", "Subscriptions", "Healthcare", "Entertainment", "Education", "Income", "Other"])
    type_filter = f3.selectbox("Filter Movement", ["All Movements", "Debits Only", "Credits Only"])

    txn_type = "debit" if type_filter == "Debits Only" else ("credit" if type_filter == "Credits Only" else None)
    cat_arg = None if cat_filter == "All" else cat_filter

    txns = repo.query_transactions(query_text=search_q, category=cat_arg, txn_type=txn_type, limit=500)
    st.caption(f"Showing **{len(txns)}** matching transactions.")

    if txns:
        df_txns = pd.DataFrame(txns)[["id", "transaction_date", "merchant", "description", "category", "debit", "credit", "reference_id"]]
        df_txns["debit"] = df_txns["debit"].apply(lambda v: fmt_inr(v) if v > 0 else "-")
        df_txns["credit"] = df_txns["credit"].apply(lambda v: fmt_inr(v) if v > 0 else "-")
        st.dataframe(df_txns, use_container_width=True, hide_index=True)

        # Inline Category Correction
        with st.expander("✏️ Correct / Override Transaction Category"):
            st.write("Correcting a category updates the transaction and teaches the normalizer to remember this merchant rule for future statements.")
            c_id, c_cat, c_btn = st.columns([1.5, 1.5, 1])
            selected_tx_id = c_id.text_input("Enter Transaction ID to recategorize")
            new_cat_choice = c_cat.selectbox("New Category", ["Food and groceries", "Food delivery", "Shopping", "Transport", "Fuel", "Bills and utilities", "Subscriptions", "Healthcare", "Entertainment", "Education", "Income", "Other"])
            if c_btn.button("Save Category Correction"):
                if selected_tx_id:
                    ok = repo.update_transaction_category(selected_tx_id, new_cat_choice)
                    if ok:
                        st.success(f"Updated `{selected_tx_id}` to `{new_cat_choice}`!")
                        st.rerun()
                    else:
                        st.error("Transaction ID not found.")

# =========================================================================
# 8. AUDIT PDF REPORT
# =========================================================================
elif nav == "📑 Audit PDF Report":
    st.title("📑 Formal Financial Audit Report (PDF)")
    st.write("Generate a publication-grade PDF audit document with KPI matrices, spending trajectories, flagged anomalies, duplicate candidates, and verifiable recovery accounting.")

    if tx_count == 0:
        st.warning("No transactions loaded. Ingest a statement first before exporting a report.")
    else:
        with st.spinner("Compiling deterministic audit bundle..."):
            pdf_path = report_service.generate_pdf_report()

            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

            st.download_button(
                label="📥 Download Audit PDF Report",
                data=pdf_bytes,
                file_name=os.path.basename(pdf_path),
                mime="application/pdf",
                type="primary"
            )

        st.success("✅ Audit PDF generated successfully with ReportLab!")
        st.info("The report includes complete verification certificates, mathematical proofs, and statutory auditor disclaimers.")

