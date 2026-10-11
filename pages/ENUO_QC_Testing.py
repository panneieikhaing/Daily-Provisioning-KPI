
import json
from io import StringIO

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="QC Testing - ENUO",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# GOOGLE SHEETS
# ============================================================

SHEET_ID = "14WOHloWhGuQOc95PrRUsYWAHT6PTCC6EL2pY18uglVs"
SHEET_TAB = ""

HC_API_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbxtIHI5c0dgeT_ZzcqaD5CAncYtrhyxLi3Bl3LLmMyzY-GEGaRG6zjmpp4K8ui0LElOeg/exec"
)


# ============================================================
# LOAD SOURCE DATA
# ============================================================

@st.cache_data(ttl=30)
def load_google_sheet():

    if SHEET_TAB:
        url = (
            f"https://docs.google.com/spreadsheets/d/"
            f"{SHEET_ID}/gviz/tq?"
            f"tqx=out:csv&sheet={SHEET_TAB}"
        )
    else:
        url = (
            f"https://docs.google.com/spreadsheets/d/"
            f"{SHEET_ID}/gviz/tq?tqx=out:csv"
        )

    response = requests.get(
        url,
        headers={
            "Cache-Control": "no-cache, no-store",
            "Pragma": "no-cache",
        },
        timeout=30,
    )

    response.raise_for_status()

    return pd.read_csv(StringIO(response.text))


# ============================================================
# LOAD HC SETTINGS
# ============================================================

