"""
Keboola Streamlit App Template

A minimal Streamlit data app that connects to Keboola Storage
to read, display, and filter data.

This template demonstrates:
1. Connecting to Keboola Storage API
2. Loading data from Storage tables
3. Interactive filtering and visualization
4. Exporting results back to Storage

For more information:
- Streamlit: https://docs.streamlit.io/
- Keboola Storage API: https://developers.keboola.com/integrate/storage/
"""

import os
import streamlit as st
import pandas as pd
from typing import Optional
import io


def get_keboola_client():
    """
    Initialize Keboola Storage API client.

    Requires KEBOOLA_STORAGE_TOKEN and KEBOOLA_STORAGE_API_URL
    environment variables.

    Returns:
        Configured Keboola client

    Raises:
        ValueError: If required environment variables are missing
    """
    try:
        from kbcstorage.client import Client
    except ImportError:
        st.error("""
        Keboola Storage Client not installed.
        Install it with: `pip install kbcstorage`
        """)
        st.stop()

    # Get credentials from environment
    token = os.getenv('KEBOOLA_STORAGE_TOKEN') or st.secrets.get('KEBOOLA_STORAGE_TOKEN')
    url = os.getenv('KEBOOLA_STORAGE_API_URL', 'https://connection.keboola.com')

    if not token:
        st.error("""
        Missing Keboola credentials!

        Please set either:
        1. Environment variable: KEBOOLA_STORAGE_TOKEN
        2. Streamlit secrets: .streamlit/secrets.toml

        Get your token from: Keboola Connection > Users & Settings > API Tokens
        """)
        st.stop()

    return Client(url, token)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_table_list(_client) -> list[dict]:
    """
    Load list of available tables from Keboola Storage.

    Args:
        _client: Keboola Storage client (underscore prevents caching)

    Returns:
        List of table metadata dictionaries
    """
    try:
        tables = _client.tables.list()
        return tables
    except Exception as e:
        st.error(f"Error loading table list: {e}")
        return []


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_table_data(_client, table_id: str) -> pd.DataFrame:
    """
    Load data from a Keboola Storage table.

    Args:
        _client: Keboola Storage client (underscore prevents caching)
        table_id: Full table ID (e.g., 'in.c-main.customers')

    Returns:
        DataFrame with table data
    """
    try:
        # Get table detail
        table_detail = _client.tables.detail(table_id)

        # Export table data to CSV
        _client.tables.export_to_file(
            table_id=table_id,
            path_name='/tmp/table_export.csv'
        )

        # Load CSV into DataFrame
        df = pd.read_csv('/tmp/table_export.csv')

        return df

    except Exception as e:
        st.error(f"Error loading table {table_id}: {e}")
        return pd.DataFrame()


def save_to_storage(client, df: pd.DataFrame, table_id: str, incremental: bool = False):
    """
    Save DataFrame back to Keboola Storage.

    Args:
        client: Keboola Storage client
        df: DataFrame to save
        table_id: Target table ID (e.g., 'out.c-main.results')
        incremental: If True, append data; if False, replace

    Returns:
        True if successful, False otherwise
    """
    try:
        # Save DataFrame to temporary CSV
        csv_path = '/tmp/export_data.csv'
        df.to_csv(csv_path, index=False)

        # Parse bucket and table name from table_id
        # Format: stage.bucket.table (e.g., 'out.c-main.results')
        parts = table_id.split('.')
        if len(parts) < 3:
            st.error(f"Invalid table ID format: {table_id}")
            return False

        bucket_id = f"{parts[0]}.{parts[1]}"
        table_name = '.'.join(parts[2:])

        # Create table if it doesn't exist
        try:
            client.tables.detail(table_id)
            # Table exists, load data
            client.tables.load(
                table_id=table_id,
                file_path=csv_path,
                is_incremental=incremental
            )
        except:
            # Table doesn't exist, create it
            client.tables.create(
                name=table_name,
                bucket_id=bucket_id,
                file_path=csv_path
            )

        return True

    except Exception as e:
        st.error(f"Error saving to Storage: {e}")
        return False


