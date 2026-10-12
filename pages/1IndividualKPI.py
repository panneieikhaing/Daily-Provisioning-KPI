
import re
from io import StringIO
from numbers import Number

import pandas as pd
import requests
import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Daily Individual KPI",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# GOOGLE SHEET IDS
# ============================================================

ENUO_HGAO_SHEET_ID = "14WOHloWhGuQOc95PrRUsYWAHT6PTCC6EL2pY18uglVs"
MDY_SHEET_ID = "1XrjpVgSeu1lDpyNNyuJdjYji8MxnoQWuo3bwwPWAs9Q"

SHEET1_TAB = ""
SHEET2_TAB = ""
FILTER_SECTION = "individual_kpi"


# ============================================================
# CALCULATION RULES
# ============================================================

CALCULATION_RULES = [
    ("RUN", "run", "MAC Count", "ALL"),
    ("Default", "default", "MAC Count", "ALL"),

    ("DBM", "dbm", "Qty Sum", "ALL"),
    ("Cleaning", "cleaning", "Qty Sum", "ALL"),
    ("Speed Test", "speed test", "Qty Sum", "ALL"),
    ("Lan Port Test", "lan port test", "Qty Sum", "ALL"),
    ("RMA", "rma", "Qty Sum", "ALL"),
    ("Test RMA", "test rma", "Qty Sum", "ALL"),
    ("Accessories", "accessories", "Qty Sum", "ALL"),
    ("Battery", "battery", "Qty Sum", "ALL"),
    ("DC Port Change", "dc port change", "Qty Sum", "ALL"),
    ("Glueattach", "glueattach", "Qty Sum", "ALL"),
    ("Injector Test", "injector test", "Qty Sum", "ALL"),
    ("Leave", "leave", "Name Count", "ALL"),
    ("Terminal Test", "terminal test", "Qty Sum", "ALL"),
    ("WAN Port Test", "wan port test", "Qty Sum", "ALL"),
    ("MAC", "mac", "Qty Sum", "ALL"),
    ("Exchange Test", "exchange test", "Qty Sum", "ALL"),
    ("Cover Change", "cover change", "Qty Sum", "ALL"),
    ("Infra", "infra", "Qty Sum", "ALL"),
    ("In & Out", "in & out", "Qty Sum", "ALL"),
    ("Flang Change", "flang change", "Qty Sum", "ALL"),
    ("14V", "14v", "Qty Sum", "ALL"),
    ("Remove Mini Battery", "remove mini battery", "Qty Sum", "ALL"),
    ("Soldering Mini CPE", "soldering mini cpe", "Qty Sum", "ALL"),
    ("Glue Mini Module", "glue mini module", "Qty Sum", "ALL"),
]

SUMMARY_CATEGORIES = [rule[0] for rule in CALCULATION_RULES]


