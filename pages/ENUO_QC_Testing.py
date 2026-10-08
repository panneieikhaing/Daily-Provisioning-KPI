# ============================================================
# ENUO_QC_TESTING.PY
# QC Testing - ENUO
# ============================================================

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
import json
from io import StringIO


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="QC Testing - ENUO",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# GOOGLE SHEET
# ============================================================

SHEET_ID = "14WOHloWhGuQOc95PrRUsYWAHT6PTCC6EL2pY18uglVs"
SHEET_TAB = ""


# ============================================================
# LOAD GOOGLE SHEET
# ============================================================

@st.cache_data(ttl=300)
def load_google_sheet():

    if SHEET_TAB:

        url = (
            f"https://docs.google.com/spreadsheets/d/"
            f"{SHEET_ID}/gviz/tq?"
            f"sheet={SHEET_TAB}&tqx=out:csv"
        )

    else:

        url = (
            f"https://docs.google.com/spreadsheets/d/"
            f"{SHEET_ID}/gviz/tq?"
            f"tqx=out:csv"
        )

    response = requests.get(
        url,
        timeout=30
    )

    response.raise_for_status()

    return pd.read_csv(
        StringIO(response.text)
    )


# ============================================================
# LOAD
# ============================================================

try:

    df = load_google_sheet()

except Exception as e:

    st.error(
        f"Unable to load Google Sheet: {e}"
    )

    st.stop()


# ============================================================
# REQUIRED COLUMNS
# ============================================================

required_columns = [
    "Date",
    "Device Name",
    "Daily (JD)",
    "Qty",
    "MAC",
    "Issue Type",
    "Region"
]

missing_columns = [
    col
    for col in required_columns
    if col not in df.columns
]

if missing_columns:

    st.error(
        "Missing columns: "
        + ", ".join(missing_columns)
    )

    st.stop()


# ============================================================
# CLEAN DATA
# ============================================================

df["Date"] = pd.to_datetime(
    df["Date"],
    errors="coerce"
)

df["Device Name"] = (
    df["Device Name"]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.lower()
)

df["Daily (JD)"] = (
    df["Daily (JD)"]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.lower()
)

df["Issue Type"] = (
    df["Issue Type"]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.lower()
)

df["MAC"] = (
    df["MAC"]
    .fillna("")
    .astype(str)
    .str.strip()
)

df["Region"] = (
    df["Region"]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.upper()
)

df["Qty"] = pd.to_numeric(
    df["Qty"],
    errors="coerce"
).fillna(0)


# ============================================================
# ENUO ONLY
# ============================================================

df = df[
    df["Region"] == "ENUO"
].copy()


# ============================================================
# DATE
# ============================================================

df = df[
    df["Date"].notna()
].copy()

df["Date"] = df["Date"].dt.strftime(
    "%Y-%m-%d"
)


# ============================================================
# CONVERT TO JSON
# ============================================================

records = []

for _, row in df.iterrows():

    records.append({
        "date": str(row["Date"]),
        "device": str(row["Device Name"]),
        "daily": str(row["Daily (JD)"]),
        "qty": float(row["Qty"]),
        "mac": str(row["MAC"]),
        "issueType": str(row["Issue Type"]),
        "region": str(row["Region"])
    })


data_json = json.dumps(
    records,
    ensure_ascii=False
)


# ============================================================
# HTML
# ============================================================

