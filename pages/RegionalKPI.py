import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
import json
import re
from io import StringIO


# ============================================================
# PAGE CONFIG
# ============================================================



# ============================================================
# GOOGLE SHEET IDs
# ============================================================

ENUO_HGAO_SHEET_ID = "14WOHloWhGuQOc95PrRUsYWAHT6PTCC6EL2pY18uglVs"
MDY_SHEET_ID = "1XrjpVgSeu1lDpyNNyuJdjYji8MxnoQWuo3bwwPWAs9Q"

SHEET1_TAB = ""
SHEET2_TAB = ""


# ============================================================
# LOAD GOOGLE SHEET
# ============================================================

def load_google_sheet(sheet_id, sheet_name=""):

    if sheet_name:
        url = (
            f"https://docs.google.com/spreadsheets/d/"
            f"{sheet_id}/gviz/tq?tqx=out:csv"
            f"&sheet={requests.utils.quote(sheet_name)}"
        )
    else:
        url = (
            f"https://docs.google.com/spreadsheets/d/"
            f"{sheet_id}/gviz/tq?tqx=out:csv"
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

    if (
        "<html" in text.lower()
        or "<!doctype" in text.lower()
    ):
        raise Exception(
            "Google Sheet access မရပါ။ "
            "Sharing ကို Anyone with the link → Viewer "
            "ထားပါ။"
        )

    return pd.read_csv(
        StringIO(text)
    )


# ============================================================
# NORMALIZE COLUMNS
# ============================================================

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

        n = re.sub(
            r"\s+",
            " ",
            n
        )

        if n in [
            "date",
            "day"
        ]:
            column_map[col] = "Date"

        elif n == "region":
            column_map[col] = "Region"

        elif n in [
            "daily (jd)",
            "daily jd",
            "daily(jd)",
            "daily"
        ]:
            column_map[col] = "Daily (JD)"

        elif n in [
            "qty",
            "quantity"
        ]:
            column_map[col] = "Qty"

        elif n in [
            "mac",
            "mac address",
            "macaddress"
        ]:
            column_map[col] = "MAC"

    df = df.rename(
        columns=column_map
    )

    required = [
        "Date",
        "Region",
        "Daily (JD)",
        "Qty",
        "MAC"
    ]

    missing = [
        c
        for c in required
        if c not in df.columns
    ]

    if missing:
        raise Exception(
            "Missing columns: "
            + ", ".join(missing)
            + "\n\nFound columns: "
            + ", ".join(
                map(str, df.columns)
            )
        )

    return df


# ============================================================
# CLEAN DATA
# ============================================================

def clean_data(df):

    df = normalize_columns(df)

    df = df.copy()

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce"
    )

    df["Region"] = (
        df["Region"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df["Daily (JD)"] = (
        df["Daily (JD)"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    df["Qty"] = pd.to_numeric(
        df["Qty"],
        errors="coerce"
    ).fillna(0)

    df["MAC"] = (
        df["MAC"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df = df.dropna(
        subset=["Date"]
    )

    df["Date"] = df["Date"].dt.strftime(
        "%Y-%m-%d"
    )

    return df


# ============================================================
# LOAD BOTH SHEETS
# ============================================================

try:

    df1 = load_google_sheet(
        ENUO_HGAO_SHEET_ID,
        SHEET1_TAB
    )

    df2 = load_google_sheet(
        MDY_SHEET_ID,
        SHEET2_TAB
    )

    df1 = clean_data(df1)

    df2 = clean_data(df2)

    data = pd.concat(
        [df1, df2],
        ignore_index=True
    )

except Exception as e:

    st.error(
        "Google Sheet Data မရပါ။\n\n"
        + str(e)
    )

    st.stop()


# ============================================================
# ONLY ENUO / HGAO / MDY
# ============================================================

data = data[
    data["Region"].isin(
        [
            "ENUO",
            "HGAO",
            "MDY"
        ]
    )
].copy()


# ============================================================
# SORT DATE
# ============================================================

data["_date_sort"] = pd.to_datetime(
    data["Date"],
    errors="coerce"
)

data = data.sort_values(
    "_date_sort"
)

data = data.drop(
    columns=["_date_sort"]
)


# ============================================================
# JSON
# ============================================================

records = data[
    [
        "Date",
        "Region",
        "Daily (JD)",
        "Qty",
        "MAC"
    ]
].to_dict(
    orient="records"
)

data_json = json.dumps(
    records,
    ensure_ascii=False
)


# ============================================================
# HTML
# ============================================================

html = r"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<style>

/* =========================================================
   GLOBAL
   ========================================================= */

* {
    box-sizing: border-box;
}

html,
body {
    margin: 0;
    padding: 0;
}

body {

    font-family:
        "Segoe UI",
        Arial,
        sans-serif;

    background:
        linear-gradient(
            135deg,
            #eef4ff 0%,
            #f7f9fc 45%,
            #eef2f7 100%
        );

    color: #172033;

    padding: 24px;

}


.container {

    width: 100%;

    max-width: 1550px;

    margin: 0 auto;

}


/* =========================================================
   TOP HEADER
   ========================================================= */

.top-header {

    width: 100%;

    min-height: 74px;

    background: #ffffff;

    border: 1px solid #e1e6ed;

    border-radius: 16px;

    display: flex;

    align-items: center;

    justify-content: space-between;

    padding: 12px 20px;

    margin-bottom: 20px;

    box-shadow:
        0 6px 22px rgba(
            15,
            35,
            65,
            0.08
        );

}


.brand {

    display: flex;

    align-items: center;

    gap: 11px;

    min-width: 210px;

}

.brand-text {
    line-height: 1.1;
}

.brand-title {

    font-size: 18px;

    font-weight: 800;

    color: #111111;

}


/* =========================================================
   NAV
   ========================================================= */

.nav-bar {

    display: flex;

    align-items: center;

    justify-content: center;

    gap: 8px;

}

.nav-btn {

    text-decoration: none;

    background: #111111;

    color: #ffffff;

    padding: 9px 18px;

    border-radius: 8px;

    font-size: 13px;

    font-weight: 700;

}

.nav-btn:hover {

    background: #333333;

}


/* =========================================================
   TOOLBAR
   ========================================================= */

.toolbar {

    background: rgba(
        255,
        255,
        255,
        0.94
    );

    border: 1px solid #e1e7ef;

    border-radius: 15px;

    padding: 13px 16px;

    margin-bottom: 20px;

    box-shadow:
        0 5px 18px rgba(
            15,
            35,
            65,
            0.07
        );

}


/* =========================================================
   FILTER
   ========================================================= */

.filter-box {

    position: relative;

    display: inline-block;

}

.filter-button {

    background:
        linear-gradient(
            135deg,
            #ffffff,
            #f4f7fb
        );

    color: #24344d;

    border: 1px solid #cbd5e1;

    border-radius: 9px;

    padding: 10px 17px;

    min-width: 175px;

    text-align: left;

    font-size: 14px;

    font-weight: 600;

    cursor: pointer;

}

.filter-button:hover {

    border-color: #111111;

    color: #111111;

    box-shadow:
        0 4px 12px rgba(
            0,
            0,
            0,
            0.10
        );

}


/* =========================================================
   FILTER MENU
   ========================================================= */

.filter-menu {

    display: none;

    position: absolute;

    top: 48px;

    left: 0;

    background: white;

    border: 1px solid #d8dee8;

    border-radius: 12px;

    width: 310px;

    max-height: 500px;

    overflow: hidden;

    z-index: 99999;

    box-shadow:
        0 12px 30px rgba(
            0,
            0,
            0,
            0.16
        );

}

.filter-menu.show {

    display: block;

}


/* =========================================================
   DATE SEARCH
   ========================================================= */

.date-search-wrapper {

    padding: 10px;

    background: #ffffff;

    border-bottom:
        1px solid #e5e9ef;

    position: sticky;

    top: 0;

    z-index: 10;

}

.date-search-box {

    display: flex;

    align-items: center;

    gap: 7px;

    width: 100%;

    height: 38px;

    padding: 0 9px;

    border: 1px solid #cbd5e1;

    border-radius: 8px;

    background: #f8fafc;

}

.date-search-box:focus-within {

    border-color: #111111;

    box-shadow:
        0 0 0 3px rgba(
            0,
            0,
            0,
            0.06
        );

}

.date-search-icon {

    font-size: 15px;

}

.date-search-input {

    flex: 1;

    border: none;

    outline: none;

    background: transparent;

    font-size: 13px;

    color: #1e293b;

}

.clear-search {

    border: none;

    background: transparent;

    color: #64748b;

    font-size: 15px;

    cursor: pointer;

    display: none;

}

.clear-search:hover {

    color: #111111;

}

.search-info {

    display: flex;

    justify-content: space-between;

    align-items: center;

    margin-top: 6px;

    font-size: 10px;

    color: #64748b;

}


/* =========================================================
   DATE OPTIONS
   ========================================================= */

.date-options {

    max-height: 310px;

    overflow-y: auto;

}

.filter-item {

    display: flex;

    align-items: center;

    gap: 9px;

    padding: 9px 14px;

    cursor: pointer;

    font-size: 14px;

    color: #26364d;

    transition:
        background 0.15s ease;

}

.filter-item:hover {

    background: #f3f7fd;

}

.filter-item input {

    width: 16px;

    height: 16px;

    cursor: pointer;

    accent-color: #111111;

}

.select-all {

    border-bottom:
        1px solid #e5e9ef;

    font-weight: 700;

    color: #1d3f70;

    background: #fafbfc;

}


/* =========================================================
   NO SEARCH RESULT
   ========================================================= */

.no-date-result {

    padding: 20px 12px;

    text-align: center;

    color: #94a3b8;

    font-size: 13px;

}


/* =========================================================
   FILTER BUTTONS
   ========================================================= */

.filter-actions {

    display: flex;

    gap: 8px;

    padding: 10px 12px 10px;

    border-top:
        1px solid #e5e9ef;

    background: white;

}

.apply-button {

    flex: 1;

    background: #111111;

    color: white;

    border: none;

    border-radius: 7px;

    padding: 8px;

    cursor: pointer;

    font-weight: 700;

}

.apply-button:hover {

    background: #333333;

}

.cancel-button {

    flex: 1;

    background: white;

    color: #475569;

    border: 1px solid #cbd5e1;

    border-radius: 7px;

    padding: 8px;

    cursor: pointer;

    font-weight: 600;

}

.cancel-button:hover {

    background: #f5f7fa;

}


/* =========================================================
   REGION CARD
   ========================================================= */

.region-card {

    background:
        rgba(
            255,
            255,
            255,
            0.97
        );

    border:
        1px solid #e0e6ee;

    border-radius: 18px;

    padding: 18px;

    margin-bottom: 22px;

    box-shadow:
        0 7px 24px rgba(
            15,
            35,
            65,
            0.08
        );

    overflow: hidden;

}


.region-card:hover {

    transform:
        translateY(-2px);

    box-shadow:
        0 12px 30px rgba(
            15,
            35,
            65,
            0.11
        );

}


/* =========================================================
   REGION TITLE
   ========================================================= */

.region-title {

    display: flex;

    align-items: center;

    justify-content: center;

    font-size: 21px;

    font-weight: 800;

    color: #17345f;

    padding: 5px 0 15px;

    text-align: center;

}

.region-title::before {

    content: "";

    width: 7px;

    height: 24px;

    border-radius: 5px;

    background: #111111;

    margin-right: 10px;

}

.region-title::after {

    content: "";

    width: 7px;

    height: 24px;

    border-radius: 5px;

    background: #111111;

    margin-left: 10px;

}


/* =========================================================
   TABLE
   ========================================================= */

.table-wrap {

    width: 100%;

    overflow-x: auto;

    border-radius: 12px;

    border: 1px solid #e1e6ed;

}

table {

    width: 100%;

    border-collapse: separate;

    border-spacing: 0;

    min-width: 950px;

}

thead tr:first-child th {

    background:
        linear-gradient(
            135deg,
            #172b4d,
            #214675
        );

    color: white;

    padding: 11px 8px;

    text-align: center;

    font-size: 13px;

    font-weight: 700;

    border-right:
        1px solid rgba(
            255,
            255,
            255,
            0.12
        );

}

thead tr:nth-child(2) th {

    background: #edf3fa;

    color: #28415f;

    padding: 8px 7px;

    text-align: center;

    font-size: 12px;

    font-weight: 700;

    border-right:
        1px solid #dce4ee;

    border-bottom:
        1px solid #dce4ee;

}

td {

    border-right:
        1px solid #e1e6ed;

    border-bottom:
        1px solid #e1e6ed;

    padding: 8px 7px;

    text-align: center;

    font-size: 13px;

    color: #26364d;

    background: white;

}

tbody tr:nth-child(even) td {

    background: #f8fafc;

}

tbody tr:hover td {

    background: #eef5ff;

}

.date-cell {

    font-weight: 700;

    white-space: nowrap;

    color: #173f70;

}

.total-cell {

    font-weight: 800;

    color: #1d3659;

}

.kpi-cell {

    font-weight: 800;

    color: #155db3;

}


/* =========================================================
   HC INPUT
   ========================================================= */

.hc-input {

    width: 68px;

    padding: 6px 5px;

    text-align: center;

    border:
        1px solid #cbd5e1;

    border-radius: 7px;

    font-size: 13px;

    font-weight: 600;

    color: #26364d;

    background: white;

}

.hc-input:focus {

    outline: none;

    border-color: #111111;

    box-shadow:
        0 0 0 3px rgba(
            0,
            0,
            0,
            0.08
        );

}

.hc-input:disabled {

    background: #f1f5f9;

    color: #64748b;

    cursor: not-allowed;

}


/* =========================================================
   NOTE
   ========================================================= */

.note {

    font-size: 12px;

    color: #64748b;

    margin-top: 9px;

    padding-left: 3px;

}


/* =========================================================
   SCROLLBAR
   ========================================================= */

.date-options::-webkit-scrollbar,
.table-wrap::-webkit-scrollbar {

    width: 7px;

    height: 8px;

}

.date-options::-webkit-scrollbar-track,
.table-wrap::-webkit-scrollbar-track {

    background: #eef2f7;

}

.date-options::-webkit-scrollbar-thumb,
.table-wrap::-webkit-scrollbar-thumb {

    background: #b8c5d6;

    border-radius: 10px;

}


/* =========================================================
   RESPONSIVE
   ========================================================= */

@media (max-width: 900px) {

    .top-header {

        flex-wrap: wrap;

        gap: 12px;

    }

    .nav-bar {

        order: 3;

        width: 100%;

        overflow-x: auto;

        justify-content: flex-start;

    }

}

@media (max-width: 700px) {

    body {

        padding: 12px;

    }

    .filter-menu {

        width: 290px;

    }

    .region-card {

        padding: 12px;

        border-radius: 14px;

    }

    .region-title {

        font-size: 18px;

    }

}

</style>

</head>


<body>


<div class="container">


<!-- =======================================================
     TOP HEADER
     ======================================================= -->

<div class="top-header">

    <div class="brand">

        <div class="brand-text">

            <div class="brand-title">
                Daily Provisioning Regional
            </div>

        </div>

    </div>

    <div class="nav-bar">
    </div>

</div>


<!-- =======================================================
     DATE FILTER
     ======================================================= -->

<div class="toolbar">

    <div class="filter-box">

        <button
            id="dateFilterBtn"
            class="filter-button"
            onclick="toggleDateFilter(event)"
        >
            Date (All) ▼
        </button>


        <div
            id="dateFilterMenu"
            class="filter-menu"
        >


            <!-- =================================================
                 DATE SEARCH
                 ================================================= -->

            <div class="date-search-wrapper">

                <div class="date-search-box">

                    <span class="date-search-icon">
                        🔍
                    </span>

                    <input
                        id="dateSearchInput"
                        class="date-search-input"
                        type="text"
                        placeholder="Search date..."
                        oninput="filterDateList()"
                    >

                    <button
                        id="clearSearchBtn"
                        class="clear-search"
                        onclick="clearDateSearch()"
                        type="button"
                    >
                        ✕
                    </button>

                </div>

                <div class="search-info">

                    <span id="searchResultInfo">
                        All dates
                    </span>

                    <span id="selectedDateInfo">
                        0 selected
                    </span>

                </div>

            </div>


            <!-- =================================================
                 SELECT ALL
                 ================================================= -->

            <label
                class="filter-item select-all"
            >

                <input
                    type="checkbox"
                    id="selectAllDates"
                    onchange="toggleAllDates(this.checked)"
                >

                <span>
                    Select All
                </span>

            </label>


            <!-- =================================================
                 DATE OPTIONS
                 ================================================= -->

            <div
                id="dateOptions"
                class="date-options"
            >
            </div>


            <!-- =================================================
                 ACTIONS
                 ================================================= -->

            <div class="filter-actions">

                <button
                    class="apply-button"
                    onclick="applyDateFilter()"
                    type="button"
                >
                    Apply
                </button>

                <button
                    class="cancel-button"
                    onclick="cancelDateFilter()"
                    type="button"
                >
                    Cancel
                </button>

            </div>

        </div>

    </div>

</div>


<div id="dashboard"></div>


</div>


<script>


// ============================================================
// DATA
// ============================================================

const DATA =
    __DATA_PLACEHOLDER__;


// ============================================================
// DEFAULT HC
// ============================================================

const DEFAULT_HC = {

    cleaning: 1.5,

    terminal: 2,

    default: 1.5,

    qc: 0,

    rma: 0

};


// ============================================================
// HC LOCAL STORAGE
// ============================================================

const HC_STORAGE_KEY =
    "daily_provisioning_hc_v2";


function loadHC() {

    try {

        const saved =
            localStorage.getItem(
                HC_STORAGE_KEY
            );

        if (saved) {

            return JSON.parse(
                saved
            );

        }

    } catch (e) {

        console.log(e);

    }

    return {};

}


let HC_DATA = loadHC();


function saveHC() {

    localStorage.setItem(
        HC_STORAGE_KEY,
        JSON.stringify(HC_DATA)
    );

}


// ============================================================
// HC
// ============================================================

function getHC(
    date,
    region,
    category
) {

    const key =
        date +
        "|" +
        region +
        "|" +
        category;


    if (
        HC_DATA[key] !== undefined
    ) {

        return HC_DATA[key];

    }


    return (
        DEFAULT_HC[category] || 0
    );

}


function setHC(
    date,
    region,
    category,
    value
) {

    let hc =
        parseFloat(value);


    if (!Number.isFinite(hc)) {

        hc = 0;

    }


    const key =
        date +
        "|" +
        region +
        "|" +
        category;


    HC_DATA[key] = hc;

    saveHC();

    render();

}


// ============================================================
// NUMBER FORMAT
// ============================================================

function fmt(value) {

    const n =
        Number(value) || 0;

    return Math.round(n)
        .toLocaleString("en-US");

}


function fmtHC(value) {

    const n =
        Number(value);

    if (!Number.isFinite(n)) {

        return "0";

    }

    return String(n);

}


// ============================================================
// MAC COUNT
// ============================================================

function macCount(rows) {

    return rows.filter(
        r => {

            return (
                r.MAC !== null &&
                r.MAC !== undefined &&
                String(r.MAC).trim() !== ""
            );

        }
    ).length;

}


// ============================================================
// CALCULATION
// ============================================================

function calculate(
    region,
    rows
) {

    const jd =
        rows.map(
            r => ({

                ...r,

                jd:
                    String(
                        r["Daily (JD)"] ?? ""
                    )
                    .trim()
                    .toLowerCase()

            })
        );


    // ========================================================
    // ENUO
    // ========================================================

    if (region === "ENUO") {

        const cleaning =
            jd
            .filter(
                r =>
                    r.jd === "cleaning"
            )
            .reduce(
                (sum, r) =>
                    sum +
                    Number(r.Qty || 0),
                0
            );


        const terminal =
            macCount(
                jd.filter(
                    r =>
                        r.jd === "run"
                )
            );


        const defaultValue =
            macCount(
                jd.filter(
                    r =>
                        r.jd === "default"
                )
            );


        const total =
            cleaning +
            terminal +
            defaultValue;


        return {

            cleaning,
            terminal,
            defaultValue,
            total

        };

    }


    // ========================================================
    // HGAO
    // ========================================================

    if (region === "HGAO") {

        const cleaning =
            jd
            .filter(
                r =>
                    r.jd === "cleaning"
            )
            .reduce(
                (sum, r) =>
                    sum +
                    Number(r.Qty || 0),
                0
            );


        const terminal =
            macCount(
                jd.filter(
                    r =>
                        r.jd === "run"
                )
            );


        const defaultValue =
            macCount(
                jd.filter(
                    r =>
                        r.jd === "default"
                )
            );


        const qc =
            jd
            .filter(
                r =>
                    r.jd === "speed test" ||
                    r.jd === "lanport test"
            )
            .reduce(
                (sum, r) =>
                    sum +
                    Number(r.Qty || 0),
                0
            );


        const total =
            cleaning +
            terminal +
            defaultValue +
            qc;


        return {

            cleaning,
            terminal,
            defaultValue,
            qc,
            total

        };

    }


    // ========================================================
    // PI44 / MDY
    // ========================================================

    if (region === "MDY") {

        const cleaning =
            jd
            .filter(
                r =>
                    r.jd === "cleaning"
            )
            .reduce(
                (sum, r) =>
                    sum +
                    Number(r.Qty || 0),
                0
            );


        const terminal =
            macCount(
                jd.filter(
                    r =>
                        r.jd === "run"
                )
            );


        const defaultValue =
            macCount(
                jd.filter(
                    r =>
                        r.jd === "mac/dbm"
                )
            );


        const qc =
            jd
            .filter(
                r => {

                    const type =
                        String(
                            r.jd || ""
                        )
                        .trim()
                        .toLowerCase()
                        .replace(
                            /\s+/g,
                            " "
                        );

                    return (
                        type === "speed test" ||
                        type === "lan port test"
                    );

                }
            )
            .reduce(
                (sum, r) => {

                    return (
                        sum +
                        (Number(r.Qty) || 0)
                    );

                },
                0
            );


        const rma =
            jd
            .filter(
                r =>
                    r.jd === "test rma"
            )
            .reduce(
                (sum, r) =>
                    sum +
                    Number(r.Qty || 0),
                0
            );


        const total =
            cleaning +
            terminal +
            defaultValue +
            qc +
            rma;


        return {

            cleaning,
            terminal,
            defaultValue,
            qc,
            rma,
            total

        };

    }


    return null;

}


// ============================================================
// CATEGORY CELL
// ============================================================

function categoryCell(
    date,
    region,
    category,
    total
) {

    const hc =
        getHC(
            date,
            region,
            category
        );


    let kpi = 0;


    if (
        Number(hc) !== 0
    ) {

        kpi =
            Number(total) /
            Number(hc);

    }


    return `

        <td class="total-cell">
            ${fmt(total)}
        </td>

        <td>

            <input
                class="hc-input"
                type="number"
                step="0.1"
                min="0"
                value="${fmtHC(hc)}"

                onchange="
                    setHC(
                        '${date}',
                        '${region}',
                        '${category}',
                        this.value
                    )
                "
            >

        </td>

        <td class="kpi-cell">
            ${fmt(kpi)}
        </td>

    `;

}


// ============================================================
// HEADER GROUP
// ============================================================

function headerGroup(
    name
) {

    return `

        <th colspan="3">
            ${name}
        </th>

    `;

}


function subHeaders() {

    return `

        <th>Total</th>
        <th>HC</th>
        <th>KPI</th>

    `;

}


// ============================================================
// REGION TABLE
// ============================================================

function renderRegion(
    region,
    displayName,
    dates
) {

    let html = `

        <div class="region-card">

            <div class="region-title">
                ${displayName}
            </div>

            <div class="table-wrap">

            <table>

                <thead>

                    <tr>

                        <th rowspan="2">
                            Date
                        </th>

    `;


    html +=
        headerGroup(
            "Cleaning"
        );


    html +=
        headerGroup(
            "Terminal"
        );


    html +=
        headerGroup(
            "Default"
        );


    if (
        region === "HGAO" ||
        region === "MDY"
    ) {

        html +=
            headerGroup(
                "QC"
            );

    }


    if (
        region === "MDY"
    ) {

        html +=
            headerGroup(
                "RMA"
            );

    }


    html +=
        headerGroup(
            "Total Count"
        );


    html += `

                    </tr>

                    <tr>

                        ${subHeaders()}

                        ${subHeaders()}

                        ${subHeaders()}

    `;


    if (
        region === "HGAO" ||
        region === "MDY"
    ) {

        html +=
            subHeaders();

    }


    if (
        region === "MDY"
    ) {

        html +=
            subHeaders();

    }


    html +=
        subHeaders();


    html += `

                    </tr>

                </thead>

                <tbody>

    `;


    // ========================================================
    // EACH DATE
    // ========================================================

    dates.forEach(
        date => {

            const rows =
                DATA.filter(
                    r =>
                        r.Region === region &&
                        r.Date === date
                );


            const result =
                calculate(
                    region,
                    rows
                );


            if (!result) {

                return;

            }


            html += `

                <tr>

                    <td class="date-cell">
                        ${date}
                    </td>

            `;


            html +=
                categoryCell(
                    date,
                    region,
                    "cleaning",
                    result.cleaning
                );


            html +=
                categoryCell(
                    date,
                    region,
                    "terminal",
                    result.terminal
                );


            html +=
                categoryCell(
                    date,
                    region,
                    "default",
                    result.defaultValue
                );


            if (
                region === "HGAO" ||
                region === "MDY"
            ) {

                html +=
                    categoryCell(
                        date,
                        region,
                        "qc",
                        result.qc
                    );

            }


            if (
                region === "MDY"
            ) {

                html +=
                    categoryCell(
                        date,
                        region,
                        "rma",
                        result.rma
                    );

            }


            // =================================================
            // TOTAL HC
            // =================================================

            let totalHC = 0;


            totalHC +=
                Number(
                    getHC(
                        date,
                        region,
                        "cleaning"
                    )
                );


            totalHC +=
                Number(
                    getHC(
                        date,
                        region,
                        "terminal"
                    )
                );


            totalHC +=
                Number(
                    getHC(
                        date,
                        region,
                        "default"
                    )
                );


            if (
                region === "HGAO" ||
                region === "MDY"
            ) {

                totalHC +=
                    Number(
                        getHC(
                            date,
                            region,
                            "qc"
                        )
                    );

            }


            if (
                region === "MDY"
            ) {

                totalHC +=
                    Number(
                        getHC(
                            date,
                            region,
                            "rma"
                        )
                    );

            }


            let totalKPI = 0;


            if (
                totalHC !== 0
            ) {

                totalKPI =
                    Number(result.total) /
                    totalHC;

            }


            html += `

                    <td class="total-cell">
                        ${fmt(result.total)}
                    </td>

                    <td>

                        <input
                            class="hc-input"
                            type="number"
                            value="${fmtHC(totalHC)}"
                            disabled
                        >

                    </td>

                    <td class="kpi-cell">
                        ${fmt(totalKPI)}
                    </td>

                </tr>

            `;

        }
    );


    html += `

                </tbody>

            </table>

            </div>

            <div class="note">

                KPI = Total ÷ HC

            </div>

        </div>

    `;


    return html;

}


// ============================================================
// DATE FILTER STATE
// ============================================================

let appliedDates = null;

let tempDates = null;


// ============================================================
// ALL AVAILABLE DATES
// ============================================================

function getAllDates() {

    const dates = [
        ...new Set(
            DATA
                .map(
                    r => r.Date
                )
                .filter(Boolean)
        )
    ];

    dates.sort();

    return dates;

}


// ============================================================
// DATE SEARCH
// ============================================================

function filterDateList() {

    const input =
        document.getElementById(
            "dateSearchInput"
        );

    const searchText =
        String(
            input?.value || ""
        )
        .trim()
        .toLowerCase();


    const clearBtn =
        document.getElementById(
            "clearSearchBtn"
        );


    if (clearBtn) {

        clearBtn.style.display =
            searchText
                ? "block"
                : "none";

    }


    buildDateList(
        searchText
    );

}


// ============================================================
// CLEAR DATE SEARCH
// ============================================================

function clearDateSearch() {

    const input =
        document.getElementById(
            "dateSearchInput"
        );


    if (input) {

        input.value = "";

    }


    const clearBtn =
        document.getElementById(
            "clearSearchBtn"
        );


    if (clearBtn) {

        clearBtn.style.display =
            "none";

    }


    buildDateList("");

    if (input) {

        input.focus();

    }

}


// ============================================================
// BUILD DATE LIST
// ============================================================

function buildDateList(
    searchText = ""
) {

    const container =
        document.getElementById(
            "dateOptions"
        );


    if (!container) {

        return;

    }


    const allDates =
        getAllDates();


    const search =
        String(
            searchText || ""
        )
        .trim()
        .toLowerCase();


    const filteredDates =
        allDates.filter(
            date => {

                if (!search) {

                    return true;

                }

                const raw =
                    String(date)
                    .toLowerCase();

                const display =
                    new Date(
                        date + "T00:00:00"
                    )
                    .toLocaleDateString(
                        "en-GB"
                    )
                    .toLowerCase();

                return (
                    raw.includes(search) ||
                    display.includes(search)
                );

            }
        );


    container.innerHTML = "";


    if (
        filteredDates.length === 0
    ) {

        container.innerHTML = `

            <div class="no-date-result">
                No matching date found
            </div>

        `;

    }


    filteredDates.forEach(
        date => {

            const label =
                document.createElement(
                    "label"
                );


            label.className =
                "filter-item";


            const checkbox =
                document.createElement(
                    "input"
                );


            checkbox.type =
                "checkbox";


            checkbox.className =
                "date-checkbox";


            checkbox.value =
                date;


            checkbox.checked =
                tempDates
                    ? tempDates.includes(date)
                    : true;


            label.appendChild(
                checkbox
            );


            const span =
                document.createElement(
                    "span"
                );


            span.textContent =
                date;


            label.appendChild(
                span
            );


            container.appendChild(
                label
            );

        }
    );


    const resultInfo =
        document.getElementById(
            "searchResultInfo"
        );


    if (resultInfo) {

        if (search) {

            resultInfo.textContent =
                filteredDates.length +
                " / " +
                allDates.length +
                " dates";

        } else {

            resultInfo.textContent =
                "All " +
                allDates.length +
                " dates";

        }

    }


    updateSelectedCount();

    updateSelectAll();

}


// ============================================================
// SELECTED COUNT
// ============================================================

function updateSelectedCount() {

    const info =
        document.getElementById(
            "selectedDateInfo"
        );


    if (!info) {

        return;

    }


    const selected =
        tempDates || [];


    info.textContent =
        selected.length +
        " selected";

}


// ============================================================
// SETUP DATE FILTER
// ============================================================

function setupDates() {

    const dates =
        getAllDates();


    appliedDates =
        [...dates];


    tempDates =
        [...dates];


    buildDateList("");

    updateSelectAll();

    updateDateButton();

}


// ============================================================
// OPEN / CLOSE FILTER
// ============================================================

function toggleDateFilter(
    event
) {

    if (event) {

        event.stopPropagation();

    }


    const menu =
        document.getElementById(
            "dateFilterMenu"
        );


    if (
        menu.classList.contains(
            "show"
        )
    ) {

        menu.classList.remove(
            "show"
        );

        return;

    }


    const applied =
        appliedDates || [];


    tempDates =
        [...applied];


    const input =
        document.getElementById(
            "dateSearchInput"
        );


    if (input) {

        input.value = "";

    }


    buildDateList("");

    updateSelectAll();

    updateSelectedCount();


    menu.classList.add(
        "show"
    );

}


// ============================================================
// SELECT ALL
// ============================================================

function toggleAllDates(
    checked
) {

    const visibleBoxes =
        [
            ...document.querySelectorAll(
                ".date-checkbox"
            )
        ];


    const visibleDates =
        visibleBoxes.map(
            box =>
                box.value
        );


    if (!tempDates) {

        tempDates = [];

    }


    if (checked) {

        visibleDates.forEach(
            date => {

                if (
                    !tempDates.includes(
                        date
                    )
                ) {

                    tempDates.push(
                        date
                    );

                }

            }
        );

    } else {

        tempDates =
            tempDates.filter(
                date =>
                    !visibleDates.includes(
                        date
                    )
            );

    }


    buildDateList(
        document.getElementById(
            "dateSearchInput"
        )?.value || ""
    );


    updateDateButton();

}


// ============================================================
// GET CHECKED DATES
// ============================================================

function getCheckedDates() {

    return [
        ...document.querySelectorAll(
            ".date-checkbox"
        )
    ]
    .filter(
        box =>
            box.checked
    )
    .map(
        box =>
            box.value
    );

}


// ============================================================
// UPDATE TEMP DATES
// ============================================================

function syncVisibleCheckboxes() {

    const boxes =
        [
            ...document.querySelectorAll(
                ".date-checkbox"
            )
        ];


    boxes.forEach(
        box => {

            if (
                box.checked &&
                !tempDates.includes(
                    box.value
                )
            ) {

                tempDates.push(
                    box.value
                );

            }

            if (
                !box.checked
            ) {

                tempDates =
                    tempDates.filter(
                        date =>
                            date !==
                            box.value
                    );

            }

        }
    );

}


// ============================================================
// SELECT ALL STATE
// ============================================================

function updateSelectAll() {

    const boxes =
        [
            ...document.querySelectorAll(
                ".date-checkbox"
            )
        ];


    const selectAll =
        document.getElementById(
            "selectAllDates"
        );


    if (!selectAll) {

        return;

    }


    const allDates =
        getAllDates();


    const selected =
        tempDates || [];


    const searchInput =
        document.getElementById(
            "dateSearchInput"
        );


    const search =
        String(
            searchInput?.value || ""
        )
        .trim()
        .toLowerCase();


    let visibleDates =
        allDates;


    if (search) {

        visibleDates =
            allDates.filter(
                date => {

                    const raw =
                        String(date)
                        .toLowerCase();

                    const display =
                        new Date(
                            date + "T00:00:00"
                        )
                        .toLocaleDateString(
                            "en-GB"
                        )
                        .toLowerCase();

                    return (
                        raw.includes(search) ||
                        display.includes(search)
                    );

                }
            );

    }


    const visibleSelected =
        visibleDates.filter(
            date =>
                selected.includes(
                    date
                )
        );


    selectAll.checked =
        visibleDates.length > 0 &&
        visibleSelected.length ===
        visibleDates.length;


    selectAll.indeterminate =
        visibleSelected.length > 0 &&
        visibleSelected.length <
        visibleDates.length;


    updateSelectedCount();

}


// ============================================================
// BUTTON TEXT
// ============================================================

function updateDateButton() {

    const allDates =
        getAllDates();


    const selected =
        tempDates || [];


    const button =
        document.getElementById(
            "dateFilterBtn"
        );


    if (!button) {

        return;

    }


    if (
        selected.length === 0
    ) {

        button.textContent =
            "Date (None) ▼";

    }

    else if (
        selected.length ===
        allDates.length
    ) {

        button.textContent =
            "Date (All) ▼";

    }

    else {

        button.textContent =
            "Date (" +
            selected.length +
            " selected) ▼";

    }

}


// ============================================================
// APPLY
// ============================================================

function applyDateFilter() {

    syncVisibleCheckboxes();


    appliedDates =
        [...tempDates];


    updateDateButton();


    const menu =
        document.getElementById(
            "dateFilterMenu"
        );


    menu.classList.remove(
        "show"
    );


    render();

}


// ============================================================
// CANCEL
// ============================================================

function cancelDateFilter() {

    const applied =
        appliedDates || [];


    tempDates =
        [...applied];


    const input =
        document.getElementById(
            "dateSearchInput"
        );


    if (input) {

        input.value = "";

    }


    buildDateList("");

    updateSelectAll();

    updateDateButton();


    const menu =
        document.getElementById(
            "dateFilterMenu"
        );


    menu.classList.remove(
        "show"
    );

}


// ============================================================
// CLOSE WHEN CLICK OUTSIDE
// ============================================================

document.addEventListener(
    "click",
    function(event) {

        const filter =
            document.querySelector(
                ".filter-box"
            );


        const menu =
            document.getElementById(
                "dateFilterMenu"
            );


        if (
            filter &&
            !filter.contains(event.target) &&
            menu &&
            menu.classList.contains("show")
        ) {

            cancelDateFilter();

        }

    }
);


// ============================================================
// DATE CHECKBOX CHANGE
// ============================================================

document.addEventListener(
    "change",
    function(event) {

        if (
            event.target.classList &&
            event.target.classList.contains(
                "date-checkbox"
            )
        ) {

            if (!tempDates) {

                tempDates = [];

            }


            if (
                event.target.checked
            ) {

                if (
                    !tempDates.includes(
                        event.target.value
                    )
                ) {

                    tempDates.push(
                        event.target.value
                    );

                }

            } else {

                tempDates =
                    tempDates.filter(
                        date =>
                            date !==
                            event.target.value
                    );

            }


            updateSelectAll();

            updateDateButton();

        }

    }
);


// ============================================================
// RENDER
// ============================================================

function render() {

    const allDates =
        getAllDates();


    let dates =
        appliedDates === null
            ? [...allDates]
            : [...appliedDates];


    dates =
        dates.filter(
            d =>
                allDates.includes(d)
        );


    let html = "";


    // ========================================================
    // ENUO
    // ========================================================

    html +=
        renderRegion(
            "ENUO",
            "ENUO",
            dates
        );


    // ========================================================
    // HGAO
    // ========================================================

    html +=
        renderRegion(
            "HGAO",
            "HGAO",
            dates
        );


    // ========================================================
    // PI44
    // ========================================================

    html +=
        renderRegion(
            "MDY",
            "PI44",
            dates
        );


    document.getElementById(
        "dashboard"
    ).innerHTML =
        html;

}


// ============================================================
// START
// ============================================================

setupDates();

render();


</script>


</body>

</html>
"""


# ============================================================
# INSERT DATA
# ============================================================

html = html.replace(
    "__DATA_PLACEHOLDER__",
    data_json
)


# ============================================================
# DATA STATUS
# ============================================================


# ============================================================
# SHOW DASHBOARD
# ============================================================

components.html(
    html,
    height=1900,
    scrolling=True
)