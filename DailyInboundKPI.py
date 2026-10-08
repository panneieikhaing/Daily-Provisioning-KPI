import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
import json
from io import StringIO


# =========================================================
# PAGE CONFIG
# =========================================================

def show_regionalkpi():

    import streamlit as st
    import streamlit.components.v1 as components
    import pandas as pd
    import requests
    import json
    from io import StringIO


# =========================================================
# GOOGLE SHEET
# =========================================================

SHEET_ID = "1PK1Bz7gRg8x3L8IOr7Xx8ntMADaznWWhYyEjchzuM6M"


def load_google_sheet(sheet_id):

    url = (
        f"https://docs.google.com/spreadsheets/d/"
        f"{sheet_id}/gviz/tq?tqx=out:csv"
    )

    response = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
        timeout=30
    )

    response.raise_for_status()

    return pd.read_csv(
        StringIO(response.text)
    )


# =========================================================
# LOAD DATA
# =========================================================

try:

    df = load_google_sheet(
        SHEET_ID
    )

except Exception as e:

    st.error(
        f"Google Sheet Error: {e}"
    )

    st.stop()


# =========================================================
# CLEAN COLUMN NAMES
# =========================================================

df.columns = [
    str(col).strip()
    for col in df.columns
]


# =========================================================
# FIND COLUMNS
# =========================================================

column_map = {}

for col in df.columns:

    name = (
        str(col)
        .strip()
        .lower()
    )

    if name in [
        "date",
        "regional date",
        "day"
    ]:

        column_map["Date"] = col

    elif name in [
        "region",
        "regional"
    ]:

        column_map["Region"] = col

    elif name in [
        "cpe type",
        "cpe_type",
        "cpetype",
        "type"
    ]:

        column_map["CPE Type"] = col

    elif name in [
        "mac",
        "mac address",
        "mac_address",
        "macaddress"
    ]:

        column_map["MAC"] = col


# =========================================================
# REQUIRED COLUMNS
# =========================================================

required = [
    "Date",
    "Region",
    "CPE Type",
    "MAC"
]

missing = [
    x
    for x in required
    if x not in column_map
]

if missing:

    st.error(
        "Required column မတွေ့ပါ: "
        + ", ".join(missing)
    )

    st.write(
        "Google Sheet Columns:"
    )

    st.write(
        list(df.columns)
    )

    st.stop()


# =========================================================
# RENAME
# =========================================================

df = df.rename(
    columns={
        column_map["Date"]: "Date",
        column_map["Region"]: "Region",
        column_map["CPE Type"]: "CPE Type",
        column_map["MAC"]: "MAC"
    }
)


# =========================================================
# CLEAN DATA
# =========================================================

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

df["CPE Type"] = (
    df["CPE Type"]
    .astype(str)
    .str.strip()
    .str.upper()
)

df["MAC"] = (
    df["MAC"]
    .astype(str)
    .str.strip()
    .str.upper()
)

df = df.dropna(
    subset=["Date"]
)


# =========================================================
# REGIONS
# =========================================================

regions = [
    "ENUO",
    "HGAO",
    "MYFO"
]

df = df[
    df["Region"].isin(regions)
]


# =========================================================
# REMOVE EMPTY MAC
# =========================================================

df = df[
    (df["MAC"] != "")
    &
    (df["MAC"] != "NAN")
]


# =========================================================
# CPE TYPES
# =========================================================

cpe_types = sorted(
    [
        x
        for x in
        df["CPE Type"]
        .dropna()
        .unique()
        if str(x).strip() != ""
        and str(x).strip() != "NAN"
    ]
)


# =========================================================
# JSON DATA
# =========================================================

data_json = []

for _, row in df.iterrows():

    data_json.append({

        "Date":
            row["Date"].strftime(
                "%Y-%m-%d"
            ),

        "Region":
            str(row["Region"]),

        "CPE":
            str(row["CPE Type"]),

        "MAC":
            str(row["MAC"])

    })


json_data = json.dumps(
    data_json,
    ensure_ascii=False
)

