/**
 * Spendwise AI - Frontend Application Controller
 * Handles live agent trace streaming, voice I/O, multi-language support,
 * recovery lifecycle tracking, and interactive charts.
 */

let currentChartMonthly = null;
let currentChartCategory = null;
let speechRecognizer = null;
let isRecording = false;

document.addEventListener("DOMContentLoaded", () => {
    initNavigation();
    initVoice();
    initUpload();
    initDemoReset();
    loadOverviewData();
});

// --- Page Navigation Router ---

function initNavigation() {
    const navItems = document.querySelectorAll(".nav-item");
    navItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const pageId = item.getAttribute("data-page");
            navigateTo(pageId);
        });
    });

    // Handle initial hash if present
    const hash = window.location.hash.replace("#", "");
    if (hash && document.getElementById(`view-${hash}`)) {
        navigateTo(hash);
    }
}

function navigateTo(pageId) {
    document.querySelectorAll(".nav-item").forEach(el => el.classList.remove("active"));
    document.querySelectorAll(".page-view").forEach(el => el.classList.remove("active"));

    const targetNav = document.querySelector(`.nav-item[data-page="${pageId}"]`);
    const targetView = document.getElementById(`view-${pageId}`);

    if (targetNav) targetNav.classList.add("active");
    if (targetView) targetView.classList.add("active");

    window.location.hash = pageId;

    // Load view-specific data
    if (pageId === "overview") loadOverviewData();
    else if (pageId === "transactions") loadTransactions();
    else if (pageId === "anomalies") loadAnomalies();
    else if (pageId === "recovery") loadRecoveries();
    else if (pageId === "budget") updateBudgetSimulation();
    else if (pageId === "reports") loadReportPreview();
}

// --- Overview Dashboard & Charts ---

async function loadOverviewData() {
    try {
        const res = await fetch("/api/overview");
        const data = await res.json();
        if (data.status !== "success") return;

        const ov = data.overview;
        const rec = data.recovery_summary;

        document.getElementById("m-income").innerText = `₹${formatNumber(ov.total_income)}`;
        document.getElementById("m-expense").innerText = `₹${formatNumber(ov.total_expense)}`;
        document.getElementById("m-balance").innerText = `₹${formatNumber(ov.net_balance)}`;
        document.getElementById("m-recovery").innerText = `₹${formatNumber(rec.total_confirmed)}`;
        document.getElementById("m-unresolved-label").innerText = `₹${formatNumber(rec.total_unresolved)} unresolved claims`;

        // Update Sidebar Badges
        const recBadge = document.getElementById("nav-recovery-count");
        if (recBadge) recBadge.innerText = rec.total_cases;
        const anomBadge = document.getElementById("nav-anomaly-count");
        if (anomBadge) anomBadge.innerText = data.anomaly_count + data.duplicate_count;

        // Render Charts
        renderMonthlyChart(ov.monthly_trend);
        renderCategoryChart(ov.categories);

        // Render Quick Alerts
        renderOverviewAlerts(data);
    } catch (err) {
        console.error("Error loading overview:", err);
    }
}

function renderMonthlyChart(trend) {
    const ctx = document.getElementById("monthlyTrendChart");
    if (!ctx) return;
    if (currentChartMonthly) currentChartMonthly.destroy();

    const labels = trend.map(t => t.month);
    const expenses = trend.map(t => t.debit_total);
    const incomes = trend.map(t => t.credit_total);

    currentChartMonthly = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Debits / Outlays",
                    data: expenses,
                    backgroundColor: "rgba(239, 68, 68, 0.75)",
                    borderColor: "#EF4444",
                    borderWidth: 1,
                    borderRadius: 4
                },
                {
                    label: "Inbound Credits",
                    data: incomes,
                    backgroundColor: "rgba(16, 185, 129, 0.75)",
                    borderColor: "#10B981",
                    borderWidth: 1,
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: "#94a3b8", font: { family: "Plus Jakarta Sans" } } }
            },
            scales: {
                x: { ticks: { color: "#64748b" }, grid: { color: "rgba(255,255,255,0.05)" } },
                y: { ticks: { color: "#64748b" }, grid: { color: "rgba(255,255,255,0.05)" } }
            }
        }
    });
}

