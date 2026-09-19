from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st
from analytics.customer_analytics import run_customer_analytics
from analytics.insights import run_insight_engine
from analytics.metrics import calculate_all_metrics
from analytics.product_analytics import run_product_analytics
from analytics.regional_analytics import run_regional_analytics
from analytics.segmentation import run_customer_segmentation
from database.database import (
    create_database_engine,
    test_database_connection,
)
from database.indexes import create_indexes
from database.schema import (
    get_table_columns,
    get_table_row_count,
    load_dataframe_to_database,
)
from etl.cleaner import clean_dataset
from etl.column_mapper import (
    apply_mapping,
    build_initial_mapping,
    create_mapping_dict,
    get_available_canonical_fields,
    validate_mapping,
)
from etl.feature_engineering import engineer_features
from etl.loader import (
    DataLoadError,
    get_dataset_summary,
    load_csv,
    load_sample_dataset,
)
from etl.profiler import profile_dataset
from etl.schema_detector import detect_schema
from etl.transformer import transform_dataset
from etl.validator import validate_dataset

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Adaptive E-Commerce Analytics",
    page_icon="📊",
    layout="wide",
)

# ============================================================
# THEME / APPEARANCE
# ============================================================

def get_theme() -> str:
    """Return the selected dashboard theme."""
    return st.session_state.get("theme", "Light")


def apply_theme() -> None:
    """
    Apply a professional desktop theme.

    Dark mode intentionally uses soft charcoal/slate surfaces rather
    than pure black or strong navy. This keeps the dashboard readable
    and visually close to a professional analytics application.
    """
    is_dark = get_theme() == "Dark"

    # Plotly follows the selected theme.
    px.defaults.template = (
        "plotly_dark" if is_dark else "plotly_white"
    )

    if is_dark:
        st.markdown(
            """
            <style>
            :root {
                --app-bg: #111318;
                --sidebar-bg: #25262E;
                --surface: #1C1E24;
                --surface-2: #20232A;
                --input-bg: #2A2D34;
                --border: #363942;
                --text: #F1F3F5;
                --muted: #A9ADB6;
                --hover: #30333B;
            }

            /* Main application */
            .stApp,
            [data-testid="stAppViewContainer"],
            [data-testid="stMain"] {
                background-color: var(--app-bg) !important;
                color: var(--text) !important;
            }

            .main .block-container {
                background-color: var(--app-bg) !important;
                color: var(--text) !important;
                padding-top: 2rem;
            }

            /* Sidebar */
            section[data-testid="stSidebar"],
            section[data-testid="stSidebar"] > div {
                background-color: var(--sidebar-bg) !important;
            }

            section[data-testid="stSidebar"] {
                border-right: 1px solid var(--border);
            }

            section[data-testid="stSidebar"] * {
                color: var(--text) !important;
            }

            section[data-testid="stSidebar"]
            [data-testid="stCaptionContainer"] * {
                color: var(--muted) !important;
            }

            /* Text */
            h1, h2, h3, h4, h5, h6,
            p, label {
                color: var(--text) !important;
            }

            [data-testid="stCaptionContainer"],
            [data-testid="stCaptionContainer"] p {
                color: var(--muted) !important;
            }

            /* Dividers */
            hr {
                border-color: var(--border) !important;
            }

            /* KPI cards */
            [data-testid="stMetric"] {
                background-color: var(--surface-2) !important;
                border: 1px solid var(--border) !important;
                border-radius: 10px !important;
                padding: 14px !important;
            }

            [data-testid="stMetricLabel"] {
                color: var(--muted) !important;
            }

            [data-testid="stMetricValue"] {
                color: var(--text) !important;
            }

            /* Select boxes */
            div[data-baseweb="select"] > div {
                background-color: var(--input-bg) !important;
                color: var(--text) !important;
                border-color: var(--border) !important;
            }

            div[data-baseweb="select"] * {
                color: var(--text) !important;
            }

            /* Text inputs */
            input,
            textarea {
                background-color: var(--input-bg) !important;
                color: var(--text) !important;
                border-color: var(--border) !important;
            }

            /* ==================================================
               FILE UPLOADER
               Fix the white uploader seen in dark mode.
               ================================================== */

            [data-testid="stFileUploader"] {
                background-color: transparent !important;
                border: none !important;
            }

            [data-testid="stFileUploaderDropzone"] {
                background-color: #2A2D34 !important;
                border: 1px solid #454851 !important;
                border-radius: 9px !important;
            }

            [data-testid="stFileUploaderDropzone"] * {
                color: #F1F3F5 !important;
            }

            [data-testid="stFileUploaderDropzone"] small {
                color: #A9ADB6 !important;
            }

            [data-testid="stFileUploaderDropzone"] button {
                background-color: #343740 !important;
                color: #F1F3F5 !important;
                border: 1px solid #4A4D55 !important;
                border-radius: 7px !important;
            }

            [data-testid="stFileUploaderDropzone"] button:hover {
                background-color: #3B3E47 !important;
            }

            /* Uploaded file container */
            [data-testid="stFileUploader"] section {
                background-color: #2A2D34 !important;
                border-color: #454851 !important;
            }

            /* Buttons */
            .stButton > button {
                background-color: var(--surface-2) !important;
                color: var(--text) !important;
                border: 1px solid var(--border) !important;
                border-radius: 8px !important;
            }

            .stButton > button:hover {
                background-color: var(--hover) !important;
            }

            /* Expanders */
            [data-testid="stExpander"] {
                background-color: var(--surface) !important;
                border: 1px solid var(--border) !important;
                border-radius: 8px !important;
            }

            /* Dataframes */
            [data-testid="stDataFrame"] {
                border: 1px solid var(--border) !important;
                border-radius: 8px !important;
            }

            /* Radio controls */
            div[role="radiogroup"] label {
                color: var(--text) !important;
            }

            /* Alerts */
            div[data-testid="stAlert"] {
                border-radius: 8px !important;
            }

            /* Links */
            a {
                color: #AFC7FF !important;
            }

            /* ==================================================
               PROFESSIONAL ACTION BUTTONS
               Muted blue primary action, restrained green
               success action, no bright multi-color palette.
               ================================================== */

            button[kind="primary"],
            button[data-testid="baseButton-primary"] {
                background-color: #2F6FED !important;
                color: #FFFFFF !important;
                border: 1px solid #4B82F5 !important;
                border-radius: 7px !important;
                font-weight: 600 !important;
            }

            button[kind="primary"]:hover,
            button[data-testid="baseButton-primary"]:hover {
                background-color: #3B78EA !important;
                border-color: #6A98F7 !important;
            }

            /* Standard secondary buttons */
            button[kind="secondary"],
            button[data-testid="baseButton-secondary"] {
                background-color: #252932 !important;
                color: #E7E9ED !important;
                border: 1px solid #454953 !important;
                border-radius: 7px !important;
            }

            button[kind="secondary"]:hover,
            button[data-testid="baseButton-secondary"]:hover {
                background-color: #30343D !important;
                border-color: #5A5F69 !important;
            }

            /* Selected radio controls: professional blue rather
               than Streamlit's default red accent. */
            section[data-testid="stSidebar"] input[type="radio"] {
                accent-color: #4B82F5 !important;
            }

            /* Progress */
            [data-testid="stProgress"] > div > div > div {
                background-color: #4B82F5 !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

    else:
        st.markdown(
            """
            <style>
            .stApp,
            [data-testid="stAppViewContainer"],
            [data-testid="stMain"] {
                background-color: #FFFFFF !important;
                color: #172033 !important;
            }

            .main .block-container {
                background-color: #FFFFFF !important;
                color: #172033 !important;
                padding-top: 2rem;
            }

            section[data-testid="stSidebar"] {
                background-color: #F5F7FA !important;
            }

            [data-testid="stMetric"] {
                border-radius: 10px !important;
            }

            [data-testid="stFileUploaderDropzone"] {
                border-radius: 9px !important;
            }

            button[kind="primary"],
            button[data-testid="baseButton-primary"] {
                background-color: #2F6FED !important;
                color: #FFFFFF !important;
                border-color: #2F6FED !important;
                border-radius: 7px !important;
                font-weight: 600 !important;
            }

            section[data-testid="stSidebar"] input[type="radio"] {
                accent-color: #2F6FED !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )


def display_appearance_selector() -> None:
    """Display the Light/Dark mode selector."""
    current_theme = get_theme()

    selected_theme = st.sidebar.radio(
        "Appearance",
        ["Light", "Dark"],
        index=0 if current_theme == "Light" else 1,
        format_func=lambda value: (
            "☀️ Light Mode"
            if value == "Light"
            else "🌙 Dark Mode"
        ),
        key="appearance_selector",
    )

    if selected_theme != current_theme:
        st.session_state["theme"] = selected_theme
        st.rerun()


if "theme" not in st.session_state:
    st.session_state["theme"] = "Light"

apply_theme()


# ============================================================
# DASHBOARD NAVIGATION
# ============================================================

def get_dashboard_section() -> str:
    """
    Return the dashboard section selected by the user.
    """
    return st.sidebar.radio(
        "Dashboard Section",
        [
            "Data Pipeline",
            "Business Overview",
            "Products",
            "Customers",
            "Regions",
            "Insights",
            "Data Explorer",
            "Dataset Information",
        ],
    )


def display_sidebar_header() -> None:
    """
    Display project information in the sidebar.
    """

    st.sidebar.title(
        "E-Commerce Intelligence"
    )

    st.sidebar.caption(
        "Adaptive Analytics & ETL Platform"
    )

    st.sidebar.divider()

def display_dashboard_header() -> None:
    """
    Display the main dashboard heading.
    """

    st.title(
        "Adaptive E-Commerce Analytics"
    )

    st.caption(
        "Transform heterogeneous transaction data "
        "into validated analytics and business insights."
    )


# ============================================================
# CONSTANTS
# ============================================================

SAMPLE_DATASET_NAME = "Use Sample Dataset"
UPLOAD_DATASET_NAME = "Upload CSV"

PIPELINE_STATE_KEYS = [
    "dataset",
    "dataset_signature",
    "profile",
    "schema_detection",
    "initial_mapping",
    "confirmed_mapping",
    "mapping",
    "canonical_df",
    "canonical_dataframe",
    "validation",
    "cleaned_df",
    "cleaned_dataframe",
    "cleaning_report",
    "transformed_df",
    "transformed_dataframe",
    "transformation_report",
    "featured_df",
    "featured_dataframe",
    "feature_report",
    "database_engine",
    "database_report",
    "index_report",
    "metrics",
    "product_analytics",
    "customer_analytics",
    "regional_analytics",
    "customer_segmentation",
    "business_insights",
]


# ============================================================
# SESSION STATE MANAGEMENT
# ============================================================

def clear_pipeline_state() -> None:
    """
    Clear all dataset-specific and downstream pipeline state.
    This prevents stale results from a previous dataset.
    """

    for key in PIPELINE_STATE_KEYS:
        st.session_state.pop(key, None)

    mapping_keys = [
        key
        for key in list(st.session_state.keys())
        if str(key).startswith("mapping_")
    ]

    for key in mapping_keys:
        st.session_state.pop(key, None)


def get_dataset_signature(
    dataset_source: str,
    uploaded_file=None,
) -> str:
    """
    Create a dataset signature.

    For uploaded files, the content is hashed so that two files
    with the same filename and size are still treated separately.
    """

    if dataset_source == SAMPLE_DATASET_NAME:
        return "sample_dataset"

    if uploaded_file is None:
        return "upload_none"

    try:
        file_bytes = uploaded_file.getvalue()
        content_hash = hashlib.md5(file_bytes).hexdigest()

        return (
            f"{uploaded_file.name}|"
            f"{uploaded_file.size}|"
            f"{content_hash}"
        )

    except Exception:
        return (
            f"{uploaded_file.name}|"
            f"{uploaded_file.size}"
        )


def handle_dataset_change(
    dataset_signature: str,
) -> None:
    """
    Reset the pipeline when the selected dataset changes.
    """

    previous_signature = st.session_state.get(
        "dataset_signature"
    )

    if (
        previous_signature is not None
        and previous_signature != dataset_signature
    ):
        clear_pipeline_state()

    st.session_state["dataset_signature"] = dataset_signature


def invalidate_downstream_from_mapping() -> None:
    """
    Clear everything after the mapping stage.
    """

    downstream_keys = [
        "validation",
        "cleaned_df",
        "cleaned_dataframe",
        "cleaning_report",
        "transformed_df",
        "transformed_dataframe",
        "transformation_report",
        "featured_df",
        "featured_dataframe",
        "feature_report",
        "database_engine",
        "database_report",
        "index_report",
        "metrics",
        "product_analytics",
        "customer_analytics",
        "regional_analytics",
        "customer_segmentation",
        "business_insights",
    ]

    for key in downstream_keys:
        st.session_state.pop(key, None)


def invalidate_downstream_from_cleaning() -> None:
    """
    Clear everything after the cleaning stage.
    """

    downstream_keys = [
        "transformed_df",
        "transformed_dataframe",
        "transformation_report",
        "featured_df",
        "featured_dataframe",
        "feature_report",
        "database_engine",
        "database_report",
        "index_report",
        "metrics",
        "product_analytics",
        "customer_analytics",
        "regional_analytics",
        "customer_segmentation",
        "business_insights",
    ]

    for key in downstream_keys:
        st.session_state.pop(key, None)


def invalidate_downstream_from_transformation() -> None:
    """
    Clear everything after transformation.
    """

    downstream_keys = [
        "featured_df",
        "featured_dataframe",
        "feature_report",
        "database_engine",
        "database_report",
        "index_report",
        "metrics",
        "product_analytics",
        "customer_analytics",
        "regional_analytics",
        "customer_segmentation",
        "business_insights",
    ]

    for key in downstream_keys:
        st.session_state.pop(key, None)


def invalidate_downstream_from_features() -> None:
    """
    Clear database and analytics after feature engineering.
    """

    downstream_keys = [
        "database_engine",
        "database_report",
        "index_report",
        "metrics",
        "product_analytics",
        "customer_analytics",
        "regional_analytics",
        "customer_segmentation",
        "business_insights",
    ]

    for key in downstream_keys:
        st.session_state.pop(key, None)


# ============================================================
# DISPLAY HELPERS
# ============================================================

def apply_chart_theme(fig):
    """Make Plotly chart surfaces blend into the selected theme."""
    is_dark = get_theme() == "Dark"

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            color="#F1F3F5" if is_dark else "#172033"
        ),
    )

    return fig