# ============================================================
# STYLING
# ============================================================

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 1rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100% !important;
    }

    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    .main-title {
        font-size: 27px;
        font-weight: 800;
        line-height: 1.2;
        color: #17365D;
        margin: 0 0 0.5rem 0 !important;
        padding: 0 !important;
    }

    div[data-testid="stVerticalBlock"] {
        gap: 0.55rem;
    }

    h2, h3 {
        color: #17365D;
    }

    div[data-testid="stButton"] > button {
        border-radius: 8px;
        font-weight: 600;
        min-height: 36px;
    }

    div[data-testid="stExpander"] {
        border-radius: 9px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# GENERAL HELPERS
# ============================================================

def normalize_text(value):
    if pd.isna(value):
        return ""

    text = str(value).strip().lower()
    return re.sub(r"\s+", " ", text)


def normalize_task(value):
    text = normalize_text(value)
    text = text.replace("_", " ").replace("-", " ")
    return re.sub(r"\s+", " ", text).strip()


def find_column(df, aliases):
    lookup = {
        normalize_text(column).replace("_", " "): column
        for column in df.columns
    }

    for alias in aliases:
        key = normalize_text(alias).replace("_", " ")
        if key in lookup:
            return lookup[key]

    def simple(value):
        return re.sub(r"[^a-z0-9]", "", normalize_text(value))

    lookup_simple = {
        simple(column): column
        for column in df.columns
    }

    for alias in aliases:
        key = simple(alias)
        if key in lookup_simple:
            return lookup_simple[key]

    return None


def clean_string_column(series):
    return (
        series.fillna("")
        .astype(str)
        .str.strip()
        .replace({"nan": "", "None": ""})
    )


def numeric_series(series):
    return pd.to_numeric(
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.strip(),
        errors="coerce",
    ).fillna(0)


# ============================================================
# LOAD GOOGLE SHEETS
# ============================================================

@st.cache_data(ttl=60, show_spinner=False)
def download_google_sheet(sheet_id: str, tab_name: str = ""):
    url = (
        f"https://docs.google.com/spreadsheets/d/"
        f"{sheet_id}/export?format=csv"
    )

    if tab_name:
        url += f"&sheet={requests.utils.quote(tab_name)}"

    response = requests.get(url, timeout=30)
    response.raise_for_status()
    response.encoding = "utf-8"

    if not response.text.strip():
        return pd.DataFrame()

    return pd.read_csv(StringIO(response.text), dtype=str)


# ============================================================
# NORMALIZE SOURCE DATA
# ============================================================

def normalize_columns(df, default_region=""):
    if df is None or df.empty:
        return pd.DataFrame()

    date_col = find_column(
        df, ["Date", "Work Date", "Provisioning Date"]
    )
    region_col = find_column(
        df, ["Region", "Region Name", "Area"]
    )
    name_col = find_column(
        df,
        [
            "Name", "Employee Name", "Staff Name",
            "Engineer Name", "Technician Name",
        ],
    )
    device_col = find_column(
        df, ["Device Name", "Device", "Model", "Device Model"]
    )
    daily_col = find_column(
        df,
        [
            "Daily (JD)", "Daily JD", "Daily",
            "Task", "Activity", "Job Description",
        ],
    )
    qty_col = find_column(df, ["Qty", "Quantity", "QTY"])
    mac_col = find_column(
        df,
        ["MAC", "MAC Address", "MAC/SN", "MAC SN",
         "Serial Number", "SN"],
    )

    missing = []
    if date_col is None:
        missing.append("Date")
    if daily_col is None:
        missing.append("Daily (JD)")
    if qty_col is None:
        missing.append("Qty")
    if mac_col is None:
        missing.append("MAC")

    if missing:
        raise ValueError(
            "Google Sheet မှာ လိုအပ်တဲ့ column မတွေ့ပါ: "
            + ", ".join(missing)
        )

    result = pd.DataFrame()

    result["Date"] = (
        clean_string_column(df[date_col])
        .replace("", pd.NA)
        .ffill()
        .fillna("")
    )

    if region_col:
        result["Region"] = (
            clean_string_column(df[region_col])
            .replace("", pd.NA)
            .ffill()
            .fillna("")
        )
    else:
        result["Region"] = default_region

    if name_col:
        result["Name"] = (
            clean_string_column(df[name_col])
            .replace("", pd.NA)
            .ffill()
            .fillna("")
        )
    else:
        result["Name"] = "Unknown"

    result["Device Name"] = (
        clean_string_column(df[device_col])
        if device_col
        else ""
    )
    result["Daily (JD)"] = clean_string_column(df[daily_col])
    result["Qty"] = numeric_series(df[qty_col])
    result["MAC"] = clean_string_column(df[mac_col])

    parsed_dates = pd.to_datetime(
        result["Date"],
        dayfirst=True,
        errors="coerce",
    )

    bad_dates = parsed_dates.isna() & result["Date"].ne("")

    if bad_dates.any():
        parsed_dates.loc[bad_dates] = pd.to_datetime(
            result.loc[bad_dates, "Date"],
            errors="coerce",
        )

    result["Date"] = (
        parsed_dates.dt.strftime("%Y-%m-%d").fillna("")
    )
    result["Region"] = clean_string_column(
        result["Region"]
    ).str.upper()
    result["Name"] = clean_string_column(result["Name"])
    result["Task Key"] = result["Daily (JD)"].map(normalize_task)

    result = result[
        (result["Date"] != "")
        & (result["Daily (JD)"].str.strip() != "")
    ].copy()

    return result


# ============================================================
# LOAD ALL REGIONAL DATA
# ============================================================

def load_all_data():
    frames = []

    source1 = download_google_sheet(
        ENUO_HGAO_SHEET_ID, SHEET1_TAB
    )
    if not source1.empty:
        frames.append(normalize_columns(source1))

    source2 = download_google_sheet(
        MDY_SHEET_ID, SHEET2_TAB
    )
    if not source2.empty:
        frames.append(
            normalize_columns(source2, default_region="MDY")
        )

    frames = [frame for frame in frames if not frame.empty]

    if not frames:
        return pd.DataFrame(
            columns=[
                "Date", "Region", "Name", "Device Name",
                "Daily (JD)", "Qty", "MAC", "Task Key",
            ]
        )

    data = pd.concat(frames, ignore_index=True)

    return data.sort_values(
        ["Date", "Region", "Name"],
        ascending=[False, True, True],
    ).reset_index(drop=True)


# ============================================================
# KPI CALCULATIONS
# ============================================================

def rule_applies(rule, region):
    source = rule[3]
    region = str(region).upper()

    if source == "ALL":
        return True
    if source == "ENUO_HGAO":
        return region in {"ENUO", "HGAO"}
    if source == "MDY":
        return region == "MDY"

    return True


def count_nonblank_mac(data):
    if data.empty:
        return 0

    values = (
        data["MAC"].fillna("").astype(str).str.strip()
    )
    return int(values.ne("").sum())


def calculate_category_value(data, category, region):
    rule = next(
        (item for item in CALCULATION_RULES if item[0] == category),
        None,
    )

    if (
        rule is None
        or data.empty
        or not rule_applies(rule, region)
    ):
        return 0

    if rule[2] == "MAC Count":
        return count_nonblank_mac(data)
    if rule[2] == "Name Count":
        return 1 if not data.empty else 0

    return int(round(float(data["Qty"].sum())))


def find_rule_for_task(task_key, region):
    task_key = normalize_task(task_key)

    rules = sorted(
        CALCULATION_RULES,
        key=lambda rule: len(rule[1]),
        reverse=True,
    )

    for rule in rules:
        key = normalize_task(rule[1])

        if key and (task_key == key or key in task_key):
            if rule_applies(rule, region):
                return rule

    return None


# ============================================================
# DAILY SUMMARY
# ============================================================
@st.cache_data(show_spinner=False)
def create_summary(data):
    columns = (
        ["Date", "Region", "Name"]
        + SUMMARY_CATEGORIES
        + ["Total Count"]
    )

    if data.empty:
        return pd.DataFrame(columns=columns)

    rows = []
    for (date, region, name), group in data.groupby(
        ["Date", "Region", "Name"], dropna=False
    ):
        row = {"Date": date, "Region": region, "Name": name}
        numeric_total = 0

        for category in SUMMARY_CATEGORIES:
            rule = next(item for item in CALCULATION_RULES if item[0] == category)
            rule_key = normalize_task(rule[1])
            matching = group[group["Task Key"].map(
                lambda value: rule_key in normalize_task(value)
            )]

            # Prevent overlapping task names from being double-counted.
            if category == "RMA":
                matching = matching[~matching["Task Key"].map(
                    lambda value: "test rma" in normalize_task(value)
                )]
            elif category == "Battery":
                matching = matching[~matching["Task Key"].map(
                    lambda value: "remove mini battery" in normalize_task(value)
                )]
            elif category in {"MAC", "DBM"}:
                matching = matching[~matching["Task Key"].map(
                    lambda value: "mac/dbm" in normalize_task(value)
                    or "mac dbm" in normalize_task(value)
                )]

            # MAC / DBM applies only to the MDY source task label.
            if category == "MAC / DBM":
                matching = group[group["Task Key"].map(
                    lambda value: "mac/dbm" in normalize_task(value)
                    or "mac dbm" in normalize_task(value)
                )]

            if category == "Leave":
                row[category] = "Leave" if not matching.empty else 0
                continue

            value = calculate_category_value(matching, category, region)
            row[category] = value
            numeric_total += value

        row["Total Count"] = numeric_total
        rows.append(row)

    return pd.DataFrame(rows, columns=columns)



# ============================================================
# DAILY TOTAL
# ============================================================
@st.cache_data(show_spinner=False)

def create_daily_total(summary):
    columns = ["Date", "Name", "Total", "Meet KPI"]
    if summary.empty:
        return pd.DataFrame(columns=columns)

    rows = []
    for (date, name), group in summary.groupby(["Date", "Name"], dropna=False):
        total = int(round(pd.to_numeric(
            group["Total Count"], errors="coerce"
        ).fillna(0).sum()))

        has_leave = group.get("Leave", pd.Series(dtype=object)).map(
            lambda value: isinstance(value, str) and value.strip().casefold() == "leave"
        ).any()

        # Existing KPI target is 150. Extra rules are only checked for NO rows.
        if total >= 150:
            status = "YES"
        elif has_leave:
            status = "Leave"
        else:
            status = "NO"
            extra_yes_categories = [
                "Battery", "DC Port Change", "Glueattach", "WAN Port Test",
                "Infra", "MAC", "Cover Change", "Flang Change", "14V",
                "Remove Mini Battery", "Soldering Mini CPE", "Glue Mini Module",
                "Exchange Test",
            ]
            for category in extra_yes_categories:
                if category in group.columns and pd.to_numeric(
                    group[category], errors="coerce"
                ).fillna(0).ge(1).any():
                    status = "YES"
                    break

            if status == "NO":
                rma_qty = pd.to_numeric(group.get("RMA", 0), errors="coerce")
                test_rma_qty = pd.to_numeric(group.get("Test RMA", 0), errors="coerce")
                if (rma_qty >= 40).any() or (test_rma_qty >= 40).any():
                    status = "YES"

        if has_leave and total > 0:
            total_display = f"Leave, {total:,}"
        elif has_leave:
            total_display = "Leave"
        else:
            total_display = total

        rows.append({
            "Date": date,
            "Name": name,
            "Total": total_display,
            "Meet KPI": status,
        })

    result = pd.DataFrame(rows, columns=columns)
    return result.sort_values(["Date", "Name"], ascending=[False, True]).reset_index(drop=True)



# ============================================================
# DAILY DETAIL
# ============================================================
@st.cache_data(show_spinner=False)
def create_daily_detail(data):
    columns = [
        "Date", "Region", "Name", "Device Name",
        "Daily (JD)", "Qty", "MAC Count", "Calculated Total",
    ]

    if data.empty:
        return pd.DataFrame(columns=columns)

    rows = []
    keys = ["Date", "Region", "Name", "Device Name", "Daily (JD)"]

    for values, group in data.groupby(keys, dropna=False):
        date, region, name, device, daily = values

        rule = find_rule_for_task(daily, region)
        mac_count = count_nonblank_mac(group)
        qty_sum = int(round(float(group["Qty"].sum())))

        if rule is not None and rule[2] == "MAC Count":
            calculated = mac_count
        else:
            calculated = qty_sum

        rows.append({
            "Date": date,
            "Region": region,
            "Name": name,
            "Device Name": device,
            "Daily (JD)": daily,
            "Qty": qty_sum,
            "MAC Count": mac_count,
            "Calculated Total": calculated,
        })

    return pd.DataFrame(rows, columns=columns).sort_values(
        ["Date", "Region", "Name"],
        ascending=[False, True, True],
    )


# ============================================================
# FILTER HELPERS
# ============================================================

def filter_options(data, column):
    values = [
        str(value).strip()
        for value in data[column].dropna().unique()
        if str(value).strip()
    ]

    if column == "Date":
        return sorted(values, reverse=True)

    return sorted(values, key=str.casefold)


def filter_state_key(dimension, suffix):
    return f"{FILTER_SECTION}_{dimension}_{suffix}"


def initialize_filter_state(dimension, options):
    selected_key = filter_state_key(dimension, "selected")
    draft_key = filter_state_key(dimension, "draft")

    if selected_key not in st.session_state:
        if dimension == "Date" and options:
            st.session_state[selected_key] = [options[0]]
        else:
            st.session_state[selected_key] = list(options)

    st.session_state[selected_key] = [
        value for value in st.session_state[selected_key]
        if value in options
    ]

    if draft_key not in st.session_state:
        st.session_state[draft_key] = list(
            st.session_state[selected_key]
        )
    else:
        st.session_state[draft_key] = [
            value for value in st.session_state[draft_key]
            if value in options
        ]


def toggle_filter_panel(dimension):
    open_key = filter_state_key(dimension, "open")
    is_open = st.session_state.get(open_key, False)
    st.session_state[open_key] = not is_open

    if not is_open:
        st.session_state[
            filter_state_key(dimension, "draft")
        ] = list(
            st.session_state.get(
                filter_state_key(dimension, "selected"), []
            )
        )


def apply_filter(dimension):
    st.session_state[
        filter_state_key(dimension, "selected")
    ] = list(
        st.session_state.get(
            filter_state_key(dimension, "draft"), []
        )
    )
    st.session_state[filter_state_key(dimension, "open")] = False


def cancel_filter(dimension):
    st.session_state[
        filter_state_key(dimension, "draft")
    ] = list(
        st.session_state.get(
            filter_state_key(dimension, "selected"), []
        )
    )
    st.session_state[filter_state_key(dimension, "open")] = False


# ============================================================
# FILTER — SELECT ALL / CLEAR ALL FIX
# ============================================================

def render_one_filter(dimension, label, options, searchable=True):
    initialize_filter_state(dimension, options)

    open_key = filter_state_key(dimension, "open")
    draft_key = filter_state_key(dimension, "draft")
    selected_key = filter_state_key(dimension, "selected")
    search_key = filter_state_key(dimension, "search")

    st.button(
        f"{label}  ▾",
        key=filter_state_key(dimension, "button"),
        use_container_width=True,
        on_click=toggle_filter_panel,
        args=(dimension,),
    )

    if st.session_state.get(open_key, False):
        search = ""

        if searchable:
            search = st.text_input(
                f"Search {label}",
                key=search_key,
                placeholder=f"Search {label.lower()}...",
                label_visibility="collapsed",
            ).strip().casefold()

        visible_options = [
            option for option in options
            if search in str(option).casefold()
        ]

        def checkbox_key_for(option):
            # Stable key for each option; avoids index changes
            # when the user searches or filters the options.
            return filter_state_key(
                dimension,
                "check_" + str(abs(hash(str(option)))),
            )

        # Initialize checkbox widget states BEFORE rendering buttons.
        for option in visible_options:
            key = checkbox_key_for(option)
            if key not in st.session_state:
                st.session_state[key] = (
                    option in st.session_state[draft_key]
                )

        def select_visible_options():
            current = list(st.session_state.get(draft_key, []))

            for option in visible_options:
                if option not in current:
                    current.append(option)
                st.session_state[checkbox_key_for(option)] = True

            st.session_state[draft_key] = current

        def clear_visible_options():
            current = list(st.session_state.get(draft_key, []))

            st.session_state[draft_key] = [
                option for option in current
                if option not in visible_options
            ]

            for option in visible_options:
                st.session_state[checkbox_key_for(option)] = False

        all_col, clear_col = st.columns(2)

        all_col.button(
            "Select All",
            key=filter_state_key(dimension, "all"),
            use_container_width=True,
            on_click=select_visible_options,
        )

        clear_col.button(
            "Clear All",
            key=filter_state_key(dimension, "clear"),
            use_container_width=True,
            on_click=clear_visible_options,
        )

        with st.container(height=230, border=False):
            for option in visible_options:
                st.checkbox(
                    str(option),
                    key=checkbox_key_for(option),
                    on_change=lambda opt=option: update_draft_from_checkbox(
                        dimension, opt, checkbox_key_for(opt)
                    ),
                )

        apply_col, cancel_col = st.columns(2)

        apply_col.button(
            "Apply",
            key=filter_state_key(dimension, "apply"),
            use_container_width=True,
            type="primary",
            on_click=apply_filter,
            args=(dimension,),
        )

        cancel_col.button(
            "Cancel",
            key=filter_state_key(dimension, "cancel"),
            use_container_width=True,
            on_click=cancel_filter,
            args=(dimension,),
        )

    return list(st.session_state[selected_key])


def update_draft_from_checkbox(dimension, option, checkbox_key):
    draft_key = filter_state_key(dimension, "draft")
    current = list(st.session_state.get(draft_key, []))

    if st.session_state.get(checkbox_key, False):
        if option not in current:
            current.append(option)
    else:
        if option in current:
            current.remove(option)

    st.session_state[draft_key] = current


# ============================================================
# SHARED REGION / DATE / NAME FILTER
# ============================================================

def render_shared_filter(data):
    st.markdown("**Filter**")

    region_options = filter_options(data, "Region")
    date_options = filter_options(data, "Date")
    name_options = filter_options(data, "Name")

    col_region, col_date, col_name = st.columns([1, 1, 1])

    with col_region:
        selected_regions = render_one_filter(
            "Region", "Region", region_options
        )

    with col_date:
        selected_dates = render_one_filter(
            "Date", "Date", date_options
        )

    with col_name:
        selected_names = render_one_filter(
            "Name", "Name", name_options
        )

    filtered = data.copy()

    if selected_regions:
        filtered = filtered[
            filtered["Region"].isin(selected_regions)
        ]
    else:
        filtered = filtered.iloc[0:0]

    if selected_dates:
        filtered = filtered[
            filtered["Date"].isin(selected_dates)
        ]
    else:
        filtered = filtered.iloc[0:0]

    if selected_names:
        filtered = filtered[
            filtered["Name"].isin(selected_names)
        ]
    else:
        filtered = filtered.iloc[0:0]

    return filtered


# ============================================================
# DISPLAY HELPERS
# ============================================================


# ============================================================
# DISPLAY HELPERS
# ============================================================

def format_number(value):
    if pd.isna(value):
        return "0"

    if isinstance(value, Number):
        number = float(value)

        if number.is_integer():
            return f"{int(number):,}"

        return f"{number:,.2f}".rstrip("0").rstrip(".")

    return str(value)


def format_number_columns(df, columns):
    output = df.copy()

    for column in columns:
        if column in output.columns:
            output[column] = output[column].map(format_number)

    return output


def show_table(df, numeric_columns=None, height=440):
    if df is None or df.empty:
        st.info("No data matches the selected filters.")
        return

    display_df = format_number_columns(
        df, numeric_columns or []
    )

    # Color the KPI status text
    if "Meet KPI" in display_df.columns:
        def color_status(value):
            status = str(value).strip().upper()

            if status == "YES":
                return "color: #15803D; font-weight: 800;"

            if status == "NO":
                return "color: #DC2626; font-weight: 800;"

            if status == "LEAVE":
                return "color: #D97706; font-weight: 800;"

            return ""

        styled_df = display_df.style.map(
            color_status,
            subset=["Meet KPI"],
        )

        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            height=height,
        )

    else:
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=height,
        )