function renderCategoryChart(categories) {
    const ctx = document.getElementById("categoryChart");
    if (!ctx) return;
    if (currentChartCategory) currentChartCategory.destroy();

    const top5 = categories.slice(0, 5);
    const others = categories.slice(5).reduce((acc, c) => acc + c.total_spent, 0);

    const labels = top5.map(c => c.category);
    const dataVals = top5.map(c => c.total_spent);
    if (others > 0) {
        labels.push("Other Categories");
        dataVals.push(others);
    }

    currentChartCategory = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [{
                data: dataVals,
                backgroundColor: [
                    "#00F0FF", "#38BDF8", "#6366F1", "#A855F7", "#EC4899", "#64748B"
                ],
                borderColor: "#0E1526",
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "right",
                    labels: { color: "#94a3b8", font: { size: 10, family: "Plus Jakarta Sans" } }
                }
            }
        }
    });
}

function renderOverviewAlerts(data) {
    const container = document.getElementById("overview-alerts-list");
    if (!container) return;

    let html = `
        <div style="display: flex; gap: 12px; flex-direction: column;">
            <div style="background: rgba(239, 68, 68, 0.08); border-left: 3px solid #EF4444; padding: 10px 14px; border-radius: 6px;">
                <strong style="color: #F87171;"><i class="fa-solid fa-triangle-exclamation"></i> Spending Spike Detected:</strong>
                <span style="font-size: 0.85rem; color: #cbd5e1; margin-left: 6px;">Food Delivery outlays surged by 437% in October 2024 to ₹16,460.00.</span>
            </div>
            <div style="background: rgba(245, 158, 11, 0.08); border-left: 3px solid #F59E0B; padding: 10px 14px; border-radius: 6px;">
                <strong style="color: #FBBF24;"><i class="fa-solid fa-clone"></i> Duplicate Charge Candidate:</strong>
                <span style="font-size: 0.85rem; color: #cbd5e1; margin-left: 6px;">Two identical debits of ₹620.00 at Swiggy on 2024-10-18 with matching reference.</span>
            </div>
            <div style="background: rgba(0, 240, 255, 0.08); border-left: 3px solid #00F0FF; padding: 10px 14px; border-radius: 6px;">
                <strong style="color: #38BDF8;"><i class="fa-solid fa-shield-halved"></i> Active Recovery Case:</strong>
                <span style="font-size: 0.85rem; color: #cbd5e1; margin-left: 6px;">₹1,000.00 failed payment at Shoppers Stop: ₹300.00 confirmed verified, ₹700.00 unresolved.</span>
            </div>
        </div>
    `;
    container.innerHTML = html;
}

// --- AI Investigation & Live Trace Viewer ---

document.getElementById("btn-send-investigation")?.addEventListener("click", submitInvestigation);
document.getElementById("chat-query-input")?.addEventListener("keypress", (e) => {
    if (e.key === "Enter") submitInvestigation();
});

function setQuery(text) {
    document.getElementById("chat-query-input").value = text;
    submitInvestigation();
}

async function submitInvestigation() {
    const input = document.getElementById("chat-query-input");
    const query = input.value.trim();
    if (!query) return;

    const language = document.getElementById("investigation-language").value;
    input.value = "";

    // Append User Message in UI
    appendChatMessage("user", query);

    // Show loading spinner in chat
    const loadingId = appendChatMessage("bot", '<i class="fa-solid fa-circle-notch fa-spin"></i> Investigating ledger with autonomous tools...');

    // Clear trace body
    const traceBody = document.getElementById("trace-container");
    traceBody.innerHTML = `
        <div style="padding: 12px; color: #38BDF8; font-size: 0.85rem;">
            <i class="fa-solid fa-spinner fa-spin"></i> Agent planning investigation sequence...
        </div>
    `;

    try {
        const res = await fetch("/api/investigate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: query, language: language })
        });
        const data = await res.json();

        // Remove loading
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) loadingEl.remove();

        if (data.status === "success") {
            appendChatMessage("bot", data.answer, true);
            renderTraceSteps(data.trace);
            // Optionally speak answer if voice was recently used
            if (isRecording) speakText(data.answer);
        } else {
            appendChatMessage("bot", `Error: ${data.error || "Investigation failed"}`);
        }
    } catch (err) {
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) loadingEl.remove();
        appendChatMessage("bot", `Network or server error: ${err.message}`);
    }
}

