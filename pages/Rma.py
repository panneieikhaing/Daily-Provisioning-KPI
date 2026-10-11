
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
    page_title="Daily Provisioning Regional KPI",
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
FILTER_SECTION = "daily_kpi"


# ============================================================
# KPI RULES
# ============================================================
CALCULATION_RULES = [
    ("RUN", "run", "MAC Count", "ALL"),
    ("Default", "default", "MAC Count", "ENUO_HGAO"),
    ("MAC / DBM", "mac/dbm", "MAC Count", "MDY"),
    ("DBM", "dbm", "Qty Sum", "ALL"),
    ("Cleaning", "cleaning", "Qty Sum", "ALL"),
    ("Speed Test", "speed test", "Qty Sum", "ALL"),
    ("Lan Port Test", "lan port test", "Qty Sum", "ALL"),
    ("RMA", "rma", "Qty Sum", "ALL"),
    ("Test RMA", "test rma", "Qty Sum", "ALL"),
    ("Accessories", "accessories", "Qty Sum", "ALL"),
    ("MAC", "mac", "Qty Sum", "ALL"),
    ("Exchange Test", "exchange test", "Qty Sum", "ALL"),
    ("Cover Change", "cover change", "Qty Sum", "ALL"),
    ("Infra", "infra", "Qty Sum", "ALL"),
]

SUMMARY_CATEGORIES = [r[0] for r in CALCULATION_RULES]