def display_dataset_summary(df: pd.DataFrame) -> None:
    summary = get_dataset_summary(df)

    st.subheader("Dataset Summary")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Rows",
            f"{summary['rows']:,}",
        )

    with col2:
        st.metric(
            "Columns",
            summary["columns"],
        )


def display_dataset_preview(df: pd.DataFrame) -> None:
    st.subheader("Dataset Preview")

    st.dataframe(
        df.head(20),
        use_container_width=True,
        hide_index=True,
    )


def display_profile(df: pd.DataFrame) -> None:
    st.subheader("Dataset Profile")

    profile = profile_dataset(df)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Rows",
            f"{profile['row_count']:,}",
        )

    with col2:
        st.metric(
            "Columns",
            profile["column_count"],
        )

    with col3:
        st.metric(
            "Missing Values",
            f"{profile['missing_value_count']:,}",
        )

    with col4:
        st.metric(
            "Duplicate Rows",
            f"{profile['duplicate_row_count']:,}",
        )

    st.write("### Column Profile")

    st.dataframe(
        profile["column_profile"],
        use_container_width=True,
        hide_index=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**Numeric Columns**")
        st.write(profile["numeric_columns"])

    with col2:
        st.write("**Categorical Columns**")
        st.write(profile["categorical_columns"])

    with col3:
        st.write("**Date Columns**")
        st.write(profile["date_columns"])


def display_schema_detection(df: pd.DataFrame) -> None:
    st.subheader("Schema Detection")

    schema = detect_schema(df)

    st.dataframe(
        schema,
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Confidence: High ≥ 90%, Medium ≥ 70%, Low < 70%"
    )


# ============================================================
# COLUMN MAPPING
# ============================================================

def display_mapping_editor(df: pd.DataFrame) -> None:
    st.subheader("Column Mapping")

    st.caption(
        "Required fields are mapped first. Optional fields are used "
        "automatically when available."
    )

    if "initial_mapping" not in st.session_state:
        st.session_state["initial_mapping"] = (
            build_initial_mapping(df)
        )

    initial_mapping = st.session_state["initial_mapping"]
    canonical_fields = get_available_canonical_fields()

    edited_records = []

    for _, row in initial_mapping.iterrows():
        source_column = row["source_column"]
        detected_field = row["canonical_field"]

        options = [
            "Do not map",
            *canonical_fields,
        ]

        if detected_field in canonical_fields:
            default_index = options.index(detected_field)
        else:
            default_index = 0

        selected_field = st.selectbox(
            f"{source_column}",
            options=options,
            index=default_index,
            key=f"mapping_{source_column}",
        )

        if selected_field == "Do not map":
            selected_field = None

        edited_records.append(
            {
                "source_column": source_column,
                "canonical_field": selected_field,
                "confidence": row["confidence"],
                "confidence_percent": row["confidence_percent"],
                "confidence_level": row["confidence_level"],
                "match_reason": row["match_reason"],
            }
        )

    edited_mapping = pd.DataFrame(edited_records)

    st.write("### Current Mapping")

    st.dataframe(
        edited_mapping,
        use_container_width=True,
        hide_index=True,
    )

    if st.button(
        "Confirm Mapping",
        type="primary",
        key="confirm_mapping_button",
    ):
        confirmed_rows = edited_mapping[
            edited_mapping["canonical_field"].notna()
        ].copy()

        is_valid, errors = validate_mapping(
            confirmed_rows
        )

        if not is_valid:
            st.error("Mapping validation failed.")

            for error in errors:
                st.error(error)

            return

        try:
            mapping = create_mapping_dict(
                confirmed_rows
            )

            canonical_df = apply_mapping(
                df,
                mapping,
            )

        except Exception as error:
            st.error(f"Mapping failed: {error}")
            return

        invalidate_downstream_from_mapping()

        st.session_state["confirmed_mapping"] = mapping
        st.session_state["canonical_dataframe"] = canonical_df

        st.success(
            "Column mapping confirmed successfully."
        )

        st.write("### Canonical Dataset Preview")

        st.dataframe(
            canonical_df.head(20),
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# VALIDATION
# ============================================================

def display_validation_report(
    df: pd.DataFrame,
    mapping: dict[str, str] | None,
) -> None:
    st.subheader("Data Quality Validation")

    try:
        validation = validate_dataset(
            df,
            mapping=mapping,
        )
    except Exception as error:
        st.error(f"Validation failed: {error}")
        return

    st.session_state["validation"] = validation

    score = validation["quality_score"]

    st.metric(
        "Data Quality Score",
        f"{score}/100",
    )

    st.progress(
        min(max(int(score), 0), 100) / 100
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Errors",
            validation["error_count"],
        )

    with col2:
        st.metric(
            "Warnings",
            validation["warning_count"],
        )

    with col3:
        st.metric(
            "Info",
            validation["info_count"],
        )

    with col4:
        st.metric(
            "Exact Duplicates",
            validation["duplicates"][
                "exact_duplicate_count"
            ],
        )

    if validation["issues"]:
        st.write("### Validation Issues")

        issues_df = pd.DataFrame(
            validation["issues"]
        )

        st.dataframe(
            issues_df,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.success(
            "No data quality issues were detected."
        )

    if validation["penalties"]:
        st.write("### Score Explanation")

        penalty_df = pd.DataFrame(
            validation["penalties"]
        )

        st.dataframe(
            penalty_df,
            use_container_width=True,
            hide_index=True,
        )

    with st.expander(
        "View detailed validation statistics"
    ):
        st.write("### Missing Values")

        st.json(
            validation["values"][
                "missing_by_column"
            ]
        )

        st.write("### Duplicate Analysis")

        st.json(validation["duplicates"])

        st.write("### Schema Analysis")

        st.json(
            {
                "missing_required_fields":
                    validation["schema"][
                        "missing_required_fields"
                    ],
                "available_price_fields":
                    validation["schema"][
                        "available_price_fields"
                    ],
                "unmapped_columns":
                    validation["schema"][
                        "unmapped_columns"
                    ],
            }
        )


# ============================================================
# CLEANING
# ============================================================

def display_cleaning_section(
    canonical_df: pd.DataFrame,
) -> None:
    st.subheader("Data Cleaning")

    if st.button(
        "Run Data Cleaning",
        type="primary",
        key="run_cleaning_button",
    ):
        try:
            cleaned_df, cleaning_report = clean_dataset(
                canonical_df
            )

            invalidate_downstream_from_cleaning()

            st.session_state["cleaned_dataframe"] = cleaned_df
            st.session_state["cleaning_report"] = cleaning_report

            st.success(
                "Data cleaning completed successfully."
            )

        except Exception as error:
            st.error(f"Data cleaning failed: {error}")

    if "cleaned_dataframe" not in st.session_state:
        st.info(
            "Click 'Run Data Cleaning' to continue."
        )
        return

    cleaned_df = st.session_state["cleaned_dataframe"]
    cleaning_report = st.session_state["cleaning_report"]

    st.write("### Cleaning Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Rows Before",
            f"{cleaning_report['rows_before']:,}",
        )

    with col2:
        st.metric(
            "Rows After",
            f"{cleaning_report['rows_after']:,}",
        )

    with col3:
        st.metric(
            "Rows Removed",
            f"{cleaning_report['rows_removed']:,}",
        )

    with col4:
        st.metric(
            "Missing Values After",
            f"{cleaning_report['missing_values_after']:,}",
        )

    st.write("### Cleaning Operations")

    steps_df = pd.DataFrame(
        cleaning_report["steps"]
    )

    st.dataframe(
        steps_df,
        use_container_width=True,
        hide_index=True,
    )

    st.write("### Cleaned Dataset Preview")

    st.dataframe(
        cleaned_df.head(20),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# TRANSFORMATION
# ============================================================

def display_transformation_section(
    cleaned_df: pd.DataFrame,
) -> None:
    st.subheader("Data Transformation")

    if st.button(
        "Run Data Transformation",
        type="primary",
        key="run_transformation_button",
    ):
        try:
            transformed_df, transformation_report = (
                transform_dataset(cleaned_df)
            )

            invalidate_downstream_from_transformation()

            st.session_state["transformed_dataframe"] = (
                transformed_df
            )
            st.session_state["transformation_report"] = (
                transformation_report
            )

            st.success(
                "Data transformation completed successfully."
            )

        except Exception as error:
            st.error(
                f"Data transformation failed: {error}"
            )

    if "transformed_dataframe" not in st.session_state:
        st.info(
            "Click 'Run Data Transformation' to continue."
        )
        return

    transformed_df = st.session_state[
        "transformed_dataframe"
    ]

    transformation_report = st.session_state[
        "transformation_report"
    ]

    st.write("### Transformation Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Rows",
            f"{transformation_report['rows_after']:,}",
        )

    with col2:
        st.metric(
            "Columns",
            transformation_report["columns_after"],
        )

    with col3:
        st.metric(
            "New Columns",
            transformation_report["new_column_count"],
        )

    st.write("### Transformation Operations")

    transformation_steps = pd.DataFrame(
        transformation_report["steps"]
    )

    st.dataframe(
        transformation_steps,
        use_container_width=True,
        hide_index=True,
    )

    st.write("### New Analytical Fields")

    st.write(
        transformation_report["new_columns"]
    )

    st.write("### Transformed Dataset Preview")

    st.dataframe(
        transformed_df.head(20),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# FEATURE ENGINEERING
# ============================================================

def display_feature_engineering_section(
    transformed_df: pd.DataFrame,
) -> None:
    st.subheader("Feature Engineering")
    st.caption(
        "Creates reusable analytical fields from the transformed dataset. "
        "Features are generated only when their required source fields exist."
    )

    if st.button(
        "Run Feature Engineering",
        type="primary",
        key="run_feature_button",
    ):
        try:
            featured_df, feature_report = engineer_features(
                transformed_df
            )

            invalidate_downstream_from_features()

            st.session_state["featured_dataframe"] = featured_df
            st.session_state["feature_report"] = feature_report

            st.success(
                "Feature engineering completed successfully."
            )

        except Exception as error:
            st.error(
                f"Feature engineering failed: {error}"
            )

    if "featured_dataframe" not in st.session_state:
        st.info(
            "Click 'Run Feature Engineering' to continue."
        )
        return

    featured_df = st.session_state[
        "featured_dataframe"
    ]

    feature_report = st.session_state[
        "feature_report"
    ]

    st.write("### Feature Engineering Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Rows",
            f"{feature_report['rows_after']:,}",
        )

    with col2:
        st.metric(
            "Columns",
            feature_report["columns_after"],
        )

    with col3:
        st.metric(
            "New Features",
            feature_report["new_column_count"],
        )

    st.write("### Feature Engineering Operations")

    feature_steps = pd.DataFrame(
        feature_report["steps"]
    )

    st.dataframe(
        feature_steps,
        use_container_width=True,
        hide_index=True,
    )

    st.write("### Generated Features")

    st.write(
        feature_report["new_columns"]
    )

    st.write("### Feature-Engineered Dataset")

    st.dataframe(
        featured_df.head(20),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# DATABASE
# ============================================================

def display_database_section(
    featured_df: pd.DataFrame,
) -> None:
    st.subheader("Database")

    if st.button(
        "Load Data into SQLite",
        type="primary",
        key="load_database_button",
    ):
        try:
            engine = create_database_engine()

            connection_ok = test_database_connection(
                engine
            )

            if not connection_ok:
                st.error(
                    "Database connection failed."
                )
                return

            database_report = (
                load_dataframe_to_database(
                    featured_df,
                    engine,
                )
            )

            index_report = create_indexes(
                engine
            )

            st.session_state["database_engine"] = engine
            st.session_state["database_report"] = database_report
            st.session_state["index_report"] = index_report

            st.session_state.pop("metrics", None)
            st.session_state.pop("product_analytics", None)
            st.session_state.pop("customer_analytics", None)
            st.session_state.pop("customer_segmentation", None)
            st.session_state.pop("business_insights", None)
            

            st.success(
                "Dataset loaded into SQLite successfully."
            )

        except Exception as error:
            st.error(
                f"Database loading failed: {error}"
            )

    if "database_report" not in st.session_state:
        st.info(
            "Click 'Load Data into SQLite' to continue."
        )
        return

    database_report = st.session_state["database_report"]
    engine = st.session_state["database_engine"]

    try:
        row_count = get_table_row_count(engine)
        columns = get_table_columns(engine)

    except Exception as error:
        st.error(
            f"Could not read database information: {error}"
        )
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Rows in Database",
            f"{row_count:,}",
        )

    with col2:
        st.metric(
            "Columns",
            database_report["columns_loaded"],
        )

    with col3:
        st.metric(
            "Table",
            database_report["table_name"],
        )

    st.write("### Database Columns")
    st.write(columns)

    st.write("### Database Indexes")
    st.write(
        st.session_state.get(
            "index_report",
            {},
        )
    )


# ============================================================
# BUSINESS METRICS
# ============================================================

def display_metrics_section() -> None:
    st.subheader("Business Metrics")

    if "database_engine" not in st.session_state:
        st.info(
            "Load the dataset into SQLite first."
        )
        return

    engine = st.session_state["database_engine"]

    try:
        metrics = calculate_all_metrics(engine)
        st.session_state["metrics"] = metrics

    except Exception as error:
        st.error(
            f"Metric calculation failed: {error}"
        )
        return

    st.write("### Key Performance Indicators")

    col1, col2, col3, col4 = st.columns(4)

    revenue = metrics.get("total_revenue")
    orders = metrics.get("total_orders")
    aov = metrics.get("average_order_value")
    quantity = metrics.get("total_quantity")

    with col1:
        st.metric(
            "Total Revenue",
            (
                f"{revenue:,.2f}"
                if revenue is not None
                else "N/A"
            ),
        )

    with col2:
        st.metric(
            "Total Orders",
            (
                f"{orders:,}"
                if orders is not None
                else "N/A"
            ),
        )

    with col3:
        st.metric(
            "Average Order Value",
            (
                f"{aov:,.2f}"
                if aov is not None
                else "N/A"
            ),
        )

    with col4:
        st.metric(
            "Units Sold",
            (
                f"{quantity:,.0f}"
                if quantity is not None
                else "N/A"
            ),
        )

    st.write("### Additional Metrics")

    col1, col2, col3, col4 = st.columns(4)

    customers = metrics.get("unique_customers")
    products = metrics.get("unique_products")
    profit = metrics.get("total_profit")
    margin = metrics.get("profit_margin")

    with col1:
        st.metric(
            "Unique Customers",
            (
                f"{customers:,}"
                if customers is not None
                else "N/A"
            ),
        )

    with col2:
        st.metric(
            "Unique Products",
            (
                f"{products:,}"
                if products is not None
                else "N/A"
            ),
        )

    with col3:
        st.metric(
            "Total Profit",
            (
                f"{profit:,.2f}"
                if profit is not None
                else "N/A"
            ),
        )

    with col4:
        st.metric(
            "Profit Margin",
            (
                f"{margin:.2f}%"
                if margin is not None
                else "N/A"
            ),
        )

    st.write("### Customer & Transaction Metrics")

    col1, col2, col3 = st.columns(3)

    repeat_rate = metrics.get("repeat_customer_rate")
    return_rate = metrics.get("return_rate")
    missing_rate = metrics.get("missing_value_rate")

    with col1:
        st.metric(
            "Repeat Customer Rate",
            (
                f"{repeat_rate:.2f}%"
                if repeat_rate is not None
                else "N/A"
            ),
        )

    with col2:
        st.metric(
            "Return Rate",
            (
                f"{return_rate:.2f}%"
                if return_rate is not None
                else "N/A"
            ),
        )

    with col3:
        st.metric(
            "Missing Value Rate",
            (
                f"{missing_rate:.2f}%"
                if missing_rate is not None
                else "N/A"
            ),
        )

    st.write("### All Calculated Metrics")

    metric_rows = [
        {
            "Metric": name,
            "Value": value,
        }
        for name, value in metrics.items()
    ]

    metrics_df = pd.DataFrame(metric_rows)

    st.dataframe(
        metrics_df,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# PRODUCT ANALYTICS
# ============================================================

def display_product_analytics_section() -> None:
    """
    Display product analytics AFTER business metrics.

    Product analytics is intentionally placed here so the
    Streamlit page follows the actual pipeline order:
    ETL -> Database -> Metrics -> Product Analytics.
    """

    st.subheader("Product Analytics")

    if "database_engine" not in st.session_state:
        st.info(
            "Load the dataset into SQLite first."
        )
        return

    if st.button(
        "Run Product Analytics",
        type="primary",
        key="run_product_analytics_button",
    ):
        try:
            with st.spinner(
                "Running product analytics..."
            ):
                product_results = run_product_analytics(
                    st.session_state["database_engine"],
                    limit=10,
                )

            st.session_state["product_analytics"] = (
                product_results
            )

            st.success(
                "Product analytics completed successfully."
            )

        except Exception as error:
            st.error(
                f"Product analytics failed: {error}"
            )
            return

    if "product_analytics" not in st.session_state:
        st.info(
            "Click 'Run Product Analytics' to generate "
            "product-level insights."
        )
        return

    product_results = st.session_state[
        "product_analytics"
    ]

    # --------------------------------------------------------
    # Top Products by Revenue
    # --------------------------------------------------------

    st.write("### Top Products by Revenue")

    revenue_df = product_results.get(
        "top_products_by_revenue"
    )

    if revenue_df is not None and not revenue_df.empty:
        st.dataframe(
            revenue_df,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info(
            "Product revenue data is not available "
            "for this dataset."
        )

    # --------------------------------------------------------
    # Top Products by Quantity
    # --------------------------------------------------------

    st.write("### Top Products by Quantity Sold")

    quantity_df = product_results.get(
        "top_products_by_quantity"
    )

    if quantity_df is not None and not quantity_df.empty:
        st.dataframe(
            quantity_df,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info(
            "Product quantity data is not available "
            "for this dataset."
        )

    # --------------------------------------------------------
    # Top Products by Profit
    # --------------------------------------------------------

    st.write("### Top Products by Profit")

    profit_df = product_results.get(
        "top_products_by_profit"
    )

    if profit_df is not None and not profit_df.empty:
        st.dataframe(
            profit_df,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info(
            "Profit information is not available "
            "in this dataset."
        )

    # --------------------------------------------------------
    # Category Performance
    # --------------------------------------------------------

    st.write("### Category Performance")

    category_df = product_results.get(
        "category_performance"
    )

    if category_df is not None and not category_df.empty:
        st.dataframe(
            category_df,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info(
            "Category information is not available "
            "in this dataset."
        )

    # --------------------------------------------------------
    # Product Revenue Contribution
    # --------------------------------------------------------

    st.write("### Product Revenue Contribution")

    contribution_df = product_results.get(
        "product_contribution"
    )

    if (
        contribution_df is not None
        and not contribution_df.empty
    ):
        st.dataframe(
            contribution_df,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info(
            "Product contribution cannot be calculated "
            "for this dataset."
        )

    # --------------------------------------------------------
    # Low-Performing Products
    # --------------------------------------------------------

    st.write("### Low-Performing Products")

    low_performing_df = product_results.get(
        "low_performing_products"
    )

    if (
        low_performing_df is not None
        and not low_performing_df.empty
    ):
        st.dataframe(
            low_performing_df,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info(
            "Low-performing product analysis "
            "is not available."
        )
    # ============================================================
# CUSTOMER ANALYTICS
# ============================================================

def display_customer_analytics_section() -> None:
    """
    Display customer-level analytics.

    Customer analytics is adaptive:
    - Uses customer_id when available.
    - Uses net_sales or sales_amount for revenue.
    - Gracefully handles datasets without customer information.
    """

    st.subheader("Customer Analytics")

    if "database_engine" not in st.session_state:
        st.info(
            "Load the dataset into SQLite first."
        )
        return

    if st.button(
        "Run Customer Analytics",
        type="primary",
        key="run_customer_analytics_button",
    ):
        try:

            with st.spinner(
                "Running customer analytics..."
            ):

                customer_results = (
                    run_customer_analytics(
                        st.session_state[
                            "database_engine"
                        ],
                        limit=10,
                    )
                )

            st.session_state[
                "customer_analytics"
            ] = customer_results

            st.success(
                "Customer analytics completed successfully."
            )

        except Exception as error:

            st.error(
                f"Customer analytics failed: {error}"
            )

            return

    if "customer_analytics" not in st.session_state:

        st.info(
            "Click 'Run Customer Analytics' to generate "
            "customer-level analysis."
        )

        return

    customer_results = st.session_state[
        "customer_analytics"
    ]

    # ========================================================
    # CUSTOMER SUMMARY
    # ========================================================

    st.write("### Customer Summary")

    customer_summary = customer_results.get(
        "customer_summary",
        {},
    )

    if not customer_summary.get(
        "customer_available",
        False,
    ):

        st.warning(
            "Customer-level analysis is not available "
            "because this dataset does not contain "
            "a customer identifier."
        )

    else:

        total_customers = customer_summary.get(
            "total_customers"
        )

        repeat_customers = customer_summary.get(
            "repeat_customers"
        )

        one_time_customers = customer_summary.get(
            "one_time_customers"
        )

        repeat_rate = customer_summary.get(
            "repeat_customer_rate"
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Customers",
                (
                    f"{total_customers:,}"
                    if total_customers is not None
                    else "N/A"
                ),
            )

        with col2:
            st.metric(
                "Repeat Customers",
                (
                    f"{repeat_customers:,}"
                    if repeat_customers is not None
                    else "N/A"
                ),
            )

        with col3:
            st.metric(
                "One-Time Customers",
                (
                    f"{one_time_customers:,}"
                    if one_time_customers is not None
                    else "N/A"
                ),
            )

        with col4:
            st.metric(
                "Repeat Customer Rate",
                (
                    f"{repeat_rate:.2f}%"
                    if repeat_rate is not None
                    else "N/A"
                ),
            )

    # ========================================================
    # CUSTOMER REVENUE
    # ========================================================

    st.write("### Top Customers by Revenue")

    revenue_df = customer_results.get(
        "customer_revenue"
    )

    if (
        revenue_df is not None
        and not revenue_df.empty
    ):

        st.dataframe(
            revenue_df,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "Customer revenue data is not available "
            "for this dataset."
        )

    # ========================================================
    # ORDER FREQUENCY
    # ========================================================

    st.write("### Customers by Order Frequency")

    frequency_df = customer_results.get(
        "customer_order_frequency"
    )

    if (
        frequency_df is not None
        and not frequency_df.empty
    ):

        st.dataframe(
            frequency_df,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "Customer order-frequency data is not available."
        )

    # ========================================================
    # CUSTOMER AOV
    # ========================================================

    st.write("### Customer Average Order Value")

    aov_df = customer_results.get(
        "customer_average_order_value"
    )

    if (
        aov_df is not None
        and not aov_df.empty
    ):

        st.dataframe(
            aov_df,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "Customer average-order-value data "
            "is not available."
        )

    # ========================================================
    # TOP CUSTOMERS
    # ========================================================

    st.write("### Top Customer Performance")

    top_customers_df = customer_results.get(
        "top_customers"
    )

    if (
        top_customers_df is not None
        and not top_customers_df.empty
    ):

        st.dataframe(
            top_customers_df,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "Top customer analysis is not available."
        )

    # ========================================================
    # REPEAT CUSTOMER ANALYSIS
    # ========================================================

    st.write("### One-Time vs Repeat Customers")

    repeat_df = customer_results.get(
        "repeat_customer_analysis"
    )

    if (
        repeat_df is not None
        and not repeat_df.empty
    ):

        st.dataframe(
            repeat_df,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "Repeat-customer analysis is not available."
        )

    # ========================================================
    # CUSTOMER CONTRIBUTION
    # ========================================================

    st.write("### Customer Revenue Contribution")

    contribution_df = customer_results.get(
        "customer_contribution"
    )

    if (
        contribution_df is not None
        and not contribution_df.empty
    ):

        st.dataframe(
            contribution_df.head(20),
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "Customer revenue contribution "
            "is not available."
        )
    # ============================================================
# REGIONAL ANALYTICS
# ============================================================

def display_regional_analytics_section() -> None:
    """
    Display geographic business analytics.

    Regional analytics adapts to the geographic fields
    available in the uploaded dataset.
    """

    st.subheader("Regional Analytics")

    if "database_engine" not in st.session_state:
        st.info(
            "Load the dataset into SQLite first."
        )
        return

    if st.button(
        "Run Regional Analytics",
        type="primary",
        key="run_regional_analytics_button",
    ):
        try:

            with st.spinner(
                "Running regional analytics..."
            ):

                regional_results = (
                    run_regional_analytics(
                        st.session_state[
                            "database_engine"
                        ],
                        limit=10,
                    )
                )

            st.session_state[
                "regional_analytics"
            ] = regional_results

            st.success(
                "Regional analytics completed successfully."
            )

        except Exception as error:

            st.error(
                f"Regional analytics failed: {error}"
            )

            return

    if "regional_analytics" not in st.session_state:

        st.info(
            "Click 'Run Regional Analytics' to generate "
            "geographic business analysis."
        )

        return

    regional_results = st.session_state[
        "regional_analytics"
    ]

    # ========================================================
    # REGION PERFORMANCE
    # ========================================================

    st.write("### Region Performance")

    region_df = regional_results.get(
        "region_performance"
    )

    if (
        region_df is not None
        and not region_df.empty
    ):

        st.dataframe(
            region_df,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "Regional information is not available "
            "in this dataset."
        )

    # ========================================================
    # REGIONAL CONTRIBUTION
    # ========================================================

    st.write("### Regional Revenue Contribution")

    contribution_df = regional_results.get(
        "regional_contribution"
    )

    if (
        contribution_df is not None
        and not contribution_df.empty
    ):

        st.dataframe(
            contribution_df,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "Regional revenue contribution "
            "is not available."
        )

    # ========================================================
    # TOP REGIONS
    # ========================================================

    st.write("### Top Regions by Revenue")

    top_regions_df = regional_results.get(
        "top_regions"
    )

    if (
        top_regions_df is not None
        and not top_regions_df.empty
    ):

        st.dataframe(
            top_regions_df,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "Top-region analysis is not available."
        )

    # ========================================================
    # LOW-PERFORMING REGIONS
    # ========================================================

    st.write("### Low-Performing Regions")

    low_regions_df = regional_results.get(
        "low_performing_regions"
    )

    if (
        low_regions_df is not None
        and not low_regions_df.empty
    ):

        st.dataframe(
            low_regions_df,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "Low-performing region analysis "
            "is not available."
        )

    # ========================================================
    # COUNTRY PERFORMANCE
    # ========================================================

    st.write("### Country Performance")

    country_df = regional_results.get(
        "country_performance"
    )

    if (
        country_df is not None
        and not country_df.empty
    ):

        st.dataframe(
            country_df,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "Country-level analysis is not available "
            "because this dataset does not contain "
            "a country field."
        )

    # ========================================================
    # CITY PERFORMANCE
    # ========================================================

    st.write("### City Performance")

    city_df = regional_results.get(
        "city_performance"
    )

    if (
        city_df is not None
        and not city_df.empty
    ):

        st.dataframe(
            city_df,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "City-level analysis is not available "
            "because this dataset does not contain "
            "a city field."
        )

    # ============================================================
# CUSTOMER SEGMENTATION / RFM
# ============================================================

def display_customer_segmentation_section() -> None:
    """
    Display RFM-based customer segmentation.

    The analysis adapts to the customer and revenue fields
    available in the loaded dataset.
    """

    st.subheader("Customer Segmentation — RFM Analysis")

    if "database_engine" not in st.session_state:
        st.info(
            "Load the dataset into SQLite first."
        )
        return

    if st.button(
        "Run Customer Segmentation",
        type="primary",
        key="run_customer_segmentation_button",
    ):
        try:
            with st.spinner(
                "Calculating RFM scores and customer segments..."
            ):
                segmentation_results = (
                    run_customer_segmentation(
                        st.session_state[
                            "database_engine"
                        ]
                    )
                )

            st.session_state[
                "customer_segmentation"
            ] = segmentation_results

            if segmentation_results.get("available"):
                st.success(
                    "Customer segmentation completed successfully."
                )
            else:
                st.warning(
                    segmentation_results.get(
                        "reason",
                        "Customer segmentation is unavailable.",
                    )
                )

        except Exception as error:
            st.error(
                f"Customer segmentation failed: {error}"
            )
            return

    if "customer_segmentation" not in st.session_state:
        st.info(
            "Click 'Run Customer Segmentation' to generate "
            "RFM-based customer segments."
        )
        return

    results = st.session_state[
        "customer_segmentation"
    ]

    if not results.get("available"):
        st.warning(
            results.get(
                "reason",
                "Customer segmentation is not available.",
            )
        )
        return

    # ========================================================
    # RFM SUMMARY
    # ========================================================

    st.write("### RFM Customer Analysis")

    rfm_df = results.get("rfm_scores")

    if rfm_df is not None and not rfm_df.empty:

        display_columns = [
            column
            for column in [
                "customer_id",
                "last_order_date",
                "recency",
                "frequency",
                "monetary",
                "r_score",
                "f_score",
                "m_score",
                "rfm_score",
                "rfm_code",
                "segment",
            ]
            if column in rfm_df.columns
        ]

        st.dataframe(
            rfm_df[display_columns],
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.info(
            "No customer-level RFM data is available."
        )

    # ========================================================
    # SEGMENT SUMMARY
    # ========================================================

    st.write("### Customer Segment Summary")

    segment_df = results.get(
        "segment_summary"
    )

    if segment_df is not None and not segment_df.empty:

        st.dataframe(
            segment_df,
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.info(
            "No customer segment summary is available."
        )

    # ========================================================
    # SEGMENT DISTRIBUTION
    # ========================================================

    if (
        rfm_df is not None
        and not rfm_df.empty
        and "segment" in rfm_df.columns
    ):

        st.write("### Customer Distribution by Segment")

        segment_counts = (
            rfm_df["segment"]
            .value_counts()
            .rename_axis("segment")
            .reset_index(
                name="customer_count"
            )
        )

        st.bar_chart(
            segment_counts.set_index(
                "segment"
            )
        )

    # ========================================================
    # REVENUE BY SEGMENT
    # ========================================================

    if (
        segment_df is not None
        and not segment_df.empty
        and "segment" in segment_df.columns
        and "total_revenue" in segment_df.columns
    ):

        st.write("### Revenue by Customer Segment")

        revenue_chart = segment_df[
            [
                "segment",
                "total_revenue",
            ]
        ].copy()

        revenue_chart = revenue_chart.set_index(
            "segment"
        )

        st.bar_chart(
            revenue_chart
        )

    # ========================================================
    # RFM EXPLANATION
    # ========================================================

    with st.expander(
        "What do the RFM metrics mean?"
    ):
        st.markdown(
            """
            **Recency**
            
            Number of days since the customer's most
            recent purchase. Lower values indicate
            more recent activity.

            **Frequency**
            
            Number of orders placed by the customer.

            **Monetary**
            
            Total revenue generated by the customer.

            **RFM Score**
            
            Combined score based on Recency, Frequency
            and Monetary values.

            **RFM Code**
            
            Three-digit representation of the individual
            R, F and M scores.

            **Customer Segment**
            
            An interpretable grouping based on the
            customer's RFM characteristics.
            """
        )
    # ============================================================
# BUSINESS INSIGHT ENGINE
# ============================================================

def display_business_insights_section() -> None:
    """
    Display data-driven business insights generated from
    the currently loaded SQLite dataset.
    """

    st.subheader("Business Insight Engine")

    if "database_engine" not in st.session_state:
        st.info(
            "Load the dataset into SQLite first."
        )
        return

    if st.button(
        "Generate Business Insights",
        type="primary",
        key="generate_business_insights_button",
    ):
        try:
            with st.spinner(
                "Analyzing business performance and generating insights..."
            ):
                insight_results = run_insight_engine(
                    st.session_state[
                        "database_engine"
                    ]
                )

            st.session_state[
                "business_insights"
            ] = insight_results

            if insight_results.get("available"):
                st.success(
                    "Business insights generated successfully."
                )
            else:
                st.warning(
                    insight_results.get(
                        "reason",
                        "No business insights are available.",
                    )
                )

        except Exception as error:
            st.error(
                f"Insight generation failed: {error}"
            )
            return

    if "business_insights" not in st.session_state:
        st.info(
            "Click 'Generate Business Insights' to analyze "
            "the dataset and identify business opportunities."
        )
        return

    results = st.session_state[
        "business_insights"
    ]

    if not results.get("available"):
        st.warning(
            results.get(
                "reason",
                "No business insights are available.",
            )
        )
        return

    insights_df = results.get(
        "insights"
    )

    if insights_df is None or insights_df.empty:
        st.info(
            "No insights were generated from the available data."
        )
        return

    # ========================================================
    # SUMMARY
    # ========================================================

    st.write("### Insight Summary")

    insight_count = results.get(
        "insight_count",
        len(insights_df),
    )

    high_count = int(
        (
            insights_df["priority"]
            == "High"
        ).sum()
    )

    medium_count = int(
        (
            insights_df["priority"]
            == "Medium"
        ).sum()
    )

    low_count = int(
        (
            insights_df["priority"]
            == "Low"
        ).sum()
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Insights",
            insight_count,
        )

    with col2:
        st.metric(
            "High Priority",
            high_count,
        )

    with col3:
        st.metric(
            "Medium Priority",
            medium_count,
        )

    with col4:
        st.metric(
            "Low Priority",
            low_count,
        )

    # ========================================================
    # PRIORITY INSIGHTS
    # ========================================================

    st.write("### Business Findings & Recommendations")

    for _, insight in insights_df.iterrows():

        priority = str(
            insight.get(
                "priority",
                "Low",
            )
        )

        title = str(
            insight.get(
                "title",
                "Business Insight",
            )
        )

        finding = str(
            insight.get(
                "finding",
                "",
            )
        )

        recommendation = str(
            insight.get(
                "recommendation",
                "",
            )
        )

        metric = insight.get(
            "metric",
            "",
        )

        value = insight.get(
            "value",
            None,
        )

        if priority == "High":
            prefix = "🔴"
        elif priority == "Medium":
            prefix = "🟠"
        else:
            prefix = "🟢"

        with st.expander(
            f"{prefix} {priority} — {title}",
            expanded=(
                priority == "High"
            ),
        ):

            st.markdown(
                f"**Finding:** {finding}"
            )

            st.markdown(
                f"**Recommendation:** {recommendation}"
            )

            if metric:
                if (
                    isinstance(
                        value,
                        (int, float),
                    )
                    and not isinstance(
                        value,
                        bool,
                    )
                ):
                    if "Rate" in metric or "Contribution" in metric or "Change" in metric:
                        formatted_value = (
                            f"{value:.1f}%"
                        )
                    else:
                        formatted_value = (
                            f"{value:,.2f}"
                        )

                    st.metric(
                        metric,
                        formatted_value,
                    )
                else:
                    st.write(
                        f"**Metric:** {metric}"
                    )

    # ========================================================
    # INSIGHT TABLE
    # ========================================================

    st.write("### Complete Insight Table")

    display_columns = [
        column
        for column in [
            "insight_type",
            "priority",
            "title",
            "finding",
            "recommendation",
            "metric",
            "value",
        ]
        if column in insights_df.columns
    ]

    st.dataframe(
        insights_df[display_columns],
        use_container_width=True,
        hide_index=True,
    )

    # ========================================================
    # INSIGHT TYPES
    # ========================================================

    if "insight_type" in insights_df.columns:

        st.write("### Insights by Business Area")

        type_counts = (
            insights_df[
                "insight_type"
            ]
            .value_counts()
            .rename_axis(
                "business_area"
            )
            .reset_index(
                name="insight_count"
            )
        )

        st.bar_chart(
            type_counts.set_index(
                "business_area"
            )
        )

    # ========================================================
    # EXPLANATION
    # ========================================================

    with st.expander(
        "How does the Insight Engine work?"
    ):
        st.markdown(
            """
            The Insight Engine analyzes the fields available
            in the uploaded dataset and generates business
            findings only when the required data is available.

            **Analysis areas include:**

            - Revenue
            - Revenue trends
            - Products
            - Categories
            - Regions
            - Customers
            - Profitability
            - Returns
            - Data quality

            The engine is adaptive. If a dataset does not
            contain a field required for a particular analysis,
            that insight category is skipped instead of causing
            the application to fail.

            Each generated insight contains:

            **Finding** — what the data shows.

            **Recommendation** — a practical area for further
            business investigation or action.

            **Metric** — the numerical evidence supporting
            the finding.
            """
        )



# ============================================================
# EXECUTIVE BUSINESS OVERVIEW
# ============================================================

def display_business_overview_section() -> None:
    """Display an executive-level adaptive business overview."""

    st.header("Executive Business Overview")
    st.caption(
        "A decision-oriented view of the business metrics available "
        "in the currently loaded dataset."
    )

    if "database_engine" not in st.session_state:
        st.info(
            "Run the Data Pipeline and load the dataset into SQLite first."
        )
        return

    engine = st.session_state["database_engine"]

    try:
        metrics = calculate_all_metrics(engine)
        st.session_state["overview_metrics"] = metrics
    except Exception as error:
        st.error(f"Unable to calculate business metrics: {error}")
        return

    def fmt_number(value):
        return f"{float(value):,.2f}" if value is not None else "N/A"

    def fmt_int(value):
        return f"{int(value):,}" if value is not None else "N/A"

    primary = st.columns(4)

    with primary[0]:
        st.metric("Total Revenue", fmt_number(metrics.get("total_revenue")))
    with primary[1]:
        st.metric("Total Orders", fmt_int(metrics.get("total_orders")))
    with primary[2]:
        st.metric("Units Sold", fmt_number(metrics.get("total_quantity")))
    with primary[3]:
        st.metric(
            "Average Order Value",
            fmt_number(metrics.get("average_order_value")),
        )

    secondary = st.columns(4)

    with secondary[0]:
        st.metric("Unique Customers", fmt_int(metrics.get("unique_customers")))
    with secondary[1]:
        st.metric("Unique Products", fmt_int(metrics.get("unique_products")))
    with secondary[2]:
        profit = metrics.get("total_profit")
        st.metric("Total Profit", fmt_number(profit))
    with secondary[3]:
        margin = metrics.get("profit_margin")
        st.metric(
            "Profit Margin",
            f"{float(margin):.2f}%" if margin is not None else "N/A",
        )

    tertiary = st.columns(3)

    with tertiary[0]:
        repeat_rate = metrics.get("repeat_customer_rate")
        st.metric(
            "Repeat Customer Rate",
            f"{float(repeat_rate):.2f}%" if repeat_rate is not None else "N/A",
        )
    with tertiary[1]:
        return_rate = metrics.get("return_rate")
        st.metric(
            "Return Rate",
            f"{float(return_rate):.2f}%" if return_rate is not None else "N/A",
        )
    with tertiary[2]:
        missing_rate = metrics.get("missing_value_rate")
        st.metric(
            "Missing Value Rate",
            f"{float(missing_rate):.2f}%" if missing_rate is not None else "N/A",
        )

    st.divider()

    # Revenue trend
    available_columns = get_database_columns(engine)

    if (
        "order_date" in available_columns
        and ("net_sales" in available_columns or "sales_amount" in available_columns)
    ):
        sales_column = (
            "net_sales"
            if "net_sales" in available_columns
            else "sales_amount"
        )

        query = f"""
            SELECT
                strftime('%Y-%m', order_date) AS month,
                SUM({sales_column}) AS revenue
            FROM transactions
            WHERE order_date IS NOT NULL
            GROUP BY strftime('%Y-%m', order_date)
            ORDER BY month
        """

        try:
            trend_df = execute_database_query(engine, query)

            if not trend_df.empty:
                st.subheader("Revenue Trend")

                fig = px.line(
                    trend_df,
                    x="month",
                    y="revenue",
                    markers=True,
                    title="Monthly Revenue",
                )
                fig.update_layout(
                    xaxis_title="Month",
                    yaxis_title="Revenue",
                )
                fig = apply_chart_theme(fig)

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                )
        except Exception as error:
            st.warning(
                f"Revenue trend could not be displayed: {error}"
            )

    st.subheader("Metric Availability")

    availability_items = [
        ("Total Revenue", metrics.get("total_revenue") is not None),
        ("Total Orders", metrics.get("total_orders") is not None),
        ("Total Quantity", metrics.get("total_quantity") is not None),
        ("Average Order Value", metrics.get("average_order_value") is not None),
        ("Unique Customers", metrics.get("unique_customers") is not None),
        ("Unique Products", metrics.get("unique_products") is not None),
        ("Total Profit", metrics.get("total_profit") is not None),
        ("Profit Margin", metrics.get("profit_margin") is not None),
        ("Repeat Customer Rate", metrics.get("repeat_customer_rate") is not None),
        ("Return Rate", metrics.get("return_rate") is not None),
        ("Missing Value Rate", metrics.get("missing_value_rate") is not None),
    ]

    # Use a native Streamlit/Pandas table instead of custom HTML.
    # This avoids Markdown interpreting the HTML as a code block and
    # keeps the status indicators reliable in both Light and Dark modes.
    availability_df = pd.DataFrame(
        [
            {
                "Metric": metric_name,
                "Status": "✓ Available" if available else "× Unavailable",
            }
            for metric_name, available in availability_items
        ]
    )

    def style_metric_status(column):
        return [
            (
                "color: #16794A; background-color: #DDF7EA; font-weight: 600;"
                if str(value).startswith("✓")
                else "color: #B42318; background-color: #FDE4E4; font-weight: 600;"
            )
            for value in column
        ]

    styled_availability_df = (
        availability_df.style
        .apply(style_metric_status, subset=["Status"])
        .set_properties(
            subset=["Metric"],
            **{"font-weight": "500"},
        )
    )

    st.dataframe(
        styled_availability_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Metric": st.column_config.TextColumn("Metric"),
            "Status": st.column_config.TextColumn("Status"),
        },
    )


# ============================================================
# DATA EXPLORER
# ============================================================

def get_database_columns(engine) -> list[str]:
    """Return database columns using the existing schema helper."""
    try:
        return get_table_columns(engine)
    except Exception:
        return []


def execute_database_query(engine, query: str) -> pd.DataFrame:
    """Execute a read-only SQL query."""
    from sqlalchemy import text

    normalized = query.strip().lower()

    if not normalized.startswith("select"):
        raise ValueError("Only SELECT queries are allowed in the Data Explorer.")

    with engine.connect() as connection:
        return pd.read_sql_query(text(query), connection)


def display_data_explorer_section() -> None:
    """Display an adaptive read-only transaction explorer."""

    st.header("Data Explorer")
    st.caption(
        "Explore the loaded transaction table without changing the database."
    )

    if "database_engine" not in st.session_state:
        st.info(
            "Run the Data Pipeline and load the dataset into SQLite first."
        )
        return

    engine = st.session_state["database_engine"]
    columns = get_database_columns(engine)

    if not columns:
        st.warning("No database columns are available.")
        return

    st.write("### Quick Dataset Explorer")

    selected_columns = st.multiselect(
        "Columns to display",
        options=columns,
        default=columns[: min(8, len(columns))],
    )

    if not selected_columns:
        st.info("Select at least one column.")
        return

    limit = st.slider(
        "Rows to display",
        min_value=10,
        max_value=500,
        value=50,
        step=10,
    )

    safe_columns = ", ".join(
        f'"{column}"' for column in selected_columns
    )

    query = f"""
        SELECT {safe_columns}
        FROM transactions
        LIMIT {int(limit)}
    """

    try:
        explorer_df = execute_database_query(
            engine,
            query,
        )

        st.dataframe(
            explorer_df,
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            f"Showing up to {limit:,} rows from the transactions table."
        )

    except Exception as error:
        st.error(
            f"Could not load explorer data: {error}"
        )

    st.divider()

    st.write("### Read-Only SQL Explorer")

    sql_query = st.text_area(
        "SQL SELECT query",
        value='SELECT * FROM transactions LIMIT 20',
        height=120,
        help="Only SELECT statements are permitted.",
    )

    if st.button(
        "Run SQL Query",
        key="run_sql_explorer_button",
    ):
        try:
            result_df = execute_database_query(
                engine,
                sql_query,
            )

            st.dataframe(
                result_df,
                use_container_width=True,
                hide_index=True,
            )

            st.success(
                f"Query returned {len(result_df):,} rows."
            )

        except Exception as error:
            st.error(
                f"SQL query failed: {error}"
            )


# ============================================================
# DATASET INFORMATION
# ============================================================

def display_dataset_information_section() -> None:
    """Display information about the active dataset and pipeline state."""

    st.header("Dataset Information")

    if "dataset" not in st.session_state:
        st.info("No dataset is currently loaded.")
        return

    df = st.session_state["dataset"]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Rows", f"{len(df):,}")

    with col2:
        st.metric("Columns", len(df.columns))

    with col3:
        memory_mb = (
            df.memory_usage(deep=True).sum() / (1024 ** 2)
        )
        st.metric("Memory", f"{memory_mb:.2f} MB")

    with col4:
        st.metric(
            "Missing Cells",
            f"{int(df.isna().sum().sum()):,}",
        )

    st.write("### Dataset Columns")
    columns_df = pd.DataFrame(
        {
            "Column": df.columns,
            "Data Type": [
                str(dtype)
                for dtype in df.dtypes
            ],
            "Missing Values": [
                int(df[column].isna().sum())
                for column in df.columns
            ],
            "Unique Values": [
                int(df[column].nunique(dropna=True))
                for column in df.columns
            ],
        }
    )

    st.dataframe(
        columns_df,
        use_container_width=True,
        hide_index=True,
    )

    st.write("### Pipeline Status")

    status_items = [
        ("Dataset Loaded", "dataset" in st.session_state),
        ("Schema Detected", "schema_detection" in st.session_state),
        ("Mapping Confirmed", "confirmed_mapping" in st.session_state),
        ("Validated", "validation" in st.session_state),
        ("Cleaned", "cleaned_dataframe" in st.session_state),
        ("Transformed", "transformed_dataframe" in st.session_state),
        ("Features Engineered", "featured_dataframe" in st.session_state),
        ("SQLite Loaded", "database_engine" in st.session_state),
        ("Metrics Available", "metrics" in st.session_state),
    ]

    status_df = pd.DataFrame(
        [
            {
                "Stage": name,
                "Status": "Complete" if complete else "Pending",
            }
            for name, complete in status_items
        ]
    )

    st.dataframe(
        status_df,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# PHASE 18 — NAVIGATION ROUTER
# ============================================================

def display_dashboard_section(
    selected_section: str,
) -> None:
    """Render the selected business dashboard section."""

    if selected_section == "Data Pipeline":
        display_dataset_summary(df)
        st.divider()
        display_dataset_preview(df)
        st.divider()
        display_profile(df)
        st.divider()
        display_schema_detection(df)
        st.divider()
        display_mapping_editor(df)

        if "canonical_dataframe" not in st.session_state:
            st.info(
                "Confirm the column mapping above to continue."
            )
            return

        canonical_df = st.session_state[
            "canonical_dataframe"
        ]

        confirmed_mapping = st.session_state.get(
            "confirmed_mapping",
            {},
        )

        st.divider()
        display_validation_report(
            canonical_df,
            confirmed_mapping,
        )

        st.divider()
        display_cleaning_section(canonical_df)

        if "cleaned_dataframe" not in st.session_state:
            return

        cleaned_df = st.session_state[
            "cleaned_dataframe"
        ]

        st.divider()
        display_transformation_section(cleaned_df)

        if "transformed_dataframe" not in st.session_state:
            return

        transformed_df = st.session_state[
            "transformed_dataframe"
        ]

        st.divider()
        display_feature_engineering_section(
            transformed_df
        )

        if "featured_dataframe" not in st.session_state:
            return

        featured_df = st.session_state[
            "featured_dataframe"
        ]

        st.divider()
        display_database_section(featured_df)
        return

    if selected_section == "Business Overview":
        display_business_overview_section()
        return

    if selected_section == "Products":
        if "database_engine" not in st.session_state:
            st.info(
                "Complete the Data Pipeline and load SQLite first."
            )
            return
        display_product_analytics_section()
        return

    if selected_section == "Customers":
        if "database_engine" not in st.session_state:
            st.info(
                "Complete the Data Pipeline and load SQLite first."
            )
            return
        display_customer_analytics_section()
        st.divider()
        display_customer_segmentation_section()
        return

    if selected_section == "Regions":
        if "database_engine" not in st.session_state:
            st.info(
                "Complete the Data Pipeline and load SQLite first."
            )
            return
        display_regional_analytics_section()
        return

    if selected_section == "Insights":
        if "database_engine" not in st.session_state:
            st.info(
                "Complete the Data Pipeline and load SQLite first."
            )
            return
        display_business_insights_section()
        return

    if selected_section == "Data Explorer":
        display_data_explorer_section()
        return

    if selected_section == "Dataset Information":
        display_dataset_information_section()
        return


# ============================================================
# APPLICATION HEADER
# ============================================================

st.title(
    "Adaptive E-Commerce Analytics & ETL Intelligence Platform"
)

st.caption(
    "A reusable platform for heterogeneous e-commerce data: "
    "load → profile → map → validate → clean → transform → "
    "feature engineer → analyze → generate insights."
)


# ============================================================
# SIDEBAR
# ============================================================

display_sidebar_header()

display_appearance_selector()

st.sidebar.divider()
st.sidebar.header("Dataset")

dataset_source = st.sidebar.radio(
    "Choose dataset source:",
    [
        SAMPLE_DATASET_NAME,
        UPLOAD_DATASET_NAME,
    ],
)

# ============================================================
# DATASET LOADING
# ============================================================

df = None
uploaded_file = None

if dataset_source == SAMPLE_DATASET_NAME:

    sample_path = Path("data/sample_sales.csv")

    dataset_signature = get_dataset_signature(
        dataset_source
    )

    handle_dataset_change(
        dataset_signature
    )

    if not sample_path.exists():
        st.warning(
            "Sample dataset not found. "
            "Run generate_sample_data.py first."
        )
    else:
        try:
            df = load_sample_dataset(sample_path)
        except DataLoadError as error:
            st.error(str(error))

else:

    # The uploader intentionally stays directly below the
    # Upload CSV source selector and before Dashboard Section.
    uploaded_file = st.sidebar.file_uploader(
        "Upload an e-commerce CSV",
        type=["csv"],
        key="ecommerce_csv_uploader",
    )

    dataset_signature = get_dataset_signature(
        dataset_source,
        uploaded_file,
    )

    handle_dataset_change(
        dataset_signature
    )

    if uploaded_file is not None:
        try:
            df = load_csv(uploaded_file)
        except DataLoadError as error:
            st.error(str(error))

# Dashboard navigation comes AFTER the dataset/upload controls.
selected_section = get_dashboard_section()

st.sidebar.divider()
st.sidebar.caption(
    "Complete the Data Pipeline first. "
    "Analytics sections become available after SQLite loading."
)


# ============================================================
# STOP IF NO DATASET
# ============================================================

if df is None:
    st.info(
        "Select a dataset source and provide a valid CSV."
    )
    st.stop()


# ============================================================
# STORE CURRENT DATASET
# ============================================================

st.session_state["dataset"] = df


# ============================================================
# ACTIVE DATASET INDICATOR
# ============================================================

st.info(
    f"Active dataset: {len(df):,} rows × {len(df.columns):,} columns"
)


# ============================================================
# DASHBOARD ROUTER
# ============================================================

display_dashboard_header()

st.divider()

display_dashboard_section(
    selected_section
)