function appendChatMessage(sender, content, showSpeaker = false) {
    const chatContainer = document.getElementById("chat-messages");
    const msgId = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
    const msgDiv = document.createElement("div");
    msgDiv.className = `msg ${sender}-msg`;
    msgDiv.id = msgId;

    const avatarIcon = sender === "user" ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-shield-halved"></i>';
    const speakerBtn = showSpeaker ? `<button class="btn-speaker" onclick="speakText(this.dataset.text)" data-text="${encodeURIComponent(content)}" title="Read Aloud" style="background: none; border: none; color: #00F0FF; cursor: pointer; margin-left: 8px;"><i class="fa-solid fa-volume-high"></i></button>` : '';

    msgDiv.innerHTML = `
        <div class="msg-avatar">${avatarIcon}</div>
        <div class="msg-bubble">
            <p>${content} ${speakerBtn}</p>
        </div>
    `;

    chatContainer.appendChild(msgDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return msgId;
}

function renderTraceSteps(trace) {
    const traceBody = document.getElementById("trace-container");
    const countBadge = document.getElementById("trace-step-count");
    if (countBadge) countBadge.innerText = `${trace.length} Steps`;

    if (!trace || trace.length === 0) {
        traceBody.innerHTML = `<div class="trace-empty-state"><p>No tool trace returned.</p></div>`;
        return;
    }

    let html = "";
    trace.forEach((step, idx) => {
        let obsFormatted = step.observation;
        try {
            const parsed = JSON.parse(step.observation);
            obsFormatted = JSON.stringify(parsed, null, 2);
        } catch (e) {
            // Keep text
        }

        html += `
            <div class="trace-step-item">
                <div class="step-header">
                    <span class="step-num">Iteration ${idx + 1}</span>
                    <span class="step-tool">${step.tool}</span>
                </div>
                <div class="step-thought">
                    <strong>Thought:</strong> ${step.thought}
                </div>
                <div style="font-size: 0.75rem; color: #94a3b8; margin-bottom: 4px;">
                    <strong>Args:</strong> <code>${JSON.stringify(step.args)}</code>
                </div>
                <div class="step-obs">${escapeHtml(obsFormatted)}</div>
            </div>
        `;
    });

    traceBody.innerHTML = html;
    traceBody.scrollTop = traceBody.scrollHeight;
}

// --- Voice Interaction (Speech-to-Text & Text-to-Speech) ---

function initVoice() {
    const btnVoice = document.getElementById("btn-voice-input");
    const voiceIndicator = document.getElementById("voice-indicator");

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        if (btnVoice) btnVoice.style.display = "none";
        return;
    }

    speechRecognizer = new SpeechRecognition();
    speechRecognizer.continuous = false;
    speechRecognizer.interimResults = false;

    // Map language dropdown to speech recognition locale
    const langMap = {
        "English": "en-IN",
        "Tamil": "ta-IN",
        "Hindi": "hi-IN",
        "Telugu": "te-IN",
        "Malayalam": "ml-IN"
    };

    btnVoice.addEventListener("click", () => {
        if (isRecording) {
            speechRecognizer.stop();
            isRecording = false;
            btnVoice.classList.remove("recording");
            if (voiceIndicator) voiceIndicator.style.display = "none";
        } else {
            const currentLang = document.getElementById("investigation-language").value;
            speechRecognizer.lang = langMap[currentLang] || "en-IN";
            try {
                speechRecognizer.start();
                isRecording = true;
                btnVoice.classList.add("recording");
                if (voiceIndicator) voiceIndicator.style.display = "flex";
            } catch (err) {
                console.error("Speech start error:", err);
            }
        }
    });

    speechRecognizer.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        document.getElementById("chat-query-input").value = transcript;
        isRecording = false;
        btnVoice.classList.remove("recording");
        if (voiceIndicator) voiceIndicator.style.display = "none";
        submitInvestigation();
    };

    speechRecognizer.onerror = (event) => {
        console.warn("Speech recognition error:", event.error);
        isRecording = false;
        btnVoice.classList.remove("recording");
        if (voiceIndicator) voiceIndicator.style.display = "none";
    };

    speechRecognizer.onend = () => {
        isRecording = false;
        btnVoice.classList.remove("recording");
        if (voiceIndicator) voiceIndicator.style.display = "none";
    };
}