cpe_json = json.dumps(
    cpe_types,
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

<style>

* {
    box-sizing: border-box;
}

body {

    margin: 0;

    padding: 25px;

    font-family:
        Arial,
        "Segoe UI",
        sans-serif;

    background:
        linear-gradient(
            135deg,
            #eef3f9,
            #f8fafc
        );

    color: #1e293b;
}


/* =====================================================
   NAVIGATION
   ===================================================== */

.nav-bar {

    display: flex;

    justify-content: center;

    gap: 10px;

    margin-bottom: 18px;
}

.nav-btn {

    display: inline-block;

    padding: 9px 20px;

    border-radius: 10px;

    background:
        rgba(
            255,
            255,
            255,
            0.15
        );

    color: white;

    text-decoration: none;

    font-size: 13px;

    font-weight: 700;

    border:
        1px solid
        rgba(
            255,
            255,
            255,
            0.25
        );
}

.nav-btn:hover {

    background:
        rgba(
            255,
            255,
            255,
            0.28
        );
}

.nav-btn.active {

    background: white;

    color: #1d4ed8;
}


/* =====================================================
   HEADER
   ===================================================== */

.header {

    background:
        linear-gradient(
            135deg,
            #172554,
            #2563eb
        );

    color: white;

    padding: 28px;

    border-radius: 20px;

    text-align: center;

    margin-bottom: 24px;

    box-shadow:
        0 10px 30px
        rgba(
            15,
            23,
            42,
            0.16
        );
}

.title {

    font-size: 30px;

    font-weight: 800;

    letter-spacing: 0.4px;
}

.subtitle {

    margin-top: 8px;

    font-size: 13px;

    opacity: 0.85;
}


/* =====================================================
   FILTER CARD
   ===================================================== */

.filter-card {

    background: white;

    padding: 16px 20px;

    border-radius: 15px;

    margin-bottom: 22px;

    box-shadow:
        0 5px 18px
        rgba(
            15,
            23,
            42,
            0.07
        );

    display: flex;

    align-items: center;

    gap: 12px;

    flex-wrap: wrap;
}

.filter-label {

    font-weight: 700;

    color: #334155;
}


/* =====================================================
   DATE FILTER
   ===================================================== */

.date-filter {

    position: relative;

    display: inline-block;
}

.date-filter-button {

    min-width: 230px;

    padding: 10px 14px;

    background: white;

    border:
        1px solid
        #cbd5e1;

    border-radius: 9px;

    cursor: pointer;

    display: flex;

    align-items: center;

    justify-content: space-between;

    gap: 12px;

    font-size: 13px;

    color: #334155;
}

.date-filter-button:hover {

    border-color: #2563eb;

    box-shadow:
        0 0 0 2px
        rgba(
            37,
            99,
            235,
            0.08
        );
}

.arrow {

    font-size: 11px;

    color: #64748b;
}


/* =====================================================
   DATE DROPDOWN
   ===================================================== */

.date-menu {

    display: none;

    position: absolute;

    top: calc(100% + 6px);

    left: 0;

    width: 320px;

    background: white;

    border:
        1px solid
        #cbd5e1;

    border-radius: 12px;

    box-shadow:
        0 12px 30px
        rgba(
            15,
            23,
            42,
            0.18
        );

    z-index: 9999;

    padding: 10px;
}

.date-menu.show {

    display: block;
}


/* =====================================================
   DATE SEARCH
   ===================================================== */

.date-search-wrapper {

    position: relative;

    margin-bottom: 8px;
}

.date-search {

    width: 100%;

    padding: 10px 36px 10px 12px;

    border:
        1px solid
        #cbd5e1;

    border-radius: 8px;

    outline: none;

    font-size: 13px;

    color: #334155;

    background: #f8fafc;
}

.date-search::placeholder {

    color: #94a3b8;
}

.date-search:focus {

    border-color: #2563eb;

    background: white;

    box-shadow:
        0 0 0 2px
        rgba(
            37,
            99,
            235,
            0.08
        );
}

.clear-search {

    position: absolute;

    right: 8px;

    top: 50%;

    transform:
        translateY(-50%);

    border: none;

    background: transparent;

    color: #64748b;

    cursor: pointer;

    font-size: 14px;

    display: none;
}

.clear-search:hover {

    color: #1e293b;
}


/* =====================================================
   SEARCH INFO
   ===================================================== */

.search-info {

    font-size: 11px;

    color: #64748b;

    padding:
        3px
        7px
        7px;

    display: flex;

    justify-content: space-between;
}


/* =====================================================
   SELECT ALL
   ===================================================== */

.select-all-row {

    padding: 8px 7px;

    border-bottom:
        1px solid
        #e2e8f0;

    margin-bottom: 5px;
}

.select-all-row label {

    display: flex;

    align-items: center;

    gap: 9px;

    cursor: pointer;

    font-weight: 700;

    font-size: 13px;
}


/* =====================================================
   DATE LIST
   ===================================================== */

.date-list {

    max-height: 300px;

    overflow-y: auto;

    padding-right: 3px;
}

.date-row {

    display: flex;

    align-items: center;

    gap: 9px;

    padding: 7px;

    border-radius: 7px;

    cursor: pointer;

    font-size: 13px;
}

.date-row:hover {

    background: #f1f5f9;
}

.date-row input,
.select-all-row input {

    width: 16px;

    height: 16px;

    accent-color: #2563eb;

    cursor: pointer;

    flex-shrink: 0;
}

.no-date-result {

    padding: 18px 8px;

    text-align: center;

    color: #94a3b8;

    font-size: 12px;
}


/* =====================================================
   FILTER FOOTER
   ===================================================== */

.filter-footer {

    display: flex;

    justify-content: flex-end;

    gap: 8px;

    padding-top: 10px;

    margin-top: 7px;

    border-top:
        1px solid
        #e2e8f0;
}

.apply-btn,
.cancel-btn {

    padding: 8px 17px;

    border-radius: 8px;

    font-size: 12px;

    font-weight: 700;

    cursor: pointer;
}

.apply-btn {

    background: #2563eb;

    color: white;

    border: none;
}

.apply-btn:hover {

    background: #1d4ed8;
}

.cancel-btn {

    background: #f1f5f9;

    color: #334155;

    border:
        1px solid
        #cbd5e1;
}

.cancel-btn:hover {

    background: #e2e8f0;
}


/* =====================================================
   REGION CARD
   ===================================================== */

.region-card {

    background: white;

    border-radius: 18px;

    overflow: hidden;

    margin-bottom: 28px;

    border:
        1px solid
        #e2e8f0;

    box-shadow:
        0 8px 25px
        rgba(
            15,
            23,
            42,
            0.09
        );
}

.region-header {

    padding: 17px 22px;

    background:
        linear-gradient(
            90deg,
            #eff6ff,
            #ffffff
        );

    display: flex;

    align-items: center;

    justify-content: space-between;

    border-bottom:
        1px solid
        #e2e8f0;
}

.region-name {

    font-size: 21px;

    font-weight: 800;

    color: #1e3a8a;
}

.badge {

    background: #dbeafe;

    color: #1d4ed8;

    padding: 6px 13px;

    border-radius: 20px;

    font-size: 11px;

    font-weight: 800;
}


/* =====================================================
   TABLE
   ===================================================== */

.table-wrap {

    overflow-x: auto;
}

table {

    width: 100%;

    border-collapse: collapse;

    min-width: 900px;
}

thead th {

    background: #172554;

    color: white;

    padding: 12px 10px;

    font-size: 12px;

    white-space: nowrap;
}

tbody td {

    padding: 11px 9px;

    text-align: center;

    border-bottom:
        1px solid
        #e5e7eb;

    font-size: 13px;
}

tbody tr:hover {

    background: #f8fafc;
}

.date {

    font-weight: 700;

    white-space: nowrap;
}


/* =====================================================
   TOTAL
   ===================================================== */

.total {

    font-weight: 800;

    background: #f8fafc;
}


/* =====================================================
   HC INPUT
   ===================================================== */

.hc-input {

    width: 75px;

    padding: 7px;

    text-align: center;

    border:
        1px solid
        #cbd5e1;

    border-radius: 8px;

    font-weight: 700;

    outline: none;
}

.hc-input:focus {

    border-color: #2563eb;

    box-shadow:
        0 0 0 2px
        rgba(
            37,
            99,
            235,
            0.12
        );
}


/* =====================================================
   KPI
   ===================================================== */

.kpi {

    font-weight: 800;

    font-size: 14px;
}


/* =====================================================
   MEET KPI
   ===================================================== */

.meet {

    display: inline-block;

    padding: 6px 14px;

    border-radius: 20px;

    font-size: 11px;

    font-weight: 900;

    min-width: 58px;
}

.yes {

    color: #166534;

    background: #dcfce7;

    border:
        1px solid
        #86efac;
}

.no {

    color: #991b1b;

    background: #fee2e2;

    border:
        1px solid
        #fca5a5;
}


/* =====================================================
   REGION TOTAL
   ===================================================== */

.region-total {

    background:
        linear-gradient(
            90deg,
            #f1f5f9,
            #e2e8f0
        );

    font-weight: 800;
}

.region-total td {

    padding: 14px 10px;

    font-weight: 800;
}


/* =====================================================
   NO DATA
   ===================================================== */

.no-data {

    background: white;

    padding: 30px;

    border-radius: 15px;

    text-align: center;

    color: #64748b;

    font-weight: 700;
}

</style>

</head>


<body>


<!-- =====================================================
     HEADER
     ===================================================== -->

<div class="header">

    <div class="nav-bar">

    </div>

    <div class="title">
        Daily Inbound KPI
    </div>

    <div class="subtitle"></div>

</div>


<!-- =====================================================
     DATE FILTER
     ===================================================== -->

<div class="filter-card">

    <span class="filter-label">
        Date:
    </span>


    <div class="date-filter">

        <button
            id="dateFilterButton"
            class="date-filter-button"
            onclick="toggleDateMenu()"
        >

            <span id="dateFilterText">
                All Dates
            </span>

            <span class="arrow">
                ▼
            </span>

        </button>


        <div
            id="dateMenu"
            class="date-menu"
        >


            <!-- =================================================
                 SEARCH
                 ================================================= -->

            <div class="date-search-wrapper">

                <input
                    id="dateSearch"
                    class="date-search"
                    type="text"
                    placeholder="🔍 Search date..."
                    autocomplete="off"
                    oninput="filterDateList()"
                >

                <button
                    id="clearSearch"
                    class="clear-search"
                    onclick="clearDateSearch()"
                    type="button"
                >
                    ✕
                </button>

            </div>


            <!-- =================================================
                 SEARCH INFO
                 ================================================= -->

            <div class="search-info">

                <span id="searchResultText">
                    All dates
                </span>

                <span id="selectedCountText">
                    0 selected
                </span>

            </div>


            <!-- =================================================
                 SELECT ALL
                 ================================================= -->

            <div class="select-all-row">

                <label>

                    <input
                        type="checkbox"
                        id="selectAllDates"
                        onchange="toggleAllDates()"
                    >

                    <span>
                        Select All
                    </span>

                </label>

            </div>


            <!-- =================================================
                 DATE LIST
                 ================================================= -->

            <div
                id="dateList"
                class="date-list"
            ></div>


            <!-- =================================================
                 FOOTER
                 ================================================= -->

            <div class="filter-footer">

                <button
                    class="cancel-btn"
                    onclick="cancelDateFilter()"
                >
                    Cancel
                </button>

                <button
                    class="apply-btn"
                    onclick="applyDateFilter()"
                >
                    Apply
                </button>

            </div>

        </div>

    </div>

</div>


<!-- =====================================================
     DASHBOARD
     ===================================================== -->

<div id="dashboard"></div>


<script>


/* =====================================================
   DATA
   ===================================================== */

const DATA =
    __DATA_PLACEHOLDER__;


const CPE_TYPES =
    __CPE_PLACEHOLDER__;


/* =====================================================
   DATE FILTER STATE
   ===================================================== */

let appliedDates = [];

let tempDates = [];


/* =====================================================
   HC STORAGE
   ===================================================== */

const HC_KEY =
    "daily_regional_hc_dynamic_v1";


let HC_DATA =
    JSON.parse(
        localStorage.getItem(
            HC_KEY
        ) || "{}"
    );


function saveHC() {

    localStorage.setItem(
        HC_KEY,
        JSON.stringify(
            HC_DATA
        )
    );

}


/* =====================================================
   FORMAT NUMBER
   ===================================================== */

function fmt(value) {

    if (
        value === null ||
        value === undefined ||
        isNaN(value)
    ) {

        return "";

    }

    return Number(value).toLocaleString(
        "en-US",
        {
            maximumFractionDigits: 0
        }
    );

}


/* =====================================================
   FORMAT DATE
   ===================================================== */

function formatDate(date) {

    const d =
        new Date(
            date + "T00:00:00"
        );


    const day =
        String(
            d.getDate()
        ).padStart(
            2,
            "0"
        );


    const month =
        d.toLocaleString(
            "en-US",
            {
                month: "short"
            }
        );


    const year =
        d.getFullYear();


    return (
        day +
        "-" +
        month +
        "-" +
        year
    );

}


/* =====================================================
   GET ALL DATES
   ===================================================== */

function getAllDates() {

    return [
        ...new Set(
            DATA
                .map(
                    row =>
                        String(
                            row.Date || ""
                        ).trim()
                )
                .filter(
                    date =>
                        date !== ""
                )
        )
    ].sort();

}


/* =====================================================
   BUILD DATE LIST
   ===================================================== */

function buildDateList(
    searchText = ""
) {

    const dates =
        getAllDates();


    const list =
        document.getElementById(
            "dateList"
        );


    list.innerHTML = "";


    const search =
        String(
            searchText || ""
        )
        .toLowerCase()
        .trim();


    const filteredDates =
        dates.filter(
            date => {

                const rawDate =
                    date.toLowerCase();


                const displayDate =
                    formatDate(
                        date
                    ).toLowerCase();


                return (
                    rawDate.includes(
                        search
                    )
                    ||
                    displayDate.includes(
                        search
                    )
                );

            }
        );


    const searchResultText =
        document.getElementById(
            "searchResultText"
        );


    if (search) {

        searchResultText.textContent =
            `${filteredDates.length} of ${dates.length} dates`;

    } else {

        searchResultText.textContent =
            `${dates.length} dates`;

    }


    /* =================================================
       NO RESULT
       ================================================= */

    if (
        filteredDates.length === 0
    ) {

        list.innerHTML = `

            <div class="no-date-result">

                🔍 No matching date found

            </div>

        `;

        updateSelectAll();

        updateSelectedCount();

        return;

    }


    /* =================================================
       DATE CHECKBOXES
       ================================================= */

    filteredDates.forEach(
        date => {

            const checked =
                tempDates.includes(
                    date
                );


            const row =
                document.createElement(
                    "label"
                );


            row.className =
                "date-row";


            row.setAttribute(
                "data-date",
                date
            );


            row.innerHTML = `

                <input
                    type="checkbox"
                    class="date-checkbox"
                    value="${date}"
                    ${checked ? "checked" : ""}
                    onchange="
                        dateCheckboxChanged(
                            '${date}',
                            this.checked
                        )
                    "
                >

                <span>
                    ${formatDate(date)}
                </span>

            `;


            list.appendChild(
                row
            );

        }
    );


    updateSelectAll();

    updateSelectedCount();

}


/* =====================================================
   OPEN / CLOSE DATE MENU
   ===================================================== */

function toggleDateMenu() {

    const menu =
        document.getElementById(
            "dateMenu"
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


    tempDates =
        [...appliedDates];


    const search =
        document.getElementById(
            "dateSearch"
        );


    search.value = "";


    document.getElementById(
        "clearSearch"
    ).style.display =
        "none";


    buildDateList();


    menu.classList.add(
        "show"
    );


    setTimeout(
        function() {

            search.focus();

        },
        50
    );

}


/* =====================================================
   CLICK OUTSIDE
   ===================================================== */

document.addEventListener(
    "click",
    function(event) {

        const filter =
            document.querySelector(
                ".date-filter"
            );


        if (
            filter &&
            !filter.contains(
                event.target
            )
        ) {

            const menu =
                document.getElementById(
                    "dateMenu"
                );


            menu.classList.remove(
                "show"
            );

        }

    }
);


/* =====================================================
   DATE CHECKBOX CHANGE
   ===================================================== */

function dateCheckboxChanged(
    date,
    checked
) {

    if (
        checked
    ) {

        if (
            !tempDates.includes(
                date
            )
        ) {

            tempDates.push(
                date
            );

        }

    } else {

        tempDates =
            tempDates.filter(
                d =>
                    d !== date
            );

    }


    updateSelectAll();

    updateSelectedCount();

}


/* =====================================================
   SELECT ALL
   ===================================================== */

function toggleAllDates() {

    const selectAll =
        document.getElementById(
            "selectAllDates"
        );


    const search =
        document.getElementById(
            "dateSearch"
        )
        .value
        .toLowerCase()
        .trim();


    const allDates =
        getAllDates();


    const visibleDates =
        allDates.filter(
            date => {

                const raw =
                    date.toLowerCase();


                const formatted =
                    formatDate(
                        date
                    ).toLowerCase();


                return (
                    raw.includes(
                        search
                    )
                    ||
                    formatted.includes(
                        search
                    )
                );

            }
        );


    if (
        selectAll.checked
    ) {

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
        search
    );

}


/* =====================================================
   UPDATE SELECT ALL
   ===================================================== */

function updateSelectAll() {

    const selectAll =
        document.getElementById(
            "selectAllDates"
        );


    if (!selectAll) {

        return;

    }


    const search =
        document.getElementById(
            "dateSearch"
        )
        ?.value
        .toLowerCase()
        .trim()
        || "";


    const allDates =
        getAllDates();


    const visibleDates =
        allDates.filter(
            date => {

                const raw =
                    date.toLowerCase();


                const formatted =
                    formatDate(
                        date
                    ).toLowerCase();


                return (
                    raw.includes(
                        search
                    )
                    ||
                    formatted.includes(
                        search
                    )
                );

            }
        );


    if (
        visibleDates.length === 0
    ) {

        selectAll.checked =
            false;

        selectAll.indeterminate =
            false;

        return;

    }


    const selectedVisible =
        visibleDates.filter(
            date =>
                tempDates.includes(
                    date
                )
        ).length;


    selectAll.checked =
        selectedVisible ===
        visibleDates.length;


    selectAll.indeterminate =
        selectedVisible > 0
        &&
        selectedVisible <
        visibleDates.length;

}


/* =====================================================
   SEARCH DATE
   ===================================================== */

function filterDateList() {

    const searchInput =
        document.getElementById(
            "dateSearch"
        );


    const search =
        searchInput
        .value
        .toLowerCase()
        .trim();


    const clearButton =
        document.getElementById(
            "clearSearch"
        );


    clearButton.style.display =
        search
            ? "block"
            : "none";


    buildDateList(
        search
    );

}


/* =====================================================
   CLEAR SEARCH
   ===================================================== */

function clearDateSearch() {

    const search =
        document.getElementById(
            "dateSearch"
        );


    search.value = "";


    document.getElementById(
        "clearSearch"
    ).style.display =
        "none";


    buildDateList();


    search.focus();

}


/* =====================================================
   APPLY DATE FILTER
   ===================================================== */

function applyDateFilter() {

    appliedDates =
        [...tempDates];


    updateDateFilterText();


    const menu =
        document.getElementById(
            "dateMenu"
        );


    menu.classList.remove(
        "show"
    );


    render();

}


/* =====================================================
   CANCEL DATE FILTER
   ===================================================== */

function cancelDateFilter() {

    tempDates =
        [...appliedDates];


    const menu =
        document.getElementById(
            "dateMenu"
        );


    menu.classList.remove(
        "show"
    );

}


/* =====================================================
   DATE FILTER BUTTON TEXT
   ===================================================== */

function updateDateFilterText() {

    const text =
        document.getElementById(
            "dateFilterText"
        );


    const allDates =
        getAllDates();


    if (
        appliedDates.length === 0
        ||
        appliedDates.length ===
        allDates.length
    ) {

        text.textContent =
            "All Dates";

        return;

    }


    if (
        appliedDates.length === 1
    ) {

        text.textContent =
            formatDate(
                appliedDates[0]
            );

        return;

    }


    text.textContent =
        appliedDates.length +
        " dates selected";

}


/* =====================================================
   SELECTED COUNT
   ===================================================== */

function updateSelectedCount() {

    const el =
        document.getElementById(
            "selectedCountText"
        );


    if (!el) {

        return;

    }


    const total =
        getAllDates().length;


    const selected =
        tempDates.length;


    if (
        selected === 0
    ) {

        el.textContent =
            "0 selected";

        return;

    }


    if (
        selected === total
    ) {

        el.textContent =
            "All selected";

        return;

    }


    el.textContent =
        `${selected} selected`;

}


/* =====================================================
   UNIQUE MAC
   ===================================================== */

function uniqueMAC(rows) {

    const macSet =
        new Set();


    rows.forEach(
        row => {

            const mac =
                String(
                    row.MAC || ""
                )
                .trim()
                .toUpperCase();


            if (
                mac &&
                mac !== "NAN"
            ) {

                macSet.add(
                    mac
                );

            }

        }
    );


    return macSet.size;

}


/* =====================================================
   CPE COUNT
   ===================================================== */

function cpeCount(
    rows,
    type
) {

    const filtered =
        rows.filter(
            row =>

                String(
                    row.CPE || ""
                )
                .trim()
                .toUpperCase()
                ===
                String(type)
                    .trim()
                    .toUpperCase()

        );


    return uniqueMAC(
        filtered
    );

}


/* =====================================================
   GET HC
   ===================================================== */

function getHC(
    region,
    date
) {

    const key =
        region +
        "|" +
        date;


    return Number(
        HC_DATA[key] || 0
    );

}


/* =====================================================
   CHANGE HC
   ===================================================== */

function changeHC(
    region,
    date,
    value
) {

    const key =
        region +
        "|" +
        date;


    HC_DATA[key] =
        Number(value) || 0;


    saveHC();


    render();

}


/* =====================================================
   KPI
   ===================================================== */

function getKPI(
    total,
    hc
) {

    if (
        !hc ||
        hc <= 0
    ) {

        return 0;

    }


    return total / hc;

}


/* =====================================================
   MEET KPI
   ===================================================== */

function meet(kpi) {

    if (
        kpi >= 50
    ) {

        return `
            <span class="meet yes">
                YES
            </span>
        `;

    }


    return `
        <span class="meet no">
            NO
        </span>
    `;

}


/* =====================================================
   GET REGION DATA
   ===================================================== */

function getRegionData(
    region
) {

    let regionData =
        DATA.filter(
            row =>

                String(
                    row.Region
                )
                .trim()
                .toUpperCase()
                ===
                region
        );


    if (
        appliedDates.length > 0
    ) {

        regionData =
            regionData.filter(
                row =>
                    appliedDates.includes(
                        row.Date
                    )
            );

    }


    return regionData;

}


/* =====================================================
   RENDER REGION
   ===================================================== */

function renderRegion(
    region
) {

    const regionData =
        getRegionData(
            region
        );


    if (
        regionData.length === 0
    ) {

        return "";

    }


    const dates =
        [
            ...new Set(
                regionData.map(
                    row =>
                        row.Date
                )
            )
        ]
        .sort();


    let html = `

    <div class="region-card">

        <div class="region-header">

            <div class="region-name">

                ${region}

            </div>

            <div class="badge">

                ${CPE_TYPES.length}
                CPE TYPES

            </div>

        </div>


        <div class="table-wrap">

        <table>

            <thead>

                <tr>

                    <th>
                        Regional
                    </th>

                    <th>
                        Date
                    </th>

    `;


    /* =================================================
       CPE HEADERS
       ================================================= */

    CPE_TYPES.forEach(
        type => {

            html += `

                <th>
                    ${type}
                </th>

            `;

        }
    );


    html += `

                    <th>
                        Total
                    </th>

                    <th>
                        Daily HC
                    </th>

                    <th>
                        1 HC KPI
                    </th>

                    <th>
                        Meet KPI
                    </th>

                </tr>

            </thead>


            <tbody>

    `;


    /* =================================================
       SUM
       ================================================= */

    const sums = {};


    CPE_TYPES.forEach(
        type => {

            sums[type] = 0;

        }
    );


    let sumTotal = 0;

    let sumHC = 0;


    /* =================================================
       DATE ROWS
       ================================================= */

    dates.forEach(
        date => {

            const rows =
                regionData.filter(
                    row =>
                        row.Date === date
                );


            let total = 0;


            const counts = {};


            CPE_TYPES.forEach(
                type => {

                    const count =
                        cpeCount(
                            rows,
                            type
                        );


                    counts[type] =
                        count;


                    total += count;


                    sums[type] +=
                        count;

                }
            );


            const hc =
                getHC(
                    region,
                    date
                );


            const kpi =
                getKPI(
                    total,
                    hc
                );


            sumTotal +=
                total;


            sumHC +=
                hc;


            html += `

            <tr>

                <td class="date">

                    ${region}

                </td>


                <td class="date">

                    ${formatDate(date)}

                </td>

            `;


            /* =================================================
               CPE VALUES
               ================================================= */

            CPE_TYPES.forEach(
                type => {

                    html += `

                        <td>

                            ${fmt(
                                counts[type]
                            )}

                        </td>

                    `;

                }
            );


            html += `

                <td class="total">

                    ${fmt(total)}

                </td>


                <td>

                    <input

                        class="hc-input"

                        type="number"

                        min="0"

                        step="0.1"

                        value="${hc}"

                        onchange="
                            changeHC(
                                '${region}',
                                '${date}',
                                this.value
                            )
                        "

                    >

                </td>


                <td class="kpi">

                    ${fmt(kpi)}

                </td>


                <td>

                    ${meet(kpi)}

                </td>

            </tr>

            `;

        }
    );


    /* =================================================
       REGION TOTAL
       ================================================= */

    const totalKPI =
        getKPI(
            sumTotal,
            sumHC
        );


    html += `

        <tr class="region-total">

            <td colspan="2">

                ${region} Total

            </td>

    `;


    CPE_TYPES.forEach(
        type => {

            html += `

                <td>

                    ${fmt(
                        sums[type]
                    )}

                </td>

            `;

        }
    );


    html += `

            <td>

                ${fmt(
                    sumTotal
                )}

            </td>


            <td>

                ${fmt(
                    sumHC
                )}

            </td>


            <td>

                ${fmt(
                    totalKPI
                )}

            </td>


            <td>

                ${meet(
                    totalKPI
                )}

            </td>

        </tr>


        </tbody>

        </table>

        </div>

    </div>

    `;


    return html;

}


/* =====================================================
   RENDER ALL REGIONS
   ===================================================== */

function render() {

    let html = "";


    html +=
        renderRegion(
            "ENUO"
        );


    html +=
        renderRegion(
            "HGAO"
        );


    html +=
        renderRegion(
            "MYFO"
        );


    if (
        html === ""
    ) {

        html = `

            <div class="no-data">

                No data available
                for selected date.

            </div>

        `;

    }


    document.getElementById(
        "dashboard"
    ).innerHTML =
        html;

}


/* =====================================================
   INITIALIZE
   ===================================================== */

const allDates =
    getAllDates();


/*
   Default = All Dates
*/

appliedDates =
    [...allDates];


tempDates =
    [...allDates];


buildDateList();

updateDateFilterText();

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
    json_data
)

html = html.replace(
    "__CPE_PLACEHOLDER__",
    cpe_json
)


# =========================================================
# STREAMLIT
# =========================================================

components.html(
    html,
    height=1900,
    scrolling=True
)