# ============================================================
# DESIGN
# ============================================================
st.markdown(
    """
    <style>
    :root {
        --navy: #17365D;
        --blue: #2563EB;
        --border: #DCE4EF;
        --muted: #64748B;
    }

    .stApp {
        background: #F5F7FB;
    }

    .block-container {
        max-width: 100% !important;
        padding-top: .55rem !important;
        padding-bottom: .7rem !important;
        padding-left: 1.3rem !important;
        padding-right: 1.3rem !important;
    }

    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 1rem !important;
    }

    .main-title {
        font-size: 29px;
        font-weight: 800;
        color: #17365D;
        line-height: 1.25;
        margin: 0 0 4px 0;
    }

    .subtitle {
        font-size: 12px;
        color: #64748B;
        margin-bottom: 8px;
    }

    div[data-testid="stVerticalBlock"] {
        gap: .45rem;
    }

    div[data-testid="stMarkdownContainer"] p {
        margin-bottom: .2rem;
    }

    h2, h3 {
        color: #17365D !important;
    }

    h2 {
        margin-top: .45rem !important;
    }

    /* Remove unwanted large white bordered containers */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: none !important;
        border-radius: 0 !important;
        background: transparent !important;
        box-shadow: none !important;
    }

    /* Filter buttons */
    div[data-testid="stButton"] > button {
        min-height: 39px;
        border: 1px solid #D5DFEC;
        border-radius: 9px;
        background: #FFFFFF;
        color: #17365D;
        font-weight: 650;
        transition: all .15s ease;
    }

    div[data-testid="stButton"] > button:hover {
        border-color: #93B4F5;
        color: #1D4ED8;
        background: #F8FBFF;
    }

    div[data-testid="stButton"] > button[kind="primary"] {
        background: #2563EB;
        color: white;
        border-color: #2563EB;
    }

    div[data-testid="stTextInput"] input {
        border-radius: 9px !important;
        border-color: #D7E0EC !important;
        background: #FFFFFF !important;
    }

    div[data-testid="stCheckbox"] label {
        font-size: 13px !important;
    }

    /* KPI cards */
    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E0E7F0;
        border-radius: 12px;
        padding: 12px 14px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, .035);
    }

    div[data-testid="stMetricLabel"] {
        color: #64748B !important;
        font-weight: 600;
    }

    div[data-testid="stMetricValue"] {
        color: #17365D !important;
        font-weight: 800;
    }

    /* Scrollable data tables */
    div[data-testid="stDataFrame"] {
        border: 1px solid #E0E7F0;
        border-radius: 10px;
        overflow: hidden;
        background: #FFFFFF;
    }

    div[data-testid="stDataFrame"] [role="grid"] {
        scrollbar-width: thin;
        scrollbar-color: #B8C7DA #F1F5F9;
    }

    div[data-testid="stExpander"] {
        border: 1px solid #E0E7F0;
        border-radius: 9px;
        background: transparent;
    }

    hr {
        border-color: #DCE4EF !important;
        margin: .4rem 0 !important;
    }

    .filter-label {
        color: #64748B;
        font-size: 12px;
        font-weight: 700;
        margin-bottom: 2px;
    }

    .filter-help {
        color: #64748B;
        font-size: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
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
        normalize_text(c).replace("_", " "): c
        for c in df.columns
    }

    for alias in aliases:
        key = normalize_text(alias).replace("_", " ")
        if key in lookup:
            return lookup[key]

    def simple(value):
        return re.sub(r"[^a-z0-9]", "", normalize_text(value))

    simple_lookup = {simple(c): c for c in df.columns}

    for alias in aliases:
        if simple(alias) in simple_lookup:
            return simple_lookup[simple(alias)]

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
# GOOGLE SHEET LOADER
# ============================================================
@st.cache_data(ttl=60, show_spinner=False)
def download_google_sheet(sheet_id, tab_name=""):
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

    return pd.read_csv(
        StringIO(response.text),
        dtype=str,
    )


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
    qty_col = find_column(
        df, ["Qty", "Quantity", "QTY"]
    )
    mac_col = find_column(
        df,
        [
            "MAC", "MAC Address", "MAC/SN",
            "MAC SN", "Serial Number", "SN",
        ],
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
            + ". Column headings ကို စစ်ပေးပါ။"
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

    result["Region"] = (
        clean_string_column(result["Region"]).str.upper()
    )
    result["Name"] = clean_string_column(result["Name"])
    result["Task Key"] = result["Daily (JD)"].map(normalize_task)

    return result[
        (result["Date"] != "")
        & (result["Daily (JD)"].str.strip() != "")
    ].copy()


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
# CALCULATION RULES
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

    return int(
        data["MAC"].astype(str).str.strip().ne("").sum()
    )


def calculate_category_value(data, category, region):
    rule = next(
        (r for r in CALCULATION_RULES if r[0] == category),
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

    return int(round(float(data["Qty"].sum())))


def find_rule_for_task(task_key, region):
    task_key = normalize_task(task_key)

    # Longer task matches first to prevent RMA matching Test RMA.
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
        ["Date", "Region", "Name"],
        dropna=False,
    ):
        row = {
            "Date": date,
            "Region": region,
            "Name": name,
        }

        for category in SUMMARY_CATEGORIES:
            rule = next(
                r for r in CALCULATION_RULES
                if r[0] == category
            )

            matching = group[
                group["Task Key"].map(
                    lambda value:
                    normalize_task(rule[1])
                    in normalize_task(value)
                )
            ]

            if category == "RMA":
                matching = matching[
                    ~matching["Task Key"].map(
                        lambda value:
                        "test rma" in normalize_task(value)
                    )
                ]

            if category == "MAC / DBM":
                matching = group[
                    group["Task Key"].map(
                        lambda value:
                        "mac/dbm" in normalize_task(value)
                        or "mac dbm" in normalize_task(value)
                    )
                ]

            row[category] = calculate_category_value(
                matching,
                category,
                region,
            )

        row["Total Count"] = sum(
            row[category] for category in SUMMARY_CATEGORIES
        )

        rows.append(row)

    return pd.DataFrame(rows, columns=columns)


def create_daily_total(summary):
    columns = ["Date", "Name", "Total"]

    if summary.empty:
        return pd.DataFrame(columns=columns)

    total = summary.groupby(
        ["Date", "Name"],
        as_index=False,
        dropna=False,
    )["Total Count"].sum()

    return total.rename(
        columns={"Total Count": "Total"}
    )


def create_daily_detail(data):
    columns = [
        "Date", "Region", "Name", "Device Name",
        "Daily (JD)", "Qty", "MAC Count", "Calculated Total",
    ]

    if data.empty:
        return pd.DataFrame(columns=columns)

    rows = []

    keys = [
        "Date", "Region", "Name",
        "Device Name", "Daily (JD)",
    ]

    for values, group in data.groupby(
        keys,
        dropna=False,
    ):
        date, region, name, device, daily = values

        rule = find_rule_for_task(daily, region)
        mac_count = count_nonblank_mac(group)
        qty_sum = int(round(float(group["Qty"].sum())))

        if rule is None:
            calculated = qty_sum
        elif rule[2] == "MAC Count":
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

    return pd.DataFrame(
        rows,
        columns=columns,
    ).sort_values(
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
            # Default date: newest date
            st.session_state[selected_key] = [options[0]]
        else:
            st.session_state[selected_key] = list(options)

    st.session_state[selected_key] = [
        value
        for value in st.session_state[selected_key]
        if value in options
    ]

    if draft_key not in st.session_state:
        st.session_state[draft_key] = list(
            st.session_state[selected_key]
        )
    else:
        st.session_state[draft_key] = [
            value
            for value in st.session_state[draft_key]
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
                filter_state_key(dimension, "selected"),
                [],
            )
        )


def apply_filter(dimension):
    st.session_state[
        filter_state_key(dimension, "selected")
    ] = list(
        st.session_state.get(
            filter_state_key(dimension, "draft"),
            [],
        )
    )

    st.session_state[
        filter_state_key(dimension, "open")
    ] = False


def cancel_filter(dimension):
    st.session_state[
        filter_state_key(dimension, "draft")
    ] = list(
        st.session_state.get(
            filter_state_key(dimension, "selected"),
            [],
        )
    )

    st.session_state[
        filter_state_key(dimension, "open")
    ] = False


# ============================================================
# CHECKBOX DROPDOWN FILTER
# Search + Select All + Scroll + Apply + Cancel
# ============================================================
def render_one_filter(dimension, label, options):
    initialize_filter_state(dimension, options)

    open_key = filter_state_key(dimension, "open")
    draft_key = filter_state_key(dimension, "draft")
    selected_key = filter_state_key(dimension, "selected")

    selected = st.session_state[selected_key]

    if not selected:
        button_text = f"No {label} Selected"
    elif len(selected) == len(options):
        button_text = (
            "All Dates" if dimension == "Date"
            else f"All {label}s"
        )
    elif dimension == "Date" and len(selected) == 1:
        button_text = selected[0]
    elif len(selected) == 1:
        button_text = selected[0]
    else:
        button_text = f"{len(selected)} selected"

    st.markdown(
        f'<div class="filter-label">{label}</div>',
        unsafe_allow_html=True,
    )

    st.button(
        f"{button_text}  ▾",
        key=filter_state_key(dimension, "button"),
        use_container_width=True,
        on_click=toggle_filter_panel,
        args=(dimension,),
    )

    if st.session_state.get(open_key, False):

        search = st.text_input(
            f"Search {label}",
            key=filter_state_key(dimension, "search"),
            placeholder=f"🔍 Search {label.lower()}...",
            label_visibility="collapsed",
        ).strip().casefold()

        visible_options = [
            value for value in options
            if search in str(value).casefold()
        ]

        selected_visible = sum(
            value in st.session_state[draft_key]
            for value in visible_options
        )

        st.caption(
            f"{selected_visible} of {len(visible_options)} options selected"
        )

        col_all, col_clear = st.columns(2)

        if col_all.button(
            "Select All",
            key=filter_state_key(dimension, "all"),
            use_container_width=True,
        ):
            current = list(st.session_state[draft_key])

            st.session_state[draft_key] = list(
                dict.fromkeys(current + visible_options)
            )

            st.rerun()

        if col_clear.button(
            "Clear All",
            key=filter_state_key(dimension, "clear"),
            use_container_width=True,
        ):
            st.session_state[draft_key] = [
                value
                for value in st.session_state[draft_key]
                if value not in visible_options
            ]

            st.rerun()

        # Scrollable list for long option lists
        with st.container(height=220, border=False):
            for index, option in enumerate(visible_options):
                checkbox_key = filter_state_key(
                    dimension,
                    f"check_{index}_{abs(hash(option))}",
                )

                checked = option in st.session_state[draft_key]

                new_checked = st.checkbox(
                    str(option),
                    value=checked,
                    key=checkbox_key,
                )

                draft_values = list(
                    st.session_state[draft_key]
                )

                if new_checked and option not in draft_values:
                    draft_values.append(option)
                    st.session_state[draft_key] = draft_values

                elif not new_checked and option in draft_values:
                    draft_values.remove(option)
                    st.session_state[draft_key] = draft_values

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


def render_shared_filter(data):
    st.subheader("Filters")
    st.caption(
        "Search and select values. Click Apply to update the dashboard."
    )

    region_options = filter_options(data, "Region")
    date_options = filter_options(data, "Date")
    name_options = filter_options(data, "Name")

    col_region, col_date, col_name = st.columns(
        [1, 1, 1],
        gap="medium",
    )

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

    numeric_columns = numeric_columns or []

    display_df = format_number_columns(
        df,
        numeric_columns,
    )

    # Scroll vertically and horizontally for large datasets
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
    '<div class="main-title">Daily Provisioning Regional KPI</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'Regional operations overview · Region / Date / Name filters'
    '</div>',
    unsafe_allow_html=True,
)

refresh_col, _ = st.columns([1, 5])

with refresh_col:
    if st.button(
        "↻ Refresh Data",
        key="refresh_data",
    ):
        st.cache_data.clear()
        st.rerun()


# Load source data
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
        "No valid data found. Please check Google Sheet "
        "permissions and source data."
    )
    st.stop()


# FILTERS
filtered_data = render_shared_filter(all_data)

st.divider()

if filtered_data.empty:
    st.warning(
        "No data matches the selected Region, Date, and Name. "
        "Open the filters, select values, and click Apply."
    )
    st.stop()


# CALCULATIONS
summary_df = create_summary(filtered_data)
daily_total_df = create_daily_total(summary_df)
detail_df = create_daily_detail(filtered_data)


# ============================================================
# DAILY TOTAL
# ============================================================
st.subheader("Daily Total")

metric_cols = st.columns(4)

metric_cols[0].metric(
    "Total Records",
    f"{len(filtered_data):,}",
)

metric_cols[1].metric(
    "Total Qty",
    format_number(filtered_data["Qty"].sum()),
)

metric_cols[2].metric(
    "MAC Count",
    f"{count_nonblank_mac(filtered_data):,}",
)

metric_cols[3].metric(
    "People",
    f"{filtered_data['Name'].replace('', pd.NA).nunique():,}",
)

show_table(
    daily_total_df,
    numeric_columns=["Total"],
    height=280,
)


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


# ============================================================
# CALCULATION RULES
# ============================================================
with st.expander("View Calculation Rules"):

    rules_df = pd.DataFrame(
        CALCULATION_RULES,
        columns=[
            "Category",
            "Task Match",
            "Calculation",
            "Applicable Region",
        ],
    )

    st.dataframe(
        rules_df,
        use_container_width=True,
        hide_index=True,
        height=350,
    )

    st.caption(
        "MAC Count = count of non-empty MAC values. "
        "Qty Sum = sum of Qty values. "
        "Region restrictions are applied as shown above."
    )


# ============================================================
# DAILY DETAIL
# ============================================================
st.subheader("Daily Detail")

show_table(
    detail_df,
    numeric_columns=[
        "Qty",
        "MAC Count",
        "Calculated Total",
    ],
    height=480,
)


# FOOTER
st.caption(
    "Data source: ENUO/HGAO sheet and MDY sheet "
    "· Data refresh cache: 60 seconds."
)