def main():
    """
    Main Streamlit app function.
    """

    # Page configuration
    st.set_page_config(
        page_title="Keboola Data Viewer",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Header
    st.title("📊 Keboola Data Viewer")
    st.markdown("View, filter, and export data from Keboola Storage")

    # Initialize Keboola client
    try:
        client = get_keboola_client()
    except Exception as e:
        st.error(f"Failed to initialize Keboola client: {e}")
        st.stop()

    # Sidebar - Table Selection
    st.sidebar.header("Data Source")

    # Load available tables
    with st.spinner("Loading tables..."):
        tables = load_table_list(client)

    if not tables:
        st.warning("No tables found in Storage")
        st.stop()

    # Create table selector
    table_options = {
        f"{t['id']} ({t.get('rowsCount', 0)} rows)": t['id']
        for t in tables
    }

    selected_table_display = st.sidebar.selectbox(
        "Select a table",
        options=list(table_options.keys()),
        help="Choose a table to view and analyze"
    )

    selected_table_id = table_options[selected_table_display]

    # Load button
    if st.sidebar.button("🔄 Load Data", type="primary"):
        st.cache_data.clear()

    # Load table data
    with st.spinner(f"Loading {selected_table_id}..."):
        df = load_table_data(client, selected_table_id)

    if df.empty:
        st.warning("No data available")
        st.stop()

    # Display basic info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Rows", f"{len(df):,}")
    with col2:
        st.metric("Columns", len(df.columns))
    with col3:
        st.metric("Memory", f"{df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")

    # Data Preview
    st.subheader("📋 Data Preview")

    # Show/hide columns
    with st.expander("🔧 Column Selector", expanded=False):
        all_columns = df.columns.tolist()
        selected_columns = st.multiselect(
            "Select columns to display",
            options=all_columns,
            default=all_columns[:10] if len(all_columns) > 10 else all_columns
        )

    display_df = df[selected_columns] if selected_columns else df

    # Filtering
    st.subheader("🔍 Filters")

    # Create filter UI
    filter_col1, filter_col2 = st.columns(2)

    with filter_col1:
        # Text search across all string columns
        search_term = st.text_input(
            "Search (text columns)",
            placeholder="Enter search term...",
            help="Search across all text columns"
        )

    with filter_col2:
        # Row limit
        max_rows = st.number_input(
            "Max rows to display",
            min_value=10,
            max_value=len(df),
            value=min(100, len(df)),
            step=10
        )

    # Apply text search filter
    filtered_df = display_df.copy()

    if search_term:
        mask = filtered_df.astype(str).apply(
            lambda row: row.str.contains(search_term, case=False, na=False).any(),
            axis=1
        )
        filtered_df = filtered_df[mask]

        st.info(f"Found {len(filtered_df)} rows matching '{search_term}'")

    # Column-specific filters
    with st.expander("📊 Advanced Filters", expanded=False):
        st.markdown("Filter by specific columns:")

        # Numeric column filters
        numeric_cols = filtered_df.select_dtypes(include=['number']).columns.tolist()

        if numeric_cols:
            selected_numeric = st.selectbox("Select numeric column", numeric_cols)

            if selected_numeric:
                col_min = float(filtered_df[selected_numeric].min())
                col_max = float(filtered_df[selected_numeric].max())

                range_values = st.slider(
                    f"Range for {selected_numeric}",
                    min_value=col_min,
                    max_value=col_max,
                    value=(col_min, col_max)
                )

                filtered_df = filtered_df[
                    (filtered_df[selected_numeric] >= range_values[0]) &
                    (filtered_df[selected_numeric] <= range_values[1])
                ]

        # Categorical column filters
        categorical_cols = filtered_df.select_dtypes(include=['object']).columns.tolist()

        if categorical_cols:
            selected_categorical = st.selectbox("Select categorical column", categorical_cols)

            if selected_categorical:
                unique_values = filtered_df[selected_categorical].unique().tolist()

                if len(unique_values) <= 50:  # Only show multiselect for reasonable number of values
                    selected_values = st.multiselect(
                        f"Filter {selected_categorical}",
                        options=unique_values,
                        default=unique_values
                    )

                    filtered_df = filtered_df[filtered_df[selected_categorical].isin(selected_values)]
                else:
                    st.info(f"Too many unique values ({len(unique_values)}) to filter")

    # Display filtered data
    st.dataframe(
        filtered_df.head(int(max_rows)),
        use_container_width=True,
        hide_index=True
    )

    # Statistics
    with st.expander("📈 Statistics", expanded=False):
        st.subheader("Data Summary")

        tab1, tab2 = st.tabs(["Numeric Columns", "Categorical Columns"])

        with tab1:
            numeric_df = filtered_df.select_dtypes(include=['number'])
            if not numeric_df.empty:
                st.dataframe(numeric_df.describe(), use_container_width=True)
            else:
                st.info("No numeric columns in selected data")

        with tab2:
            categorical_df = filtered_df.select_dtypes(include=['object'])
            if not categorical_df.empty:
                for col in categorical_df.columns[:5]:  # Show first 5 categorical columns
                    st.markdown(f"**{col}**")
                    value_counts = categorical_df[col].value_counts().head(10)
                    st.bar_chart(value_counts)
            else:
                st.info("No categorical columns in selected data")

    # Export Options
    st.subheader("💾 Export")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Download as CSV
        csv_buffer = io.StringIO()
        filtered_df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()

        st.download_button(
            label="⬇️ Download CSV",
            data=csv_data,
            file_name=f"{selected_table_id.replace('.', '_')}_filtered.csv",
            mime="text/csv",
            help="Download filtered data as CSV"
        )

    with col2:
        # Download as JSON
        json_data = filtered_df.to_json(orient='records', indent=2)

        st.download_button(
            label="⬇️ Download JSON",
            data=json_data,
            file_name=f"{selected_table_id.replace('.', '_')}_filtered.json",
            mime="application/json",
            help="Download filtered data as JSON"
        )

    with col3:
        # Save back to Storage
        if st.button("💾 Save to Storage", help="Save filtered data back to Keboola Storage"):
            with st.spinner("Saving to Storage..."):
                # Ask for table name
                output_table_id = st.text_input(
                    "Output table ID",
                    value=f"out.c-main.{selected_table_id.split('.')[-1]}_filtered",
                    help="Format: out.c-bucket.table-name"
                )

                if output_table_id:
                    success = save_to_storage(client, filtered_df, output_table_id)

                    if success:
                        st.success(f"✓ Data saved to {output_table_id}")
                    else:
                        st.error("Failed to save data")

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
        <p>Built with Streamlit + Keboola Storage API</p>
        <p><a href='https://help.keboola.com'>Documentation</a> |
        <a href='https://developers.keboola.com'>API Reference</a></p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == '__main__':
    main()
