import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
import json
import re
from io import StringIO

st.set_page_config(
    page_title="RMA Regional KPI",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# GOOGLE SHEET
# =========================================================

YGN_2026_SHEET_ID = "14WOHloWhGuQOc95PrRUsYWAHT6PTCC6EL2pY18uglVs"
RMA_TAB = "RMA REPAIR"


def load_google_sheet(sheet_id, sheet_name):

    url = (
        f"https://docs.google.com/spreadsheets/d/"
        f"{sheet_id}/gviz/tq?tqx=out:csv"
        f"&sheet={requests.utils.quote(sheet_name)}"
    )

    headers = {
        "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "Chrome/130 Safari/537.36"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    text = response.text

    if "<html" in text.lower() or "<!doctype" in text.lower():

        raise Exception(
            "Google Sheet access မရပါ။\n\n"
            "Google Sheet → Share → General access → "
            "Anyone with the link → Viewer ထားပေးပါ။"
        )

    return pd.read_csv(StringIO(text))


# =========================================================
# NORMALIZE COLUMNS
# =========================================================

def normalize_columns(df):

    df = df.copy()

    df.columns = [
        str(c).strip()
        for c in df.columns
    ]

    column_map = {}

    for col in df.columns:

        n = (
            str(col)
            .strip()
            .lower()
            .replace("_", " ")
            .replace("-", " ")
        )

        n = re.sub(r"\s+", " ", n)

        if n in ["date", "day"]:
            column_map[col] = "Date"

        elif n == "region":
            column_map[col] = "Region"

        elif n in [
            "mac",
            "mac address",
            "macaddress"
        ]:
            column_map[col] = "MAC"

        elif n in [
            "status",
            "rma status",
            "repair status"
        ]:
            column_map[col] = "Status"

    df = df.rename(columns=column_map)

    required = [
        "Date",
        "Region",
        "MAC",
        "Status"
    ]

    missing = [
        c for c in required
        if c not in df.columns
    ]

    if missing:

        raise Exception(
            "Missing columns: "
            + ", ".join(missing)
            + "\n\nFound columns: "
            + ", ".join(map(str, df.columns))
        )

    return df


# =========================================================
# CLEAN DATA
# =========================================================

def clean_data(df):

    df = normalize_columns(df).copy()

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce"
    )

    df["Region"] = (
        df["Region"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df["MAC"] = (
        df["MAC"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["Status"] = (
        df["Status"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    df = df.dropna(
        subset=["Date"]
    )

    df["Date"] = df["Date"].dt.strftime(
        "%Y-%m-%d"
    )

    df = df[
        df["Region"].isin(
            ["ENUO", "HGAO"]
        )
    ].copy()

    return df


# =========================================================
# LOAD
# =========================================================

try:

    data = load_google_sheet(
        YGN_2026_SHEET_ID,
        RMA_TAB
    )

    data = clean_data(data)

except Exception as e:

    st.error(
        "RMA REPAIR Google Sheet Data မရပါ။\n\n"
        + str(e)
    )

    st.stop()


# =========================================================
# SORT
# =========================================================

data["_sort"] = pd.to_datetime(
    data["Date"],
    errors="coerce"
)

data = (
    data
    .sort_values("_sort")
    .drop(columns=["_sort"])
)


# =========================================================
# JSON
# =========================================================

records = data[
    [
        "Date",
        "Region",
        "MAC",
        "Status"
    ]
].to_dict(
    orient="records"
)

data_json = json.dumps(
    records,
    ensure_ascii=False
)


# =========================================================
# HTML
# =========================================================

html = r"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<style>
st.page_link(
    "pages/rma.py",
    label="ENUO & HGAO RMA",
    icon="📦"
)
* {
    box-sizing: border-box;
}

body {

    margin: 0;

    font-family:
        "Segoe UI",
        Arial,
        sans-serif;

    background:
        linear-gradient(
            135deg,
            #f5f7fb,
            #eef2f7
        );

    color: #172033;

}

.dashboard {

    width: 100%;

    max-width: 1550px;

    margin: auto;

    padding: 22px;

}


/* =====================================================
   HEADER
   ===================================================== */

.header {

    background:
        linear-gradient(
            135deg,
            #111827,
            #1f2937
        );

    color: white;

    border-radius: 18px;

    padding: 24px 28px;

    box-shadow:
        0 10px 30px
        rgba(15, 23, 42, 0.15);

    margin-bottom: 18px;

}

.header-title {

    font-size: 28px;

    font-weight: 800;

}

.header-subtitle {

    margin-top: 6px;

    font-size: 14px;

    color: #cbd5e1;

}


/* =====================================================
   DATE CONTROL
   ===================================================== */

.control-panel {

    background: white;

    border-radius: 16px;

    padding: 18px;

    margin-bottom: 18px;

    box-shadow:
        0 5px 20px
        rgba(15, 23, 42, 0.07);

}

.control-label {

    font-size: 13px;

    font-weight: 700;

    color: #475569;

    margin-bottom: 5px;

}

.select-box {

    position: relative;

    display: inline-block;

}

.main-button {

    min-width: 210px;

    height: 42px;

    border: 1px solid #d1d5db;

    background: white;

    border-radius: 10px;

    padding: 0 14px;

    font-size: 14px;

    cursor: pointer;

    text-align: left;

    color: #172033;

}

.main-button:hover {

    border-color: #64748b;

}


/* =====================================================
   DATE DROPDOWN
   ===================================================== */

.date-dropdown {

    display: none;

    position: absolute;

    top: 48px;

    left: 0;

    width: 310px;

    background: white;

    border: 1px solid #d9dee8;

    border-radius: 14px;

    padding: 12px;

    z-index: 9999;

    box-shadow:
        0 15px 40px
        rgba(15, 23, 42, 0.18);

}

.date-dropdown.show {

    display: block;

}

.search-date {

    width: 100%;

    height: 40px;

    border: 1px solid #d1d5db;

    border-radius: 9px;

    padding: 0 12px;

    font-size: 14px;

    outline: none;

    margin-bottom: 10px;

}

.search-date:focus {

    border-color: #2563eb;

    box-shadow:
        0 0 0 3px
        rgba(37, 99, 235, 0.10);

}

.date-top {

    display: flex;

    justify-content: space-between;

    align-items: center;

    padding: 5px 3px 9px;

    border-bottom: 1px solid #edf0f5;

}

.select-all-label {

    display: flex;

    align-items: center;

    gap: 8px;

    font-size: 13px;

    font-weight: 700;

    cursor: pointer;

}

.select-all-label input {

    width: 16px;

    height: 16px;

}

.date-list {

    max-height: 300px;

    overflow-y: auto;

    padding: 8px 2px;

}

.date-item {

    display: flex;

    align-items: center;

    gap: 9px;

    padding: 8px 7px;

    border-radius: 8px;

    cursor: pointer;

    font-size: 13px;

}

.date-item:hover {

    background: #f1f5f9;

}

.date-item input {

    width: 16px;

    height: 16px;

    cursor: pointer;

}

.date-actions {

    display: flex;

    justify-content: flex-end;

    gap: 8px;

    padding-top: 10px;

    border-top: 1px solid #edf0f5;

}

.btn {

    border: none;

    border-radius: 8px;

    padding: 9px 15px;

    cursor: pointer;

    font-size: 13px;

    font-weight: 700;

}

.btn-cancel {

    background: #f1f5f9;

    color: #334155;

}

.btn-apply {

    background: #2563eb;

    color: white;

}


/* =====================================================
   TABLE
   ===================================================== */

.table-card {

    background: white;

    border-radius: 16px;

    padding: 16px;

    box-shadow:
        0 5px 20px
        rgba(15, 23, 42, 0.07);

    overflow-x: auto;

}

table {

    width: 100%;

    border-collapse: separate;

    border-spacing: 0;

    min-width: 1100px;

}

thead th {

    background: #172033;

    color: white;

    padding: 12px 10px;

    font-size: 12px;

    text-align: center;

    border-right: 1px solid
        rgba(255,255,255,0.12);

}

thead tr:first-child th:first-child {

    border-top-left-radius: 10px;

}

thead tr:first-child th:last-child {

    border-top-right-radius: 10px;

}

tbody td {

    padding: 10px 8px;

    text-align: center;

    font-size: 13px;

    border-bottom: 1px solid #edf0f5;

    border-right: 1px solid #edf0f5;

}

tbody tr:hover td {

    background: #f8fafc;

}

.date-cell {

    font-weight: 700;

    color: #334155;

}

.number {

    font-weight: 700;

}

.kpi {

    font-weight: 800;

    color: #2563eb;

}

.reuse {

    font-weight: 800;

    color: #059669;

}

.reuse-percent {

    font-weight: 800;

    color: #7c3aed;

}


/* =====================================================
   HC INPUT
   ===================================================== */

.hc-input {

    width: 72px;

    height: 32px;

    text-align: center;

    border: 1px solid #cbd5e1;

    border-radius: 7px;

    outline: none;

    font-size: 13px;

    font-weight: 700;

}

.hc-input:focus {

    border-color: #2563eb;

    box-shadow:
        0 0 0 2px
        rgba(37, 99, 235, 0.10);

}


/* =====================================================
   EMPTY
   ===================================================== */

.empty {

    padding: 40px;

    text-align: center;

    color: #64748b;

    font-size: 14px;

}


/* =====================================================
   INFO
   ===================================================== */

.info {

    margin-top: 14px;

    background: #f8fafc;

    border: 1px solid #e2e8f0;

    border-radius: 12px;

    padding: 13px 16px;

    color: #475569;

    font-size: 12px;

    line-height: 1.8;

}

</style>

</head>


<body>

<div class="dashboard">


<!-- =================================================
     HEADER
     ================================================= -->

<div class="header">

    <div class="header-title">
        RMA Regional KPI
    </div>

    <div class="header-subtitle">
        RMA REPAIR • ENUO & HGAO
    </div>

</div>


<!-- =================================================
     DATE FILTER
     ================================================= -->

<div class="control-panel">

    <div class="select-box">

        <div class="control-label">
            Date
        </div>

        <button
            class="main-button"
            id="dateButton"
            onclick="toggleDateFilter()"
        >
            All Dates
        </button>


        <div
            class="date-dropdown"
            id="dateDropdown"
        >

            <input
                id="dateSearch"
                class="search-date"
                type="text"
                placeholder="🔍 Search date..."
                oninput="filterDateList()"
            >


            <div class="date-top">

                <label class="select-all-label">

                    <input
                        type="checkbox"
                        id="selectAllDates"
                        onchange="toggleAllDates()"
                    >

                    <span>
                        Select All
                    </span>

                </label>

                <span
                    id="dateCount"
                    style="
                        font-size:12px;
                        color:#64748b;
                    "
                ></span>

            </div>


            <div
                class="date-list"
                id="dateList"
            ></div>


            <div class="date-actions">

                <button
                    class="btn btn-cancel"
                    onclick="cancelDateFilter()"
                >
                    Cancel
                </button>

                <button
                    class="btn btn-apply"
                    onclick="applyDateFilter()"
                >
                    Apply
                </button>

            </div>

        </div>

    </div>

</div>


<!-- =================================================
     TABLE
     ================================================= -->

<div class="table-card">

    <div id="tableContainer"></div>

</div>


<!-- =================================================
     INFO
     ================================================= -->



</div>


</div>


<script>


// =====================================================
// DATA
// =====================================================

const DATA = __DATA_PLACEHOLDER__;


// =====================================================
// HC
// =====================================================

const DEFAULT_HC = {
    rma: 1
};

const STORAGE_KEY =
    "rma_dashboard_hc_v4";


// =====================================================
// DATE STATE
// =====================================================

let selectedDates = [];

let temporaryDates = [];


// =====================================================
// HC STORAGE
// =====================================================

function loadHC() {

    try {

        const raw =
            localStorage.getItem(
                STORAGE_KEY
            );

        if (!raw) {
            return {};
        }

        return JSON.parse(raw);

    } catch (e) {

        return {};

    }

}


function saveHC(obj) {

    localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(obj)
    );

}


function hcKey(
    date,
    region
) {

    return (
        date +
        "|" +
        region
    );

}


function getHC(
    date,
    region
) {

    const obj = loadHC();

    const key =
        hcKey(
            date,
            region
        );

    if (
        obj[key] !== undefined
    ) {

        return Number(
            obj[key]
        );

    }

    return Number(
        DEFAULT_HC.rma
    );

}


function setHC(
    date,
    region,
    value
) {

    const obj = loadHC();

    const key =
        hcKey(
            date,
            region
        );

    let num =
        Number(value);

    if (
        !Number.isFinite(num)
        ||
        num < 0
    ) {

        num = 0;

    }

    obj[key] = num;

    saveHC(obj);

    render();

}


// =====================================================
// FORMAT
// =====================================================

function fmt(value) {

    const n =
        Number(value);

    if (
        !Number.isFinite(n)
    ) {

        return "0";

    }

    return Math.round(n)
        .toLocaleString();

}


function fmtKPI(value) {

    const n =
        Number(value);

    if (
        !Number.isFinite(n)
        ||
        n <= 0
    ) {

        return "0";

    }

    return Math.round(n)
        .toLocaleString();

}


function fmtPercent(value) {

    const n =
        Number(value);

    if (
        !Number.isFinite(n)
    ) {

        return "0.00%";

    }

    return n.toFixed(2) + "%";

}


// =====================================================
// MAC COUNT
// =====================================================

function macCount(rows) {

    return rows.filter(
        r =>
            String(
                r.MAC ?? ""
            ).trim() !== ""
    ).length;

}


// =====================================================
// RMA COUNT
// =====================================================

function calculateRMA(
    region,
    rows
) {

    return macCount(
        rows.filter(
            r =>
                String(
                    r.Region ?? ""
                )
                .trim()
                .toUpperCase()
                === region
        )
    );

}


// =====================================================
// REUSE
// REPAIR PASS
// =====================================================

function calculateReuse(
    rows
) {

    return macCount(

        rows.filter(
            r => {

                const status =
                    String(
                        r.Status ?? ""
                    )
                    .trim()
                    .toLowerCase();

                return (
                    status ===
                    "repair pass"
                );

            }
        )

    );

}


// =====================================================
// DATES
// =====================================================

function getAllDates() {

    const set =
        new Set();

    DATA.forEach(
        r => {

            const d =
                String(
                    r.Date ?? ""
                ).trim();

            if (d) {

                set.add(d);

            }

        }
    );

    return Array.from(set).sort();

}


// =====================================================
// DATE LIST
// =====================================================

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
        .trim()
        .toLowerCase();


    const allDates =
        getAllDates();


    const filtered =
        allDates.filter(
            d =>
                d.toLowerCase()
                .includes(search)
        );


    list.innerHTML = "";


    if (
        filtered.length === 0
    ) {

        list.innerHTML = `
            <div
                style="
                    padding:20px;
                    text-align:center;
                    color:#94a3b8;
                    font-size:13px;
                "
            >
                No date found
            </div>
        `;

        updateSelectAll();

        return;

    }


    filtered.forEach(
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

            checkbox.checked =
                temporaryDates.includes(
                    date
                );


            checkbox.onchange =
                function() {

                    if (
                        this.checked
                    ) {

                        if (
                            !temporaryDates
                                .includes(date)
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

                    updateSelectAll();

                };


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


    document.getElementById(
        "dateCount"
    ).textContent =
        filtered.length +
        " dates";


    updateSelectAll();

}


// =====================================================
// SEARCH
// =====================================================

function filterDateList() {

    renderDateList();

}


// =====================================================
// SELECT ALL
// =====================================================

function toggleAllDates() {

    const checkbox =
        document.getElementById(
            "selectAllDates"
        );


    const search =
        document.getElementById(
            "dateSearch"
        )
        .value
        .trim()
        .toLowerCase();


    const dates =
        getAllDates().filter(
            d =>
                d
                .toLowerCase()
                .includes(search)
        );


    if (
        checkbox.checked
    ) {

        dates.forEach(
            date => {

                if (
                    !temporaryDates
                        .includes(date)
                ) {

                    temporaryDates.push(
                        date
                    );

                }

            }
        );

    } else {

        temporaryDates =
            temporaryDates.filter(
                d =>
                    !dates.includes(d)
            );

    }


    renderDateList();

}


// =====================================================
// UPDATE SELECT ALL
// =====================================================

function updateSelectAll() {

    const checkbox =
        document.getElementById(
            "selectAllDates"
        );

    if (!checkbox) {
        return;
    }


    const search =
        document.getElementById(
            "dateSearch"
        )
        .value
        .trim()
        .toLowerCase();


    const dates =
        getAllDates().filter(
            d =>
                d
                .toLowerCase()
                .includes(search)
        );


    const selected =
        dates.filter(
            d =>
                temporaryDates
                    .includes(d)
        ).length;


    checkbox.checked =
        dates.length > 0 &&
        selected === dates.length;


    checkbox.indeterminate =
        selected > 0 &&
        selected < dates.length;

}


// =====================================================
// OPEN DATE
// =====================================================

function toggleDateFilter() {

    const dropdown =
        document.getElementById(
            "dateDropdown"
        );


    if (
        dropdown.classList
            .contains("show")
    ) {

        dropdown.classList
            .remove("show");

        return;

    }


    temporaryDates =
        [...selectedDates];


    document.getElementById(
        "dateSearch"
    ).value = "";


    renderDateList();


    dropdown.classList
        .add("show");

}


// =====================================================
// APPLY
// =====================================================

function applyDateFilter() {

    selectedDates =
        [...temporaryDates];


    document.getElementById(
        "dateDropdown"
    )
    .classList
    .remove("show");


    updateDateButton();

    render();

}


// =====================================================
// CANCEL
// =====================================================

function cancelDateFilter() {

    temporaryDates =
        [...selectedDates];


    document.getElementById(
        "dateDropdown"
    )
    .classList
    .remove("show");


    document.getElementById(
        "dateSearch"
    ).value = "";

}


// =====================================================
// DATE BUTTON
// =====================================================

function updateDateButton() {

    const button =
        document.getElementById(
            "dateButton"
        );


    const allDates =
        getAllDates();


    if (
        selectedDates.length ===
        allDates.length
    ) {

        button.textContent =
            "All Dates";

    }

    else if (
        selectedDates.length === 0
    ) {

        button.textContent =
            "No Date Selected";

    }

    else {

        button.textContent =
            selectedDates.length +
            " Dates Selected";

    }

}


// =====================================================
// OUTSIDE CLICK
// =====================================================

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
            dropdown.classList
                .contains("show")
            &&
            !dropdown.contains(
                event.target
            )
            &&
            event.target !== button
        ) {

            dropdown.classList
                .remove("show");

        }

    }
);


// =====================================================
// RENDER TABLE
// =====================================================

function render() {

    const container =
        document.getElementById(
            "tableContainer"
        );


    let rows =
        DATA.filter(
            r =>
                selectedDates.includes(
                    String(
                        r.Date ?? ""
                    ).trim()
                )
        );


    const dates =
        selectedDates
            .filter(
                d =>
                    rows.some(
                        r =>
                            String(
                                r.Date ?? ""
                            ).trim()
                            === d
                    )
            )
            .sort();


    if (
        dates.length === 0
    ) {

        container.innerHTML = `
            <div class="empty">
                No data for selected date.
            </div>
        `;

        return;

    }


    let html = `

    <table>

        <thead>

            <tr>

                <th rowspan="2">
                    Date
                </th>

                <th colspan="3">
                    ENUO
                </th>

                <th colspan="3">
                    HGAO
                </th>

                <th colspan="3">
                    TOTAL RMA
                </th>

                <th rowspan="2">
                    REUSE
                </th>

                <th rowspan="2">
                    REUSE %
                </th>

            </tr>


            <tr>

                <th>RMA</th>
                <th>HC</th>
                <th>KPI</th>

                <th>RMA</th>
                <th>HC</th>
                <th>KPI</th>

                <th>Total</th>
                <th>HC</th>
                <th>KPI</th>

            </tr>

        </thead>

        <tbody>
    `;


    dates.forEach(
        date => {

            const dateRows =
                rows.filter(
                    r =>
                        String(
                            r.Date ?? ""
                        ).trim()
                        === date
                );


            // =========================================
            // RMA
            // =========================================

            const enuoRMA =
                calculateRMA(
                    "ENUO",
                    dateRows
                );


            const hgaoRMA =
                calculateRMA(
                    "HGAO",
                    dateRows
                );


            const totalRMA =
                enuoRMA +
                hgaoRMA;


            // =========================================
            // REUSE
            // =========================================

            const totalReuse =
                calculateReuse(
                    dateRows
                );


            // =========================================
            // HC
            // =========================================

            const enuoHC =
                getHC(
                    date,
                    "ENUO"
                );


            const hgaoHC =
                getHC(
                    date,
                    "HGAO"
                );


            const totalHC =
                enuoHC +
                hgaoHC;


            // =========================================
            // KPI
            // =========================================

            const enuoKPI =
                enuoHC > 0
                ?
                enuoRMA / enuoHC
                :
                0;


            const hgaoKPI =
                hgaoHC > 0
                ?
                hgaoRMA / hgaoHC
                :
                0;


            const totalKPI =
                totalHC > 0
                ?
                totalRMA / totalHC
                :
                0;


            // =========================================
            // REUSE %
            // =========================================

            const reusePercent =
                totalRMA > 0
                ?
                (
                    totalReuse /
                    totalRMA
                ) * 100
                :
                0;


            html += `

            <tr>

                <td class="date-cell">
                    ${date}
                </td>


                <!-- ENUO -->

                <td class="number">
                    ${fmt(enuoRMA)}
                </td>

                <td>

                    <input
                        class="hc-input"
                        type="number"
                        step="1"
                        min="0"
                        value="${enuoHC}"
                        onchange="
                            setHC(
                                '${date}',
                                'ENUO',
                                this.value
                            )
                        "
                    >

                </td>

                <td class="kpi">
                    ${fmtKPI(enuoKPI)}
                </td>


                <!-- HGAO -->

                <td class="number">
                    ${fmt(hgaoRMA)}
                </td>

                <td>

                    <input
                        class="hc-input"
                        type="number"
                        step="1"
                        min="0"
                        value="${hgaoHC}"
                        onchange="
                            setHC(
                                '${date}',
                                'HGAO',
                                this.value
                            )
                        "
                    >

                </td>

                <td class="kpi">
                    ${fmtKPI(hgaoKPI)}
                </td>


                <!-- TOTAL -->

                <td class="number">
                    ${fmt(totalRMA)}
                </td>

                <td>
                    ${fmt(totalHC)}
                </td>

                <td class="kpi">
                    ${fmtKPI(totalKPI)}
                </td>


                <!-- REUSE -->

                <td class="reuse">
                    ${fmt(totalReuse)}
                </td>


                <!-- REUSE % -->

                <td class="reuse-percent">
                    ${fmtPercent(reusePercent)}
                </td>

            </tr>

            `;

        }
    );


    html += `

        </tbody>

    </table>

    `;


    container.innerHTML =
        html;

}


// =====================================================
// INITIALIZE
// =====================================================

function setupDates() {

    const dates =
        getAllDates();

    selectedDates =
        [...dates];

    temporaryDates =
        [...dates];

    renderDateList();

    updateDateButton();

}


setupDates();

render();

</script>

</body>

</html>
"""


# =========================================================
# INSERT DATA
# =========================================================

html = html.replace(
    "__DATA_PLACEHOLDER__",
    data_json
)


# =========================================================
# STREAMLIT
# =========================================================



components.html(
    html,
    height=1900,
    scrolling=True
)