# ============================================================
# MAIN APP
# ============================================================

st.markdown(
    '<div class="main-title">'
    'Daily Individual KPI'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# MODERN DASHBOARD STYLING
# ============================================================

st.markdown("""
<style>
/* Main page spacing */
.block-container {
    padding-top: 1.2rem !important;
    padding-bottom: 2rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 100% !important;
}

/* Page title */
.main-title {
    text-align: center;
    width: 100%;
    font-size: 2.3rem;
    font-weight: 800;
    color: #17365D;
    margin: 0.2rem 0 1.5rem 0;
    padding-bottom: 0.8rem;
    border-bottom: 3px solid #DCE6F1;
}

/* Section titles */
h2, h3 {
    color: #17365D !important;
    font-weight: 750 !important;
}

/* More spacing between Streamlit blocks */
div[data-testid="stVerticalBlock"] {
    gap: 0.8rem;
}

/* Buttons */
div[data-testid="stButton"] > button {
    border-radius: 9px;
    min-height: 40px;
    font-weight: 650;
    border: 1px solid #D5DFEA;
    transition: all 0.2s ease;
}

div[data-testid="stButton"] > button:hover {
    border-color: #2563EB;
    color: #2563EB;
}

/* Filter panel */
div[data-testid="stExpander"] {
    border: 1px solid #DCE6F1;
    border-radius: 12px;
    background: #FFFFFF;
}

/* Table container */
div[data-testid="stDataFrame"] {
    border: 1px solid #DCE6F1;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 3px 12px rgba(15, 23, 42, 0.06);
}

/* Divider between report sections */
hr {
    margin-top: 1.6rem !important;
    margin-bottom: 1.6rem !important;
    border-color: #DCE6F1 !important;
}

/* Info and warning boxes */
div[data-testid="stAlert"] {
    border-radius: 10px;
}

/* Footer */
small {
    color: #64748B;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# LOAD DATA
# ============================================================

try:
    with st.spinner("Loading Google Sheet data..."):
        all_data = load_all_data()

except Exception as error:
    st.error(
        "Unable to load Google Sheet data. "
        "Check Google Sheet permissions, column headings, "
        "and internet connection."
    )
    st.exception(error)
    st.stop()

if all_data.empty:
    st.warning(
        "No valid data found in the Google Sheets. "
        "Please check that the sheets are shared and contain data."
    )
    st.stop()


# ============================================================
# FILTERS
# ============================================================

filtered_data = render_shared_filter(all_data)

st.divider()

if filtered_data.empty:
    st.warning(
        "No data matches the selected Region, Date, and Name "
        "filters. Open the filters and select at least one option."
    )
    st.stop()


# ============================================================
# CREATE REPORT DATA
# ============================================================

summary_df = create_summary(filtered_data)
daily_total_df = create_daily_total(summary_df)
detail_df = create_daily_detail(filtered_data)


# ============================================================
# DAILY TOTAL — NO KPI CARDS
# ============================================================

st.subheader("Daily Total")

show_table(
    daily_total_df,
    numeric_columns=["Total"],
    height=280,
)

st.markdown("<div style='height: 28px'></div>",
            unsafe_allow_html=True)


# ============================================================
# DAILY SUMMARY
# ============================================================
st.subheader("Daily Summary")

summary_columns = (
    ["Date", "Region", "Name"]
    + SUMMARY_CATEGORIES
    + ["Total Count"]
)

summary_display = summary_df.reindex(
    columns=summary_columns
)

show_table(
    summary_display,
    numeric_columns=SUMMARY_CATEGORIES + ["Total Count"],
    height=420,
)

st.markdown("<div style='height: 28px'></div>",
            unsafe_allow_html=True)



# ============================================================
# CALCULATION RULES
# ============================================================


# ============================================================
# DAILY DETAIL
# ============================================================
st.subheader("Daily Detail")

show_table(
    detail_df,
    numeric_columns=[
        "Qty", "MAC Count", "Calculated Total"
    ],
    height=480,
)

# ============================================================
# FOOTER
# ============================================================

st.caption(
    "Data source: ENUO/HGAO sheet and MDY sheet. "
    "Data refresh cache: 20 seconds."
)
