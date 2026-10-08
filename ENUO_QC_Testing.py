import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
import json


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="QC Testing - ENUO",
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

@st.cache_data(ttl=60)
def load_google_sheet():

    if SHEET_TAB:
        url = (
            f"https://docs.google.com/spreadsheets/d/"
            f"{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_TAB}"
        )
    else:
        url = (
            f"https://docs.google.com/spreadsheets/d/"
            f"{SHEET_ID}/gviz/tq?tqx=out:csv"
        )

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    from io import StringIO

    df = pd.read_csv(StringIO(response.text))

    return df


# ============================================================
# PREPARE DATA
# ============================================================

try:

    df = load_google_sheet()

    # --------------------------------------------------------
    # Clean column names
    # --------------------------------------------------------

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

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
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        st.error(
            "Missing columns: "
            + ", ".join(missing_columns)
        )
        st.stop()

    # --------------------------------------------------------
    # ENUO ONLY
    # --------------------------------------------------------

    df["Region"] = (
        df["Region"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df = df[df["Region"] == "ENUO"].copy()

    # --------------------------------------------------------
    # Clean Date
    # --------------------------------------------------------

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce"
    )

    df = df.dropna(subset=["Date"]).copy()

    df["DateDisplay"] = df["Date"].dt.strftime(
        "%d-%b-%Y"
    )

    # --------------------------------------------------------
    # Clean Daily JD
    # --------------------------------------------------------

    df["Daily (JD)"] = (
        df["Daily (JD)"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------
    # Clean Device Name
    # --------------------------------------------------------

    df["Device Name"] = (
        df["Device Name"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------
    # Clean Issue Type
    # --------------------------------------------------------

    df["Issue Type"] = (
        df["Issue Type"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------
    # Clean MAC
    # --------------------------------------------------------

    df["MAC"] = (
        df["MAC"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------
    # Clean Qty
    # --------------------------------------------------------

    df["Qty"] = pd.to_numeric(
        df["Qty"],
        errors="coerce"
    ).fillna(0)

    # --------------------------------------------------------
    # Sort Date
    # --------------------------------------------------------

    df = df.sort_values(
        by=["Date", "Daily (JD)"],
        ascending=[True, True]
    )

    # --------------------------------------------------------
    # Send required data to HTML
    # --------------------------------------------------------

    records = []

    for _, row in df.iterrows():

        records.append({
            "date": row["DateDisplay"],
            "date_sort": row["Date"].strftime("%Y-%m-%d"),

            "device": str(row["Device Name"]).strip(),

            "daily": str(row["Daily (JD)"]).strip(),

            "qty": float(row["Qty"]),

            "mac": str(row["MAC"]).strip(),

            "issue_type": str(row["Issue Type"]).strip()
        })

    data_json = json.dumps(
        records,
        ensure_ascii=False
    )


except Exception as e:

    st.error(f"Unable to load Google Sheet: {e}")
    st.stop()


# ============================================================
# HTML DASHBOARD
# ============================================================

html = r"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>QC Testing</title>


<style>

/* =========================================================
   GLOBAL
   ========================================================= */

* {
    box-sizing: border-box;
}

body {

    margin: 0;

    padding: 24px;

    background: #f5f7fb;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    color: #1f2937;
}


/* =========================================================
   HEADER
   ========================================================= */

.header {

    margin-bottom: 20px;
}

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


/* =========================================================
   DATE FILTER
   ========================================================= */

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

.date-button:hover {

    border-color: #9ca3af;
}

.arrow {

    font-size: 12px;
}


/* =========================================================
   DROPDOWN
   ========================================================= */

.dropdown {

    display: none;

    position: absolute;

    top: 48px;

    left: 0;

    width: 320px;

    background: white;

    border: 1px solid #d1d5db;

    border-radius: 10px;

    box-shadow:
        0 10px 25px rgba(0,0,0,0.10);

    z-index: 999;
}

.dropdown.open {

    display: block;
}


/* =========================================================
   SEARCH
   ========================================================= */

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

    outline: none;

    font-size: 13px;
}

.search-box input:focus {

    border-color: #6b7280;
}


/* =========================================================
   SELECT BUTTONS
   ========================================================= */

.select-actions {

    display: flex;

    gap: 8px;

    padding: 9px 10px;

    border-bottom: 1px solid #e5e7eb;
}

.select-actions button {

    border: none;

    background: #f3f4f6;

    padding: 6px 10px;

    border-radius: 5px;

    cursor: pointer;

    font-size: 12px;

    color: #374151;
}

.select-actions button:hover {

    background: #e5e7eb;
}


/* =========================================================
   DATE LIST
   ========================================================= */

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

.date-option:hover {

    background: #f9fafb;
}

.date-option input {

    width: 15px;

    height: 15px;

    cursor: pointer;
}


/* =========================================================
   DROPDOWN FOOTER
   ========================================================= */

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

    font-size: 13px;
}

.cancel-btn {

    background: white;

    border: 1px solid #d1d5db;

    color: #374151;
}

.apply-btn {

    background: #111827;

    border: 1px solid #111827;

    color: white;
}


/* =========================================================
   TABLE
   ========================================================= */

.table-container {

    width: 100%;

    overflow-x: auto;

    background: white;

    border: 1px solid #e5e7eb;

    border-radius: 10px;

    box-shadow:
        0 2px 8px rgba(0,0,0,0.04);
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

    font-weight: 600;

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

tbody tr:hover {

    background: #f9fafb;
}

tbody tr:last-child td {

    border-bottom: none;
}


/* =========================================================
   DATE
   ========================================================= */

.date-cell {

    font-weight: 600;

    text-align: left !important;

    padding-left: 18px !important;
}


/* =========================================================
   NUMBER
   ========================================================= */

.number {

    font-variant-numeric: tabular-nums;
}


/* =========================================================
   HC INPUT
   ========================================================= */

.hc-input {

    width: 80px;

    height: 34px;

    border: 1px solid #d1d5db;

    border-radius: 6px;

    text-align: center;

    font-size: 13px;

    outline: none;
}

.hc-input:focus {

    border-color: #6b7280;

    box-shadow:
        0 0 0 2px rgba(107,114,128,0.12);
}


/* =========================================================
   KPI
   ========================================================= */

.kpi {

    font-weight: 700;

    font-size: 14px;
}


/* =========================================================
   TOTAL
   ========================================================= */

.total-row td {

    background: #f3f4f6;

    font-weight: 700;

    border-top: 2px solid #d1d5db;
}


/* =========================================================
   EMPTY
   ========================================================= */

.empty {

    padding: 35px;

    text-align: center;

    color: #6b7280;

    font-size: 14px;
}

</style>

</head>


<body>


<!-- =======================================================
     HEADER
     ======================================================= -->

<div class="header">

    <h1>QC Testing</h1>

    <p>ENUO</p>

</div>


<!-- =======================================================
     DATE FILTER
     ======================================================= -->

<div class="filter-area">

    <button
        class="date-button"
        onclick="toggleDropdown()"
        id="dateButton"
    >

        <span id="dateButtonText">
            All Dates
        </span>

        <span class="arrow">
            ▼
        </span>

    </button>


    <div
        class="dropdown"
        id="dateDropdown"
    >


        <!-- SEARCH -->

        <div class="search-box">

            <input
                type="text"
                id="dateSearch"
                placeholder="Search date..."
                oninput="filterDates()"
            >

        </div>


        <!-- SELECT ACTIONS -->

        <div class="select-actions">

            <button onclick="selectAllDates()">
                Select All
            </button>

            <button onclick="clearDates()">
                Clear
            </button>

        </div>


        <!-- DATE LIST -->

        <div
            class="date-list"
            id="dateList"
        ></div>


        <!-- FOOTER -->

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


<!-- =======================================================
     TABLE
     ======================================================= -->

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


        <tbody id="tableBody">

        </tbody>

    </table>

</div>


<script>


// =========================================================
// DATA FROM PYTHON
// =========================================================

const DATA = __DATA_JSON__;


// =========================================================
// GLOBAL VARIABLES
// =========================================================

let selectedDates = [];

let tempSelectedDates = [];

let hcValues = {};


// =========================================================
// DATE LIST
// =========================================================

const uniqueDates = [
    ...new Set(
        DATA.map(row => row.date)
    )
];


// Sort dates
uniqueDates.sort(
    (a, b) => {

        const da = new Date(a);
        const db = new Date(b);

        return da - db;
    }
);


// =========================================================
// INITIAL HC
// =========================================================

uniqueDates.forEach(date => {

    hcValues[date] = 1;

});


// =========================================================
// DROPDOWN
// =========================================================

function toggleDropdown() {

    const dropdown =
        document.getElementById(
            "dateDropdown"
        );

    if (
        dropdown.classList.contains("open")
    ) {

        dropdown.classList.remove("open");

    } else {

        tempSelectedDates = [
            ...selectedDates
        ];

        renderDateList();

        dropdown.classList.add("open");
    }
}


// =========================================================
// RENDER DATE LIST
// =========================================================

function renderDateList() {

    const list =
        document.getElementById(
            "dateList"
        );

    const search =
        document.getElementById(
            "dateSearch"
        ).value
        .trim()
        .toLowerCase();


    list.innerHTML = "";


    uniqueDates.forEach(date => {

        if (
            search &&
            !date.toLowerCase().includes(search)
        ) {
            return;
        }


        const label =
            document.createElement("label");

        label.className =
            "date-option";


        const checkbox =
            document.createElement("input");

        checkbox.type = "checkbox";

        checkbox.value = date;

        checkbox.checked =
            tempSelectedDates.includes(date);


        checkbox.addEventListener(
            "change",
            function () {

                if (this.checked) {

                    if (
                        !tempSelectedDates.includes(
                            date
                        )
                    ) {

                        tempSelectedDates.push(
                            date
                        );

                    }

                } else {

                    tempSelectedDates =
                        tempSelectedDates.filter(
                            d => d !== date
                        );
                }

            }
        );


        const text =
            document.createElement("span");

        text.textContent = date;


        label.appendChild(checkbox);

        label.appendChild(text);

        list.appendChild(label);

    });

}


// =========================================================
// FILTER DATE SEARCH
// =========================================================

function filterDates() {

    renderDateList();

}


// =========================================================
// SELECT ALL
// =========================================================

function selectAllDates() {

    tempSelectedDates = [
        ...uniqueDates
    ];

    renderDateList();

}


// =========================================================
// CLEAR
// =========================================================

function clearDates() {

    tempSelectedDates = [];

    renderDateList();

}


// =========================================================
// CANCEL
// =========================================================

function cancelDates() {

    document
        .getElementById("dateDropdown")
        .classList.remove("open");

}


// =========================================================
// APPLY
// =========================================================

function applyDates() {

    selectedDates = [
        ...tempSelectedDates
    ];


    selectedDates.sort(
        (a, b) => {

            return new Date(a) - new Date(b);

        }
    );


    document
        .getElementById("dateDropdown")
        .classList.remove("open");


    updateDateButton();

    updateTable();

}


// =========================================================
// DATE BUTTON TEXT
// =========================================================

function updateDateButton() {

    const text =
        document.getElementById(
            "dateButtonText"
        );


    if (
        selectedDates.length === 0 ||
        selectedDates.length === uniqueDates.length
    ) {

        text.textContent =
            "All Dates";

    } else if (
        selectedDates.length === 1
    ) {

        text.textContent =
            selectedDates[0];

    } else {

        text.textContent =
            selectedDates.length +
            " Dates Selected";

    }

}


// =========================================================
// NUMBER
// =========================================================

function number(value) {

    const n =
        Number(value);

    if (
        Number.isNaN(n)
    ) {

        return 0;

    }

    return n;

}


// =========================================================
// CALCULATE DAILY DATA
// =========================================================

function calculate(date) {

    let qcInbound = 0;

    let totalTest = 0;

    let qcPass = 0;

    let qcFail = 0;


    DATA.forEach(row => {

        if (
            row.date !== date
        ) {

            return;

        }


        const daily =
            String(
                row.daily || ""
            )
            .trim()
            .toLowerCase();


        const device =
            String(
                row.device || ""
            )
            .trim()
            .toLowerCase();


        const issueType =
            String(
                row.issue_type || ""
            )
            .trim()
            .toLowerCase();


        const qty =
            number(row.qty);


        const mac =
            String(
                row.mac || ""
            ).trim();


        // =================================================
        // QC INBOUND
        //
        // Run       -> MAC COUNT
        // Cleaning  + FFO -> QTY SUM
        // =================================================

        if (
            daily === "run"
        ) {

            if (
                mac !== "" &&
                mac.toLowerCase() !== "nan"
            ) {

                qcInbound += 1;

            }

        }


        if (
            daily === "cleaning" &&
            device === "ffo"
        ) {

            qcInbound += qty;

        }


        // =================================================
        // TEST DATA
        //
        // Speed Test
        // LAN Port Test
        //
        // Total Test = QTY SUM
        // =================================================

        if (
            daily === "speed test" ||
            daily === "lan port test"
        ) {

            totalTest += qty;


            // =============================================
            // USE = PASS
            // =============================================

            if (
                issueType === "use"
            ) {

                qcPass += qty;

            }


            // =============================================
            // RMA = FAIL
            // =============================================

            if (
                issueType === "rma"
            ) {

                qcFail += qty;

            }

        }

    });


    // RMA = QC FAIL

    const rma =
        qcFail;


    return {

        qcInbound,
        totalTest,
        qcPass,
        qcFail,
        rma

    };

}


// =========================================================
// SAVE HC
// =========================================================

function saveHC(date, value) {

    let hc =
        Number(value);


    if (
        Number.isNaN(hc) ||
        hc < 0
    ) {

        hc = 0;

    }


    hcValues[date] = hc;


    updateTable();

}


// =========================================================
// FORMAT KPI
// =========================================================

function formatKPI(value) {

    if (
        !Number.isFinite(value)
    ) {

        return "0";

    }


    return value.toFixed(2);

}


// =========================================================
// UPDATE TABLE
// =========================================================

function updateTable() {

    const tbody =
        document.getElementById(
            "tableBody"
        );


    tbody.innerHTML = "";


    let datesToShow;


    if (
        selectedDates.length === 0
    ) {

        datesToShow = [
            ...uniqueDates
        ];

    } else {

        datesToShow = [
            ...selectedDates
        ];

    }


    datesToShow.sort(
        (a, b) => {

            return new Date(a) - new Date(b);

        }
    );


    // =====================================================
    // EMPTY
    // =====================================================

    if (
        datesToShow.length === 0
    ) {

        tbody.innerHTML = `
            <tr>
                <td
                    colspan="8"
                    class="empty"
                >
                    No date selected
                </td>
            </tr>
        `;

        return;

    }


    // =====================================================
    // TOTAL VALUES
    // =====================================================

    let grandInbound = 0;

    let grandTest = 0;

    let grandPass = 0;

    let grandFail = 0;

    let grandRMA = 0;

    let grandHC = 0;


    // =====================================================
    // DAILY ROWS
    // =====================================================

    datesToShow.forEach(date => {

        const result =
            calculate(date);


        const hc =
            number(
                hcValues[date]
            );


        const kpi =
            hc > 0
                ? result.totalTest / hc
                : 0;


        // Grand totals

        grandInbound +=
            result.qcInbound;

        grandTest +=
            result.totalTest;

        grandPass +=
            result.qcPass;

        grandFail +=
            result.qcFail;

        grandRMA +=
            result.rma;

        grandHC +=
            hc;


        // =================================================
        // ROW
        // =================================================

        const tr =
            document.createElement("tr");


        tr.innerHTML = `

            <td class="date-cell">
                ${date}
            </td>


            <td class="number">
                ${result.qcInbound}
            </td>


            <td class="number">
                ${result.totalTest}
            </td>


            <td class="number">
                ${result.qcPass}
            </td>


            <td class="number">
                ${result.qcFail}
            </td>


            <td class="number">
                ${result.rma}
            </td>


            <td>

                <input
                    class="hc-input"
                    type="number"
                    min="0"
                    step="1"
                    value="${hc}"
                    onchange="
                        saveHC(
                            '${date}',
                            this.value
                        )
                    "
                >

            </td>


            <td class="kpi">
                ${formatKPI(kpi)}
            </td>

        `;


        tbody.appendChild(tr);

    });


    // =====================================================
    // TOTAL KPI
    // =====================================================

    const grandKPI =
        grandHC > 0
            ? grandTest / grandHC
            : 0;


    // =====================================================
    // TOTAL ROW
    // =====================================================

    const totalRow =
        document.createElement("tr");


    totalRow.className =
        "total-row";


    totalRow.innerHTML = `

        <td class="date-cell">
            TOTAL
        </td>


        <td class="number">
            ${grandInbound}
        </td>


        <td class="number">
            ${grandTest}
        </td>


        <td class="number">
            ${grandPass}
        </td>


        <td class="number">
            ${grandFail}
        </td>


        <td class="number">
            ${grandRMA}
        </td>


        <td class="number">
            ${grandHC}
        </td>


        <td class="kpi">
            ${formatKPI(grandKPI)}
        </td>

    `;


    tbody.appendChild(totalRow);

}


// =========================================================
// INITIAL LOAD
// =========================================================

updateDateButton();

updateTable();


// =========================================================
// CLOSE DROPDOWN WHEN CLICKING OUTSIDE
// =========================================================

document.addEventListener(
    "click",
    function(event) {

        const area =
            document.querySelector(
                ".filter-area"
            );


        if (
            !area.contains(event.target)
        ) {

            document
                .getElementById(
                    "dateDropdown"
                )
                .classList.remove("open");

        }

    }
);


</script>

</body>

</html>
"""


# ============================================================
# INSERT DATA
# ============================================================

html = html.replace(
    "__DATA_JSON__",
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