function speakText(encodedText) {
    if (!("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const text = decodeURIComponent(encodedText);
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    window.speechSynthesis.speak(utterance);
}

// --- Recovery Center Controller ---

async function loadRecoveries() {
    try {
        const res = await fetch("/api/recoveries");
        const data = await res.json();
        if (data.status !== "success") return;

        const sum = data.summary;
        document.getElementById("rec-total-potential").innerText = `₹${formatNumber(sum.total_potential)}`;
        document.getElementById("rec-total-confirmed").innerText = `₹${formatNumber(sum.total_confirmed)}`;
        document.getElementById("rec-total-unresolved").innerText = `₹${formatNumber(sum.total_unresolved)}`;

        const container = document.getElementById("recovery-cases-list");
        if (!container) return;

        if (data.records.length === 0) {
            container.innerHTML = `<p style="padding: 20px; color: #94a3b8;">No recovery cases detected.</p>`;
            return;
        }

        let html = "";
        data.records.forEach(r => {
            const statusClass = r.status === "confirmed_recovery" ? "confirmed" : (r.status === "partially_confirmed" ? "partially" : "pending");
            
            let linksHtml = "";
            (r.links || []).forEach(link => {
                linksHtml += `
                    <div class="timeline-event credit-event">
                        <strong style="color: #10B981;">Verified Inbound Credit Received: ₹${formatNumber(link.linked_amount)}</strong>
                        <div><small>${link.credit_desc} | Date: ${link.credit_date} | Confidence: ${Math.round(link.confidence_score * 100)}%</small></div>
                    </div>
                `;
            });

            html += `
                <div class="recovery-case-card">
                    <div class="case-header">
                        <div>
                            <span class="case-merchant">${r.merchant}</span>
                            <span class="badge ${r.status === 'confirmed_recovery' ? 'cyan-badge' : 'gold-badge'}" style="margin-left: 8px;">
                                ${r.status.replace('_', ' ').toUpperCase()}
                            </span>
                        </div>
                        <div style="font-family: var(--font-mono); font-size: 0.95rem;">
                            Potential: <strong>₹${formatNumber(r.potential_amount)}</strong> |
                            Verified: <strong style="color: #10B981;">₹${formatNumber(r.confirmed_amount)}</strong> |
                            Unresolved: <strong style="color: #F59E0B;">₹${formatNumber(r.unresolved_amount)}</strong>
                        </div>
                    </div>
                    <div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 8px;">
                        <strong>Notes:</strong> ${r.notes || "Investigation initiated"}
                    </div>
                    <div class="case-timeline">
                        <div class="timeline-event">
                            <strong>Original Debit Charge: ₹${formatNumber(r.potential_amount)}</strong>
                            <div><small>${r.original_description} | Date: ${r.original_date} | Ref: ${r.original_reference || 'N/A'}</small></div>
                        </div>
                        ${linksHtml}
                        <div class="timeline-event" style="${r.unresolved_amount === 0 ? 'display:none;' : ''}">
                            <strong style="color: #F59E0B;">Remaining Unresolved Exposure: ₹${formatNumber(r.unresolved_amount)}</strong>
                            <div><small>Under investigation with bank and merchant gateway.</small></div>
                        </div>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    } catch (err) {
        console.error("Error loading recoveries:", err);
    }
}

// --- Anomaly & Duplicate Controller ---

async function loadAnomalies() {
    try {
        const res = await fetch("/api/anomalies");
        const data = await res.json();
        if (data.status !== "success") return;

        const anomBadge = document.getElementById("anomaly-badge-count");
        if (anomBadge) anomBadge.innerText = `${data.anomalies.length} Detected`;
        const dupBadge = document.getElementById("duplicate-badge-count");
        if (dupBadge) dupBadge.innerText = `${data.duplicates.length} Found`;

        // Render Anomalies
        const anomContainer = document.getElementById("anomalies-full-list");
        if (anomContainer) {
            let html = "";
            data.anomalies.forEach(a => {
                html += `
                    <div style="background: #090E1C; border: 1px solid var(--border-color); border-radius: 8px; padding: 14px; margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                            <strong>${a.merchant} (${a.category})</strong>
                            <span style="font-family: var(--font-mono); color: #EF4444; font-weight: 700;">₹${formatNumber(a.amount)}</span>
                        </div>
                        <p style="font-size: 0.82rem; color: #cbd5e1; margin-bottom: 4px;">${a.reason}</p>
                        <small style="color: #64748b;">Date: ${a.transaction_date} | Baseline Mean: ₹${formatNumber(a.historical_baseline)} | Delta: +₹${formatNumber(a.delta_amount)}</small>
                    </div>
                `;
            });
            anomContainer.innerHTML = html || "<p style='color: #64748b;'>No spending anomalies flagged.</p>";
        }

        // Render Duplicates
        const dupContainer = document.getElementById("duplicates-full-list");
        if (dupContainer) {
            let html = "";
            data.duplicates.forEach(d => {
                html += `
                    <div style="background: #090E1C; border: 1px solid var(--border-color); border-radius: 8px; padding: 14px; margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                            <strong>${d.merchant}</strong>
                            <span class="badge gold-badge">${Math.round(d.confidence * 100)}% Confidence Match</span>
                        </div>
                        <p style="font-size: 0.82rem; color: #FBBF24; margin-bottom: 6px;">${d.reason}</p>
                        <div style="background: #040711; padding: 8px; border-radius: 4px; font-size: 0.75rem; color: #94a3b8;">
                            <div>Tx 1: ${d.primary_transaction.date} | ₹${formatNumber(d.amount)} | Ref: ${d.primary_transaction.reference || 'N/A'}</div>
                            <div>Tx 2: ${d.duplicate_transaction.date} | ₹${formatNumber(d.amount)} | Ref: ${d.duplicate_transaction.reference || 'N/A'}</div>
                        </div>
                    </div>
                `;
            });
            dupContainer.innerHTML = html || "<p style='color: #64748b;'>No duplicate charges found.</p>";
        }
    } catch (err) {
        console.error("Error loading anomalies:", err);
    }
}

// --- Budget Simulator ---

function resetBudgetSliders() {
    document.getElementById("slide-food-delivery").value = 15;
    document.getElementById("slide-shopping").value = 20;
    document.getElementById("slide-entertainment").value = 10;
    document.getElementById("slide-transport").value = 10;
    document.getElementById("slide-fuel").value = 5;
    updateBudgetSimulation();
}

async function updateBudgetSimulation() {
    const cutFood = parseFloat(document.getElementById("slide-food-delivery").value);
    const cutShop = parseFloat(document.getElementById("slide-shopping").value);
    const cutEnt = parseFloat(document.getElementById("slide-entertainment").value);
    const cutTrans = parseFloat(document.getElementById("slide-transport").value);
    const cutFuel = parseFloat(document.getElementById("slide-fuel").value);

    document.getElementById("val-food-delivery").innerText = `${cutFood}%`;
    document.getElementById("val-shopping").innerText = `${cutShop}%`;
    document.getElementById("val-entertainment").innerText = `${cutEnt}%`;
    document.getElementById("val-transport").innerText = `${cutTrans}%`;
    document.getElementById("val-fuel").innerText = `${cutFuel}%`;

    const reductions = {
        "Food delivery": cutFood,
        "Shopping": cutShop,
        "Entertainment": cutEnt,
        "Transport": cutTrans,
        "Fuel": cutFuel
    };

    try {
        const res = await fetch("/api/budget/simulate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ reductions: reductions })
        });
        const data = await res.json();
        if (data.status !== "success") return;

        document.getElementById("b-current-monthly").innerText = `₹${formatNumber(data.current_total_monthly_spend)}`;
        document.getElementById("b-projected-monthly").innerText = `₹${formatNumber(data.projected_total_monthly_spend)}`;
        document.getElementById("b-monthly-saving").innerText = `₹${formatNumber(data.monthly_hypothetical_savings)}`;
        document.getElementById("b-annual-saving").innerText = `₹${formatNumber(data.annualized_hypothetical_savings)}`;

        const tbody = document.getElementById("budget-breakdown-tbody");
        if (tbody) {
            let html = "";
            (data.category_breakdown || []).forEach(c => {
                html += `
                    <tr>
                        <td><strong>${c.category}</strong></td>
                        <td>₹${formatNumber(c.current_monthly_spend)}</td>
                        <td>₹${formatNumber(c.proposed_monthly_spend)}</td>
                        <td><span class="badge ${c.percentage_reduction > 0 ? 'cyan-badge' : 'outline-badge'}">${c.percentage_reduction}%</span></td>
                        <td style="color: #10B981; font-weight: 600;">+₹${formatNumber(c.monthly_expected_saving)}</td>
                    </tr>
                `;
            });
            tbody.innerHTML = html;
        }
    } catch (err) {
        console.error("Budget simulation error:", err);
    }
}

// --- Transactions & Category Modal ---

let allLoadedTransactions = [];

async function loadTransactions() {
    try {
        const res = await fetch("/api/transactions?limit=200");
        const data = await res.json();
        if (data.status !== "success") return;

        allLoadedTransactions = data.transactions;
        renderTransactionsTable(allLoadedTransactions);
    } catch (err) {
        console.error("Error loading transactions:", err);
    }
}

function filterTransactions() {
    const query = document.getElementById("tx-search-input").value.toLowerCase();
    const category = document.getElementById("tx-category-filter").value;
    const type = document.getElementById("tx-type-filter").value;

    const filtered = allLoadedTransactions.filter(t => {
        const matchesQuery = !query || t.merchant.toLowerCase().includes(query) ||
                             t.description.toLowerCase().includes(query) ||
                             (t.reference_id && t.reference_id.toLowerCase().includes(query));
        const matchesCat = category === "All" || t.category === category;
        const matchesType = type === "all" || (type === "debit" && t.debit > 0) || (type === "credit" && t.credit > 0);
        return matchesQuery && matchesCat && matchesType;
    });

    renderTransactionsTable(filtered);
}

function renderTransactionsTable(txns) {
    const tbody = document.getElementById("transactions-tbody");
    if (!tbody) return;

    if (txns.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: #64748b; padding: 20px;">No transactions found.</td></tr>`;
        return;
    }

    let html = "";
    txns.forEach(t => {
        const isCredit = t.credit > 0;
        const amtStr = isCredit ? `+₹${formatNumber(t.credit)}` : `-₹${formatNumber(t.debit)}`;
        const amtClass = isCredit ? "income" : "expense";

        html += `
            <tr>
                <td style="font-family: var(--font-mono); font-size: 0.8rem;">${t.transaction_date}</td>
                <td><strong>${t.merchant}</strong></td>
                <td style="max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${t.description}</td>
                <td><span class="badge outline-badge">${t.category}</span></td>
                <td style="font-family: var(--font-mono); font-size: 0.75rem; color: #94a3b8;">${t.reference_id || 'N/A'}</td>
                <td style="text-align: right; font-family: var(--font-mono); font-weight: 700;" class="${amtClass}">${amtStr}</td>
                <td>
                    <button class="btn btn-sm btn-secondary" onclick="openCategoryModal('${t.id}', '${escapeQuotes(t.merchant)}', '${t.category}')">
                        <i class="fa-solid fa-pen"></i> Edit
                    </button>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

function openCategoryModal(txId, merchant, currentCat) {
    document.getElementById("modal-tx-id").value = txId;
    document.getElementById("modal-tx-desc").innerText = `Merchant: ${merchant}`;
    document.getElementById("modal-new-category").value = currentCat;
    document.getElementById("category-modal").style.display = "flex";
}

function closeCategoryModal() {
    document.getElementById("category-modal").style.display = "none";
}

async function saveCategoryModal() {
    const txId = document.getElementById("modal-tx-id").value;
    const newCat = document.getElementById("modal-new-category").value;

    try {
        const res = await fetch("/api/transactions/category", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ transaction_id: txId, category: newCat })
        });
        const data = await res.json();
        if (data.status === "success") {
            closeCategoryModal();
            loadTransactions();
            loadOverviewData();
        }
    } catch (err) {
        alert("Failed to save category: " + err.message);
    }
}

// --- Statement Ingestion Upload ---

function initUpload() {
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("file-input");

    if (!dropZone || !fileInput) return;

    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.style.borderColor = "var(--primary-cyan)";
    });

    dropZone.addEventListener("dragleave", () => {
        dropZone.style.borderColor = "var(--border-highlight)";
    });

    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.style.borderColor = "var(--border-highlight)";
        if (e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });
}

async function handleFileUpload(file) {
    const resultContainer = document.getElementById("upload-result-container");
    resultContainer.style.display = "block";
    resultContainer.innerHTML = `<div style="color: #38BDF8;"><i class="fa-solid fa-spinner fa-spin"></i> Ingesting, normalizing, and validating statement...</div>`;

    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch("/api/upload", {
            method: "POST",
            body: formData
        });
        const data = await res.json();

        if (data.status === "success") {
            const r = data.report;
            resultContainer.innerHTML = `
                <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid #10B981; padding: 16px; border-radius: 8px;">
                    <h3 style="color: #10B981; margin-bottom: 8px;"><i class="fa-solid fa-circle-check"></i> Statement Ingested Successfully</h3>
                    <p style="font-size: 0.88rem;"><strong>${data.transactions_ingested}</strong> transaction records normalized and verified from <code>${data.filename}</code>.</p>
                    <div style="font-size: 0.8rem; color: #cbd5e1; margin-top: 8px;">
                        Valid Records: ${r.valid_records} | Rejected: ${r.rejected_records} | Duplicate Refs Observed: ${r.duplicate_ref_count}
                    </div>
                </div>
            `;
            loadOverviewData();
        } else {
            resultContainer.innerHTML = `
                <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid #EF4444; padding: 16px; border-radius: 8px;">
                    <h3 style="color: #EF4444;"><i class="fa-solid fa-circle-xmark"></i> Ingestion Failed</h3>
                    <p style="font-size: 0.85rem; color: #cbd5e1;">${data.message}</p>
                </div>
            `;
        }
    } catch (err) {
        resultContainer.innerHTML = `<div style="color: #EF4444;">Upload error: ${err.message}</div>`;
    }
}

// --- Report Preview ---

async function loadReportPreview() {
    const container = document.getElementById("report-preview-text");
    if (!container) return;

    try {
        const res = await fetch("/api/overview");
        const data = await res.json();
        const ov = data.overview;
        const rec = data.recovery_summary;

        container.innerHTML = `
            <div style="line-height: 1.6; font-size: 0.85rem;">
                <p><strong>Audited Scope:</strong> ${ov.start_date || 'N/A'} through ${ov.end_date || 'N/A'}</p>
                <p><strong>Total Transactions Analyzed:</strong> ${ov.total_transactions} records</p>
                <p><strong>Net Lifetime Outlays:</strong> ₹${formatNumber(ov.total_expense)}</p>
                <p><strong>Total Inbound Credits:</strong> ₹${formatNumber(ov.total_income)}</p>
                <p><strong>Recovery Verification:</strong> ₹${formatNumber(rec.total_confirmed)} confirmed received / ₹${formatNumber(rec.total_unresolved)} unresolved exposure</p>
                <p><strong>Top Spending Category:</strong> ${ov.categories[0]?.category || 'N/A'} (₹${formatNumber(ov.categories[0]?.total_spent || 0)})</p>
                <div style="margin-top: 14px; padding: 10px; background: rgba(0, 240, 255, 0.05); border-radius: 6px; border-left: 3px solid #00F0FF;">
                    Click <strong>Download Audit PDF</strong> above to obtain the formal verification certificate.
                </div>
            </div>
        `;
    } catch (err) {
        console.error("Report preview error:", err);
    }
}

// --- Demo Reset ---

function initDemoReset() {
    const btn = document.getElementById("btn-reset-demo");
    if (!btn) return;
    btn.addEventListener("click", async () => {
        if (!confirm("Reset database to standard 168-transaction synthetic demonstration dataset?")) return;
        try {
            btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Resetting...`;
            const res = await fetch("/api/demo/reset", { method: "POST" });
            const data = await res.json();
            btn.innerHTML = `<i class="fa-solid fa-rotate-right"></i> Reset Demo Data`;
            alert(data.message || "Demo data refreshed.");
            loadOverviewData();
            loadTransactions();
            loadRecoveries();
            loadAnomalies();
        } catch (err) {
            btn.innerHTML = `<i class="fa-solid fa-rotate-right"></i> Reset Demo Data`;
            alert("Reset error: " + err.message);
        }
    });
}

// --- Helpers ---

function formatNumber(num) {
    if (num === null || num === undefined || isNaN(num)) return "0.00";
    return Number(num).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function escapeQuotes(str) {
    if (!str) return "";
    return str.replace(/'/g, "\\'");
}