html = """
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    padding: 0;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    background: #f5f7fb;

    color: #1f2937;
}


/* ============================================================
   HEADER
   ============================================================ */

.header {
    background: white;

    padding: 20px 25px;

    border-radius: 14px;

    margin-bottom: 18px;

    box-shadow:
        0 2px 10px rgba(0,0,0,0.06);

    display: flex;

    justify-content: space-between;

    align-items: center;
}

.header-left {
    display: flex;

    flex-direction: column;

    gap: 5px;
}

.title {
    font-size: 28px;

    font-weight: 800;

    color: #111827;
}

.subtitle {
    font-size: 14px;

    color: #6b7280;

    font-weight: 600;
}

.region-badge {
    background: #eef2ff;

    color: #4338ca;

    padding: 9px 18px;

    border-radius: 20px;

    font-weight: 700;

    font-size: 14px;
}


/* ============================================================
   FILTER
   ============================================================ */

.filter-bar {
    background: white;

    padding: 15px 18px;

    border-radius: 12px;

    margin-bottom: 18px;

    box-shadow:
        0 2px 8px rgba(0,0,0,0.05);

    display: flex;

    align-items: center;

    gap: 12px;
}

.filter-label {
    font-weight: 700;

    color: #374151;

    font-size: 14px;
}

.date-container {
    position: relative;
}

.date-button {
    min-width: 240px;

    background: white;

    border: 1px solid #d1d5db;

    border-radius: 8px;

    padding: 10px 14px;

    cursor: pointer;

    font-size: 14px;

    text-align: left;
}

.date-button:hover {
    border-color: #6366f1;
}

.date-arrow {
    float: right;
}


/* ============================================================
   DROPDOWN
   ============================================================ */

.dropdown {
    display: none;

    position: absolute;

    top: 48px;

    left: 0;

    width: 300px;

    background: white;

    border: 1px solid #d1d5db;

    border-radius: 10px;

    box-shadow:
        0 8px 25px rgba(0,0,0,0.15);

    z-index: 9999;

    padding: 12px;
}

.dropdown.show {
    display: block;
}

.search-box {
    width: 100%;

    padding: 9px 10px;

    border: 1px solid #d1d5db;

    border-radius: 7px;

    margin-bottom: 10px;

    outline: none;
}

.search-box:focus {
    border-color: #6366f1;
}

.action-row {
    display: flex;

    gap: 8px;

    margin-bottom: 10px;
}

.small-btn {
    flex: 1;

    padding: 7px;

    border: 1px solid #d1d5db;

    background: #f9fafb;

    border-radius: 6px;

    cursor: pointer;

    font-size: 12px;

    font-weight: 600;
}

.date-list {
    max-height: 250px;

    overflow-y: auto;

    border-top: 1px solid #e5e7eb;

    border-bottom: 1px solid #e5e7eb;

    padding: 7px 0;
}

.date-item {
    display: flex;

    align-items: center;

    gap: 8px;

    padding: 7px 5px;

    font-size: 13px;

    cursor: pointer;
}

.date-item:hover {
    background: #f3f4f6;
}

.dropdown-footer {
    display: flex;

    gap: 8px;

    margin-top: 10px;
}

.apply-btn {
    flex: 1;

    background: #4f46e5;

    color: white;

    border: none;

    border-radius: 7px;

    padding: 8px;

    cursor: pointer;

    font-weight: 700;
}

.cancel-btn {
    flex: 1;

    background: white;

    color: #374151;

    border: 1px solid #d1d5db;

    border-radius: 7px;

    padding: 8px;

    cursor: pointer;

    font-weight: 600;
}


/* ============================================================
   TABLE
   ============================================================ */

.table-card {
    background: white;

    border-radius: 14px;

    box-shadow:
        0 2px 10px rgba(0,0,0,0.06);

    overflow: hidden;
}

.table-title {
    padding: 18px 20px;

    font-size: 18px;

    font-weight: 800;

    border-bottom: 1px solid #e5e7eb;

    color: #111827;
}

.table-wrapper {
    width: 100%;

    overflow-x: auto;
}

table {
    width: 100%;

    border-collapse: collapse;

    min-width: 950px;
}

thead th {
    background: #f8fafc;

    color: #374151;

    font-size: 13px;

    font-weight: 800;

    padding: 13px 10px;

    border-bottom: 1px solid #e5e7eb;

    text-align: center;
}

tbody td {
    padding: 13px 10px;

    border-bottom: 1px solid #eef0f3;

    text-align: center;

    font-size: 14px;
}

tbody tr:hover {
    background: #fafafa;
}

.total-row td {
    background: #f8fafc;

    font-weight: 800;

    border-top: 2px solid #d1d5db;
}

.number {
    font-weight: 700;
}

.kpi {
    font-weight: 800;

    color: #4f46e5;
}

.input-box {
    width: 75px;

    padding: 7px 8px;

    border: 1px solid #d1d5db;

    border-radius: 6px;

    text-align: center;

    font-weight: 700;

    outline: none;
}

.input-box:focus {
    border-color: #6366f1;
}

.empty {
    text-align: center;

    padding: 45px;

    color: #9ca3af;

    font-weight: 600;
}


/* ============================================================
   MOBILE
   ============================================================ */

@media (max-width: 700px) {

    .header {
        padding: 16px;
    }

    .title {
        font-size: 22px;
    }

    .filter-bar {
        flex-direction: column;

        align-items: stretch;
    }

    .date-button {
        width: 100%;
    }

    .dropdown {
        width: 300px;
    }
}

</style>

</head>


<body>


<!-- ============================================================
     HEADER
     ============================================================ -->

<div class="header">

    <div class="header-left">

        <div class="title">
            QC Testing
        </div>

        <div class="subtitle">
            Daily Provisioning Regional KPI
        </div>

    </div>

    <div class="region-badge">
        ENUO
    </div>

</div>


<!-- ============================================================
     DATE FILTER
     ============================================================ -->

<div class="filter-bar">

    <div class="filter-label">
        Date
    </div>

    <div class="date-container">

        <button
            class="date-button"
            id="dateButton"
            onclick="toggleDropdown()"
        >
            All Dates
            <span class="date-arrow">▼</span>
        </button>


        <div
            class="dropdown"
            id="dateDropdown"
        >

            <input
                class="search-box"
                id="dateSearch"
                placeholder="Search date..."
                oninput="filterDates()"
            >


            <div class="action-row">

                <button
                    class="small-btn"
                    onclick="selectAllDates()"
                >
                    Select All
                </button>

                <button
                    class="small-btn"
                    onclick="clearDates()"
                >
                    Clear
                </button>

            </div>


            <div
                class="date-list"
                id="dateList"
            ></div>


            <div class="dropdown-footer">

                <button
                    class="cancel-btn"
                    onclick="cancelDates()"
                >
                    Cancel
                </button>

                <button
                    class="apply-btn"
                    onclick="applyDates()"
                >
                    Apply
                </button>

            </div>

        </div>

    </div>

</div>


<!-- ============================================================
     TABLE
     ============================================================ -->

<div class="table-card">

    <div class="table-title">
        QC Testing Daily Detail
    </div>

    <div class="table-wrapper">

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

            <tbody
                id="tableBody"
            ></tbody>

        </table>

    </div>

</div>


<script>


// ============================================================
// DATA
// ============================================================

const DATA = __DATA_JSON_PLACEHOLDER__;


// ============================================================
// VARIABLES
// ============================================================

let selectedDates = [];

let temporaryDates = [];


// ============================================================
// LOCAL STORAGE
//
// HC / RMA ကို browser ထဲမှာ သိမ်းထားမယ်
// ============================================================

const STORAGE_HC =
    "ENUO_QC_TESTING_HC";

const STORAGE_RMA =
    "ENUO_QC_TESTING_RMA";


// ============================================================
// LOAD SAVED HC
// ============================================================

let hcValues = {};

try {

    hcValues =
        JSON.parse(
            localStorage.getItem(
                STORAGE_HC
            ) || "{}"
        );

} catch (e) {

    hcValues = {};

}


// ============================================================
// LOAD SAVED RMA
// ============================================================

let rmaValues = {};

try {

    rmaValues =
        JSON.parse(
            localStorage.getItem(
                STORAGE_RMA
            ) || "{}"
        );

} catch (e) {

    rmaValues = {};

}


// ============================================================
// ALL DATES
// ============================================================

const allDates = [
    ...new Set(
        DATA
            .map(row => row.date)
            .filter(date => date)
    )
].sort();


// ============================================================
// DEFAULT VALUES
//
// မရှိသေးတဲ့ date တွေကိုသာ default ထည့်
// ရှိပြီးသား saved value ကို မထိ
// ============================================================

allDates.forEach(
    date => {

        if (
            hcValues[date] === undefined
        ) {

            hcValues[date] = 1;

        }

        if (
            rmaValues[date] === undefined
        ) {

            rmaValues[date] = 0;

        }

    }
);


// ============================================================
// SAVE HC
// ============================================================

function saveHC() {

    localStorage.setItem(
        STORAGE_HC,
        JSON.stringify(
            hcValues
        )
    );

}


// ============================================================
// SAVE RMA
// ============================================================

function saveRMA() {

    localStorage.setItem(
        STORAGE_RMA,
        JSON.stringify(
            rmaValues
        )
    );

}


// ============================================================
// FORMAT NUMBER
// ============================================================

function formatNumber(value) {

    if (!Number.isFinite(value)) {

        return "0";

    }

    return Number(value).toLocaleString(
        "en-US",
        {
            maximumFractionDigits: 0
        }
    );

}


// ============================================================
// KPI WHOLE NUMBER
// ============================================================

function formatKPI(value) {

    if (!Number.isFinite(value)) {

        return "0";

    }

    return Math.round(value).toString();

}


// ============================================================
// DATE DROPDOWN
// ============================================================

function toggleDropdown() {

    const dropdown =
        document.getElementById(
            "dateDropdown"
        );

    if (
        dropdown.classList.contains(
            "show"
        )
    ) {

        dropdown.classList.remove(
            "show"
        );

    } else {

        temporaryDates = [
            ...selectedDates
        ];

        renderDateList();

        dropdown.classList.add(
            "show"
        );

    }

}


// ============================================================
// DATE LIST
// ============================================================

function renderDateList() {

    const list =
        document.getElementById(
            "dateList"
        );

    const search =
        document.getElementById(
            "dateSearch"
        )
        .value
        .toLowerCase()
        .trim();


    list.innerHTML = "";


    allDates
        .filter(
            date =>
                date
                    .toLowerCase()
                    .includes(search)
        )
        .forEach(
            date => {

                const label =
                    document.createElement(
                        "label"
                    );

                label.className =
                    "date-item";


                const checkbox =
                    document.createElement(
                        "input"
                    );

                checkbox.type =
                    "checkbox";

                checkbox.value =
                    date;

                checkbox.checked =
                    temporaryDates.includes(
                        date
                    );


                checkbox.addEventListener(
                    "change",
                    function() {

                        if (
                            this.checked
                        ) {

                            if (
                                !temporaryDates.includes(
                                    date
                                )
                            ) {

                                temporaryDates.push(
                                    date
                                );

                            }

                        } else {

                            temporaryDates =
                                temporaryDates.filter(
                                    d =>
                                        d !== date
                                );

                        }

                    }
                );


                const text =
                    document.createElement(
                        "span"
                    );

                text.textContent =
                    date;


                label.appendChild(
                    checkbox
                );

                label.appendChild(
                    text
                );

                list.appendChild(
                    label
                );

            }
        );

}


// ============================================================
// SEARCH
// ============================================================

function filterDates() {

    renderDateList();

}


// ============================================================
// SELECT ALL
// ============================================================

function selectAllDates() {

    temporaryDates = [
        ...allDates
    ];

    renderDateList();

}


// ============================================================
// CLEAR
// ============================================================

function clearDates() {

    temporaryDates = [];

    renderDateList();

}


// ============================================================
// CANCEL
// ============================================================

function cancelDates() {

    temporaryDates = [
        ...selectedDates
    ];

    document
        .getElementById(
            "dateDropdown"
        )
        .classList.remove(
            "show"
        );

}


// ============================================================
// APPLY
// ============================================================

function applyDates() {

    selectedDates = [
        ...temporaryDates
    ];

    document
        .getElementById(
            "dateDropdown"
        )
        .classList.remove(
            "show"
        );

    updateDateButton();

    renderTable();

}


// ============================================================
// DATE BUTTON
// ============================================================

function updateDateButton() {

    const button =
        document.getElementById(
            "dateButton"
        );


    if (
        selectedDates.length === 0 ||
        selectedDates.length === allDates.length
    ) {

        button.innerHTML =
            `All Dates
             <span class="date-arrow">▼</span>`;

    } else if (
        selectedDates.length === 1
    ) {

        button.innerHTML =
            `${selectedDates[0]}
             <span class="date-arrow">▼</span>`;

    } else {

        button.innerHTML =
            `${selectedDates.length} Dates Selected
             <span class="date-arrow">▼</span>`;

    }

}


// ============================================================
// PREVIOUS DATE
//
// ဥပမာ
//
// 2026-10-01 row
// QC Inbound = 2026-09-30 data
//
// 2026-10-02 row
// QC Inbound = 2026-10-01 data
//
// 2026-10-01 မှာ 2026-09-30 (31 ရက်)
// ရဲ့ QC Inbound ကို ပြမယ်
// ============================================================

function getPreviousDate(date) {

    const d =
        new Date(
            date + "T00:00:00"
        );

    d.setDate(
        d.getDate() - 1
    );

    return d
        .toISOString()
        .split("T")[0];

}


// ============================================================
// QC INBOUND CALCULATION
//
// IMPORTANT:
// QC Inbound ကို row ရဲ့နေ့မှာ မတွက်ဘူး
// မနေ့က data ကို ဒီနေ့ row ထဲထည့်မယ်
// ============================================================

// ============================================================
// QC INBOUND
// 1 DAY SHIFT ONLY
//
// Example:
// 2026-09-30 data -> 2026-10-01 row
// 2026-10-01 data -> 2026-10-02 row
// 2026-10-02 data -> 2026-10-03 row
// ============================================================

function calculateQCInbound(targetDate) {

    // Dashboard မှာ တကယ်ရှိတဲ့ dates တွေကိုပဲယူ
    const availableDates = [...new Set(
        DATA
            .map(row => row.date)
            .filter(d => d)
    )].sort();

    // Current date ရဲ့ index
    const currentIndex = availableDates.indexOf(targetDate);

    // ပထမဆုံး date ဆိုရင် previous date မရှိ
    if (currentIndex <= 0) {
        return 0;
    }

    // Calendar previous day မဟုတ်ဘဲ
    // Date list ထဲက ရှေ့ကရှိတဲ့ date ကိုယူ
    const sourceDate = availableDates[currentIndex - 1];

    let total = 0;

    DATA.forEach(row => {

        if (row.date !== sourceDate) return;

        const daily = String(row.daily || "")
            .trim()
            .toLowerCase();

        const device = String(row.device || "")
            .trim()
            .toLowerCase();

        const mac = String(row.mac || "").trim();

        const qty = Number(row.qty) || 0;

        // RUN → MAC Count
        if (daily === "run" && mac !== "") {
            total += 1;
        }

        // CLEANING + FFO → Qty Sum
        if (daily === "cleaning" && device === "ffo") {
            total += qty;
        }
    });

    return total;
}


// ============================================================
// NORMAL DAILY CALCULATION
//
// TOTAL TEST / PASS / FAIL
// မပြောင်း
// ============================================================

function calculate(date) {

    const rows =
        DATA.filter(
            row =>
                row.date === date
        );


    // =========================================================
    // QC INBOUND
    //
    // မနေ့က data ကို ဒီနေ့ row ထဲထည့်
    // =========================================================

    const qcInbound =
        calculateQCInbound(
            date
        );


    let totalTest = 0;

    let qcPass = 0;

    let qcFail = 0;


    rows.forEach(
        row => {

            const daily =
                String(
                    row.daily || ""
                )
                .trim()
                .toLowerCase();


            const issueType =
                String(
                    row.issueType || ""
                )
                .trim()
                .toLowerCase();


            const qty =
                Number(
                    row.qty
                ) || 0;


            // =================================================
            // TOTAL TEST
            //
            // SPEED TEST
            // LAN PORT TEST
            // DBM
            //
            // ALL = QTY SUM
            // =================================================

            if (
                daily === "speed test" ||
                daily === "lan port test" ||
                daily === "dbm"
            ) {

                totalTest += qty;


                // =============================================
                // QC PASS
                // =============================================

                if (
                    issueType === "use"
                ) {

                    qcPass += qty;

                }


                // =============================================
                // QC FAIL
                // =============================================

                if (
                    issueType === "rma"
                ) {

                    qcFail += qty;

                }

            }

        }
    );


    // =========================================================
    // SAVED MANUAL RMA
    // =========================================================

    const rma =
        Number(
            rmaValues[date]
        ) || 0;


    // =========================================================
    // SAVED MANUAL HC
    // =========================================================

    const hc =
        Number(
            hcValues[date]
        ) || 0;


    // =========================================================
    // KPI
    // =========================================================

    const kpi =
        hc > 0
            ? totalTest / hc
            : 0;


    return {

        date: date,

        qcInbound: qcInbound,

        totalTest: totalTest,

        qcPass: qcPass,

        qcFail: qcFail,

        rma: rma,

        hc: hc,

        kpi: kpi

    };

}


// ============================================================
// UPDATE HC
//
// ရိုက်ပြီးတာနဲ့ Local Storage ထဲသိမ်း
// ============================================================

function updateHC(
    date,
    value
) {

    hcValues[date] =
        Number(value) || 0;


    saveHC();

    renderTable();

}


// ============================================================
// UPDATE RMA
//
// ရိုက်ပြီးတာနဲ့ Local Storage ထဲသိမ်း
// ============================================================

function updateRMA(
    date,
    value
) {

    rmaValues[date] =
        Number(value) || 0;


    saveRMA();

    renderTable();

}


// ============================================================
// RENDER TABLE
// ============================================================

function renderTable() {

    const body =
        document.getElementById(
            "tableBody"
        );


    body.innerHTML = "";


    let datesToShow;


    if (
        selectedDates.length === 0 ||
        selectedDates.length === allDates.length
    ) {

        datesToShow = [
            ...allDates
        ];

    } else {

        datesToShow = [
            ...selectedDates
        ].sort();

    }


    if (
        datesToShow.length === 0
    ) {

        body.innerHTML = `
            <tr>
                <td
                    colspan="8"
                    class="empty"
                >
                    No Date Selected
                </td>
            </tr>
        `;

        return;

    }


    let grandQCInbound = 0;

    let grandTotalTest = 0;

    let grandQCPass = 0;

    let grandQCFail = 0;

    let grandRMA = 0;

    let grandHC = 0;


    // =========================================================
    // DAILY ROWS
    // =========================================================

    datesToShow.forEach(
        date => {

            const result =
                calculate(date);


            grandQCInbound +=
                result.qcInbound;

            grandTotalTest +=
                result.totalTest;

            grandQCPass +=
                result.qcPass;

            grandQCFail +=
                result.qcFail;

            grandRMA +=
                result.rma;

            grandHC +=
                result.hc;


            const tr =
                document.createElement(
                    "tr"
                );


            tr.innerHTML = `

                <td>
                    <strong>
                        ${result.date}
                    </strong>
                </td>


                <td class="number">
                    ${formatNumber(
                        result.qcInbound
                    )}
                </td>


                <td class="number">
                    ${formatNumber(
                        result.totalTest
                    )}
                </td>


                <td class="number">
                    ${formatNumber(
                        result.qcPass
                    )}
                </td>


                <td class="number">
                    ${formatNumber(
                        result.qcFail
                    )}
                </td>


                <td>

                    <input
                        class="input-box"
                        type="number"
                        min="0"
                        step="1"
                        value="${result.rma}"
                        onchange="
                            updateRMA(
                                '${result.date}',
                                this.value
                            )
                        "
                    >

                </td>


                <td>

                    <input
                        class="input-box"
                        type="number"
                        min="0"
                        step="1"
                        value="${result.hc}"
                        onchange="
                            updateHC(
                                '${result.date}',
                                this.value
                            )
                        "
                    >

                </td>


                <td class="kpi">
                    ${formatKPI(
                        result.kpi
                    )}
                </td>

            `;


            body.appendChild(
                tr
            );

        }
    );


    // =========================================================
    // TOTAL KPI
    // =========================================================

    const totalKPI =
        grandHC > 0
            ? grandTotalTest / grandHC
            : 0;


    // =========================================================
    // TOTAL ROW
    // =========================================================

    const totalRow =
        document.createElement(
            "tr"
        );

    totalRow.className =
        "total-row";


    totalRow.innerHTML = `

        <td>
            TOTAL
        </td>


        <td>
            ${formatNumber(
                grandQCInbound
            )}
        </td>


        <td>
            ${formatNumber(
                grandTotalTest
            )}
        </td>


        <td>
            ${formatNumber(
                grandQCPass
            )}
        </td>


        <td>
            ${formatNumber(
                grandQCFail
            )}
        </td>


        <td>
            ${formatNumber(
                grandRMA
            )}
        </td>


        <td>
            ${formatNumber(
                grandHC
            )}
        </td>


        <td class="kpi">
            ${formatKPI(
                totalKPI
            )}
        </td>

    `;


    body.appendChild(
        totalRow
    );

}


// ============================================================
// CLICK OUTSIDE
// ============================================================

document.addEventListener(
    "click",
    function(event) {

        const dropdown =
            document.getElementById(
                "dateDropdown"
            );

        const button =
            document.getElementById(
                "dateButton"
            );


        if (
            !dropdown.contains(
                event.target
            ) &&
            !button.contains(
                event.target
            )
        ) {

            dropdown.classList.remove(
                "show"
            );

        }

    }
);


// ============================================================
// INITIAL DATA
// ============================================================

renderDateList();

renderTable();

</script>

</body>

</html>
"""


# ============================================================
# INSERT JSON
# ============================================================

html = html.replace(
    "__DATA_JSON_PLACEHOLDER__",
    data_json
)


# ============================================================
# DISPLAY
# ============================================================

components.html(
    html,
    height=850,
    scrolling=True
)