def load_hc_from_google_sheet():

    response = requests.get(
        HC_API_URL,
        params={"_ts": pd.Timestamp.now().timestamp()},
        headers={
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
        timeout=20,
    )

    response.raise_for_status()

    result = response.json()

    if isinstance(result, dict) and result.get("success"):
        rows = result.get("data", [])
        return rows if isinstance(rows, list) else []

    raise ValueError(
        "HC_Settings API did not return success=true."
    )


# ============================================================
# PREPARE SOURCE DATA
# ============================================================

try:

    df = load_google_sheet().copy()

    df.columns = (
        df.columns.astype(str).str.strip()
    )

    required_columns = [
        "Date",
        "Device Name",
        "Daily (JD)",
        "Qty",
        "MAC",
        "Issue Type",
        "Region",
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        st.error(
            "Missing columns: " + ", ".join(missing)
        )
        st.stop()

    df["Region"] = (
        df["Region"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df = df[df["Region"] == "ENUO"].copy()

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce",
    )

    df = df.dropna(subset=["Date"]).copy()

    # Use ISO dates for calculation and cloud keys.
    df["DateSort"] = df["Date"].dt.strftime("%Y-%m-%d")

    # Keep a readable display date.
    df["DateDisplay"] = df["Date"].dt.strftime("%Y-%m-%d")

    for column in [
        "Device Name",
        "Daily (JD)",
        "Issue Type",
        "MAC",
    ]:
        df[column] = (
            df[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    df["Daily (JD)"] = df["Daily (JD)"].str.lower()
    df["Device Name"] = df["Device Name"].str.lower()
    df["Issue Type"] = df["Issue Type"].str.lower()

    df["Qty"] = pd.to_numeric(
        df["Qty"],
        errors="coerce",
    ).fillna(0)

    df = df.sort_values(
        ["Date", "Daily (JD)"],
        ascending=[True, True],
    )

    records = []

    for _, row in df.iterrows():

        records.append({
            "date": row["DateDisplay"],
            "date_sort": row["DateSort"],
            "device": str(row["Device Name"]),
            "daily": str(row["Daily (JD)"]),
            "qty": float(row["Qty"]),
            "mac": str(row["MAC"]),
            "issue_type": str(row["Issue Type"]),
        })

    data_json = json.dumps(
        records,
        ensure_ascii=False,
    )

    # Load HC settings independently from the source data.
    hc_records = load_hc_from_google_sheet()

    hc_json = json.dumps(
        hc_records,
        ensure_ascii=False,
    )

except Exception as exc:

    st.error(f"Unable to load data: {exc}")
    st.stop()


# ============================================================
# HTML DASHBOARD
# ============================================================

html = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>QC Testing - ENUO</title>

<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    padding: 24px;
    background: #f5f7fb;
    font-family: Arial, Helvetica, sans-serif;
    color: #1f2937;
}

.header { margin-bottom: 20px; }

.header h1 {
    margin: 0;
    font-size: 28px;
    font-weight: 700;
    color: #111827;
}

.header p {
    margin: 6px 0 0;
    color: #6b7280;
    font-size: 14px;
}

.filter-area {
    position: relative;
    margin-bottom: 18px;
}

.date-button {
    width: 260px;
    height: 42px;
    padding: 0 14px;
    background: white;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    cursor: pointer;
    font-size: 14px;
    color: #374151;
}

.dropdown {
    display: none;
    position: absolute;
    top: 48px;
    left: 0;
    width: 320px;
    background: white;
    border: 1px solid #d1d5db;
    border-radius: 10px;
    box-shadow: 0 10px 25px rgba(0,0,0,.10);
    z-index: 999;
}

.dropdown.open { display: block; }

.search-box {
    padding: 10px;
    border-bottom: 1px solid #e5e7eb;
}

.search-box input {
    width: 100%;
    height: 36px;
    padding: 0 10px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
}

.select-actions {
    display: flex;
    gap: 8px;
    padding: 9px 10px;
    border-bottom: 1px solid #e5e7eb;
}

.select-actions button {
    border: none;
    background: #f3f4f6;
    padding: 7px 10px;
    border-radius: 5px;
    cursor: pointer;
}

.date-list {
    max-height: 260px;
    overflow-y: auto;
    padding: 5px 0;
}

.date-option {
    display: flex;
    align-items: center;
    gap: 9px;
    padding: 8px 12px;
    cursor: pointer;
    font-size: 13px;
}

.date-option:hover { background: #f9fafb; }

.dropdown-footer {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    padding: 10px;
    border-top: 1px solid #e5e7eb;
}

.dropdown-footer button {
    height: 34px;
    padding: 0 14px;
    border-radius: 6px;
    cursor: pointer;
}

.cancel-btn {
    background: white;
    border: 1px solid #d1d5db;
}

.apply-btn {
    background: #111827;
    border: 1px solid #111827;
    color: white;
}

.table-container {
    width: 100%;
    overflow-x: auto;
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    box-shadow: 0 2px 8px rgba(0,0,0,.04);
}

table {
    width: 100%;
    border-collapse: collapse;
    min-width: 900px;
}

thead th {
    background: #111827;
    color: white;
    font-size: 13px;
    padding: 13px 12px;
    text-align: center;
    white-space: nowrap;
}

tbody td {
    padding: 11px 12px;
    border-bottom: 1px solid #e5e7eb;
    text-align: center;
    font-size: 13px;
    white-space: nowrap;
}

tbody tr:hover { background: #f9fafb; }

.date-cell {
    font-weight: 600;
    text-align: left !important;
    padding-left: 18px !important;
}

.number { font-variant-numeric: tabular-nums; }

.hc-input, .rma-input {
    width: 80px;
    height: 34px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    text-align: center;
    font-size: 13px;
}

.kpi {
    font-weight: 700;
    font-size: 14px;
}

.total-row td {
    background: #f3f4f6;
    font-weight: 700;
    border-top: 2px solid #d1d5db;
}

.empty {
    padding: 35px;
    text-align: center;
    color: #6b7280;
}

.save-status {
    margin: 10px 0;
    font-size: 12px;
    color: #6b7280;
}

@media (max-width: 700px) {
    body { padding: 12px; }
    .header h1 { font-size: 23px; }
    .date-button { width: 100%; }
    .dropdown { width: min(320px, 95vw); }
}
</style>
</head>

<body>

<div class="header">
    <h1>QC Testing</h1>
    <p>ENUO</p>
</div>

<div class="filter-area">
    <button class="date-button"
            onclick="toggleDropdown()"
            id="dateButton">
        <span id="dateButtonText">All Dates</span>
        <span>▼</span>
    </button>

    <div class="dropdown" id="dateDropdown">
        <div class="search-box">
            <input id="dateSearch"
                   placeholder="Search date..."
                   oninput="filterDates()">
        </div>

        <div class="select-actions">
            <button onclick="selectAllDates()">Select All</button>
            <button onclick="clearDates()">Clear</button>
        </div>

        <div class="date-list" id="dateList"></div>

        <div class="dropdown-footer">
            <button class="cancel-btn" onclick="cancelDates()">Cancel</button>
            <button class="apply-btn" onclick="applyDates()">Apply</button>
        </div>
    </div>
</div>

<div class="save-status" id="saveStatus">
    HC settings loaded from Google Sheets.
</div>

<div class="table-container">
<table>
<thead>
<tr>
    <th>DATE</th>
    <th>QC INBOUND</th>
    <th>TOTAL TEST</th>
    <th>QC PASS</th>
    <th>QC FAIL</th>
    <th>RMA</th>
    <th>HC</th>
    <th>KPI</th>
</tr>
</thead>
<tbody id="tableBody"></tbody>
</table>
</div>

<script>
const DATA = __DATA_JSON__;
const HC_FROM_SHEET = __HC_DATA_JSON__;
const HC_API_URL = __HC_API_URL_JSON__;

const STORAGE_DATES = "ENUO_QC_TESTING_SELECTED_DATES";
const HC_LOCAL_KEY = "ENUO_QC_TESTING_HC";
const RMA_LOCAL_KEY = "ENUO_QC_TESTING_RMA";

let selectedDates = [];
let tempSelectedDates = [];
let hcValues = {};
let rmaValues = {};
const HC_CLOUD_DATES = new Set();

try {
    hcValues = JSON.parse(localStorage.getItem(HC_LOCAL_KEY) || "{}");
} catch (e) {
    hcValues = {};
}

try {
    rmaValues = JSON.parse(localStorage.getItem(RMA_LOCAL_KEY) || "{}");
} catch (e) {
    rmaValues = {};
}


// =========================================================
// NORMALIZE DATE KEYS FROM GOOGLE SHEETS
// =========================================================

function normalizeDate(value) {
    if (!value) return "";

    const s = String(value).trim();

    if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;

    const parsed = new Date(s);
    if (Number.isNaN(parsed.getTime())) return s;

    return [
        parsed.getFullYear(),
        String(parsed.getMonth() + 1).padStart(2, "0"),
        String(parsed.getDate()).padStart(2, "0")
    ].join("-");
}

function normalizeHCDate(value) {
    const s = String(value || "").trim();

    // Supports ISO date and the display format from older settings.
    if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;

    const months = {
        jan: "01", feb: "02", mar: "03", apr: "04",
        may: "05", jun: "06", jul: "07", aug: "08",
        sep: "09", oct: "10", nov: "11", dec: "12"
    };

    const match = s.match(/^(\d{1,2})[-\s]([A-Za-z]{3})[-\s](\d{4})$/);

    if (match && months[match[2].toLowerCase()]) {
        return match[3] + "-" + months[match[2].toLowerCase()]
            + "-" + match[1].padStart(2, "0");
    }

    return normalizeDate(s);
}


// =========================================================
// APPLY CLOUD HC SETTINGS
// =========================================================

HC_FROM_SHEET.forEach(item => {
    if (!item || !item.date) return;

    if (String(item.region || "").trim().toUpperCase() !== "ENUO") {
        return;
    }

    if (String(item.category || "").trim().toLowerCase() !== "qc") {
        return;
    }

    const key = normalizeHCDate(item.date);
    if (!key) return;

    const hc = Number(item.hc);
    if (!Number.isFinite(hc)) return;

    hcValues[key] = hc;
    HC_CLOUD_DATES.add(key);
});


// =========================================================
// DATE LIST
// =========================================================

const dateMap = new Map();

DATA.forEach(row => {
    const key = row.date_sort || normalizeHCDate(row.date);
    if (key) dateMap.set(key, row.date || key);
});

const uniqueDates = [...dateMap.keys()].sort();

try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_DATES) || "[]");

    if (Array.isArray(saved) && saved.length) {
        selectedDates = saved.filter(d => uniqueDates.includes(d));
    }
} catch (e) {
    selectedDates = [];
}

tempSelectedDates = [...selectedDates];

uniqueDates.forEach(date => {
    if (hcValues[date] === undefined || hcValues[date] === null || hcValues[date] === "") {
        hcValues[date] = 1;
    }

    if (rmaValues[date] === undefined) {
        rmaValues[date] = 0;
    }
});


// =========================================================
// DATE FILTER
// =========================================================

function toggleDropdown() {
    const dropdown = document.getElementById("dateDropdown");

    if (dropdown.classList.contains("open")) {
        dropdown.classList.remove("open");
    } else {
        tempSelectedDates = [...selectedDates];
        renderDateList();
        dropdown.classList.add("open");
    }
}

function renderDateList() {
    const list = document.getElementById("dateList");
    const search = document.getElementById("dateSearch").value.trim().toLowerCase();

    list.innerHTML = "";

    uniqueDates.forEach(date => {
        const display = dateMap.get(date) || date;

        if (
            search &&
            !date.toLowerCase().includes(search) &&
            !display.toLowerCase().includes(search)
        ) return;

        const label = document.createElement("label");
        label.className = "date-option";

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.value = date;
        checkbox.checked = tempSelectedDates.includes(date);

        checkbox.addEventListener("change", function() {
            if (this.checked) {
                if (!tempSelectedDates.includes(date)) tempSelectedDates.push(date);
            } else {
                tempSelectedDates = tempSelectedDates.filter(d => d !== date);
            }
        });

        const text = document.createElement("span");
        text.textContent = display;

        label.append(checkbox, text);
        list.appendChild(label);
    });
}

function filterDates() {
    renderDateList();
}

function selectAllDates() {
    tempSelectedDates = [...uniqueDates];
    renderDateList();
}

function clearDates() {
    tempSelectedDates = [];
    renderDateList();
}

function cancelDates() {
    tempSelectedDates = [...selectedDates];
    document.getElementById("dateDropdown").classList.remove("open");
}

function applyDates() {
    selectedDates = [...tempSelectedDates].sort();

    if (
        selectedDates.length === 0 ||
        selectedDates.length === uniqueDates.length
    ) {
        selectedDates = [];
    }

    localStorage.setItem(STORAGE_DATES, JSON.stringify(selectedDates));

    document.getElementById("dateDropdown").classList.remove("open");

    updateDateButton();
    updateTable();
}

function updateDateButton() {
    const text = document.getElementById("dateButtonText");

    if (selectedDates.length === 0 || selectedDates.length === uniqueDates.length) {
        text.textContent = "All Dates";
    } else if (selectedDates.length === 1) {
        text.textContent = dateMap.get(selectedDates[0]) || selectedDates[0];
    } else {
        text.textContent = selectedDates.length + " Dates Selected";
    }
}


// =========================================================
// NUMBER FORMATTING
// =========================================================

function number(value) {
    const n = Number(value);
    return Number.isFinite(n) ? n : 0;
}

function formatNumber(value) {
    return Math.round(number(value)).toLocaleString("en-US");
}

function formatKPI(value) {
    return String(Math.round(number(value)));
}


// =========================================================
// QC INBOUND
//
// Use the previous available source date, not calendar yesterday.
// RUN -> MAC count
// NEW -> Qty sum
// CLEANING + FFO -> Qty sum
// =========================================================

function calculateQCInbound(targetDate) {
    const currentIndex = uniqueDates.indexOf(targetDate);

    if (currentIndex <= 0) return 0;

    const sourceDate = uniqueDates[currentIndex - 1];
    let total = 0;

    DATA.forEach(row => {
        const rowDate = row.date_sort || normalizeHCDate(row.date);
        if (rowDate !== sourceDate) return;

        const daily = String(row.daily || "").trim().toLowerCase();
        const device = String(row.device || "").trim().toLowerCase();
        const mac = String(row.mac || "").trim();
        const qty = number(row.qty);

        if (daily === "run" && mac !== "" && mac.toLowerCase() !== "nan") {
            total += 1;
        }

        if (daily === "new") {
            total += qty;
        }

        if (daily === "cleaning" && device === "ffo") {
            total += qty;
        }
    });

    return total;
}


// =========================================================
// DAILY CALCULATION
//
// TOTAL TEST = SPEED TEST + LAN PORT TEST + DBM (Qty sum)
// PASS = Issue Type USE
// FAIL = Issue Type RMA
// RMA input remains manually editable, as in the earlier code.
// =========================================================

function calculate(date) {
    let totalTest = 0;
    let qcPass = 0;
    let qcFail = 0;

    DATA.forEach(row => {
        const rowDate = row.date_sort || normalizeHCDate(row.date);
        if (rowDate !== date) return;

        const daily = String(row.daily || "").trim().toLowerCase();
        const issueType = String(row.issue_type || "").trim().toLowerCase();
        const qty = number(row.qty);

        if (
            daily === "speed test" ||
            daily === "lan port test" ||
            daily === "dbm"
        ) {
            totalTest += qty;

            if (issueType === "use") {
                qcPass += qty;
            }

            if (issueType === "rma") {
                qcFail += qty;
            }
        }
    });

    return {
        qcInbound: calculateQCInbound(date),
        totalTest,
        qcPass,
        qcFail,
        rma: number(rmaValues[date])
    };
}


// =========================================================
// SAVE HC TO LOCAL STORAGE AND GOOGLE SHEETS
// =========================================================

function setStatus(message) {
    document.getElementById("saveStatus").textContent = message;
}

function saveHC(date, value) {
    let hc = Number(value);

    if (!Number.isFinite(hc) || hc < 0) hc = 0;

    hcValues[date] = hc;

    try {
        localStorage.setItem(HC_LOCAL_KEY, JSON.stringify(hcValues));
    } catch (e) {}

    updateTable();
    postHCToGoogleSheet(date, hc);
}

async function postHCToGoogleSheet(date, hc) {
    setStatus("Saving HC for " + date + " to Google Sheets...");

    try {
        // no-cors does not expose the server response to the browser.
        // This sends the request but cannot verify the sheet was updated.
        await fetch(HC_API_URL, {
            method: "POST",
            mode: "no-cors",
            headers: {
                "Content-Type": "text/plain;charset=utf-8"
            },
            body: JSON.stringify({
                date: date,
                region: "ENUO",
                category: "qc",
                hc: Number(hc)
            })
        });

        setStatus(
            "HC save request sent for " + date +
            ". Reopen or refresh to verify the saved value."
        );
    } catch (error) {
        setStatus(
            "HC save request failed. The value remains in this browser only."
        );
        console.error(error);
    }
}


// =========================================================
// SAVE MANUAL RMA
// =========================================================

function saveRMA(date, value) {
    let rma = Number(value);

    if (!Number.isFinite(rma) || rma < 0) rma = 0;

    rmaValues[date] = rma;

    try {
        localStorage.setItem(RMA_LOCAL_KEY, JSON.stringify(rmaValues));
    } catch (e) {}

    updateTable();
}


// =========================================================
// INITIALIZE MISSING HC
//
// Do not overwrite existing cloud HC.
// Missing defaults are 1 and are submitted to the API.
// The no-cors request cannot confirm server-side success.
// =========================================================

async function autoSaveMissingHC() {
    for (const date of uniqueDates) {
        if (HC_CLOUD_DATES.has(date)) continue;

        const hc = number(hcValues[date] ?? 1);

        try {
            await fetch(HC_API_URL, {
                method: "POST",
                mode: "no-cors",
                headers: {
                    "Content-Type": "text/plain;charset=utf-8"
                },
                body: JSON.stringify({
                    date: date,
                    region: "ENUO",
                    category: "qc",
                    hc: hc
                })
            });

            // Do not mark as confirmed: no-cors cannot verify a successful write.
        } catch (error) {
            console.error("Default HC request failed:", date, error);
        }
    }
}


// =========================================================
// RENDER TABLE
// =========================================================

function updateTable() {
    const tbody = document.getElementById("tableBody");
    tbody.innerHTML = "";

    const datesToShow = (
        selectedDates.length === 0 ||
        selectedDates.length === uniqueDates.length
    ) ? [...uniqueDates] : [...selectedDates];

    datesToShow.sort();

    if (!datesToShow.length) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="empty">No date selected</td>
            </tr>
        `;
        return;
    }

    let grandInbound = 0;
    let grandTest = 0;
    let grandPass = 0;
    let grandFail = 0;
    let grandRMA = 0;
    let grandHC = 0;

    datesToShow.forEach(date => {
        const result = calculate(date);
        const hc = number(hcValues[date]);
        const kpi = hc > 0 ? result.totalTest / hc : 0;

        grandInbound += result.qcInbound;
        grandTest += result.totalTest;
        grandPass += result.qcPass;
        grandFail += result.qcFail;
        grandRMA += result.rma;
        grandHC += hc;

        const tr = document.createElement("tr");

        const dateCell = document.createElement("td");
        dateCell.className = "date-cell";
        dateCell.textContent = dateMap.get(date) || date;
        tr.appendChild(dateCell);

        [
            result.qcInbound,
            result.totalTest,
            result.qcPass,
            result.qcFail
        ].forEach(value => {
            const td = document.createElement("td");
            td.className = "number";
            td.textContent = formatNumber(value);
            tr.appendChild(td);
        });

        const rmaCell = document.createElement("td");
        const rmaInput = document.createElement("input");
        rmaInput.className = "rma-input";
        rmaInput.type = "number";
        rmaInput.min = "0";
        rmaInput.step = "1";
        rmaInput.value = result.rma;
        rmaInput.addEventListener("change", () => saveRMA(date, rmaInput.value));
        rmaCell.appendChild(rmaInput);
        tr.appendChild(rmaCell);

        const hcCell = document.createElement("td");
        const hcInput = document.createElement("input");
        hcInput.className = "hc-input";
        hcInput.type = "number";
        hcInput.min = "0";
        hcInput.step = "1";
        hcInput.value = hc;
        hcInput.addEventListener("change", () => saveHC(date, hcInput.value));
        hcCell.appendChild(hcInput);
        tr.appendChild(hcCell);

        const kpiCell = document.createElement("td");
        kpiCell.className = "kpi";
        kpiCell.textContent = formatKPI(kpi);
        tr.appendChild(kpiCell);

        tbody.appendChild(tr);
    });

    const grandKPI = grandHC > 0 ? grandTest / grandHC : 0;

    const totalRow = document.createElement("tr");
    totalRow.className = "total-row";

    [
        "TOTAL",
        formatNumber(grandInbound),
        formatNumber(grandTest),
        formatNumber(grandPass),
        formatNumber(grandFail),
        formatNumber(grandRMA),
        formatNumber(grandHC),
        formatKPI(grandKPI)
    ].forEach((value, index) => {
        const td = document.createElement("td");
        td.textContent = value;

        if (index === 0) td.className = "date-cell";
        if (index === 7) td.className = "kpi";

        totalRow.appendChild(td);
    });

    tbody.appendChild(totalRow);
}


// =========================================================
// INITIAL LOAD
// =========================================================

renderDateList();
updateDateButton();
updateTable();
autoSaveMissingHC();

document.addEventListener("click", function(event) {
    const area = document.querySelector(".filter-area");

    if (!area.contains(event.target)) {
        document.getElementById("dateDropdown").classList.remove("open");
    }
});
</script>
</body>
</html>
"""

# ============================================================
# INSERT JSON SAFELY
# ============================================================

html = html.replace(
    "__DATA_JSON__",
    data_json.replace("</", "<\\/"),
)

html = html.replace(
    "__HC_DATA_JSON__",
    hc_json.replace("</", "<\\/"),
)

html = html.replace(
    "__HC_API_URL_JSON__",
    json.dumps(HC_API_URL),
)


# ============================================================
# DISPLAY
# ============================================================

components.html(
    html,
    height=850,
    scrolling=True,
)