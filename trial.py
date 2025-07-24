'''
st.set_page_config(page_title="Market Sub-Segment Explorer", layout="wide")
st.title("📊 Market Sub-Segment Explorer")

# === Input Form ===
with st.form("market_input_form"):
    market = st.text_input("Enter a market (e.g. AI, Plastics, EV Batteries):", key="market_input")
    submitted = st.form_submit_button("Analyze Market")

# === Main Market Analysis ===
if submitted and market:
    with st.spinner("Fetching Global Market Overview..."):
        global_md = get_global_overview(market)
        st.session_state["global_md"] = global_md

    with st.spinner("Analyzing vertical sub-markets..."):
        verticals_md = get_vertical_submarkets(market)

    with st.spinner("Analyzing horizontal sub-markets..."):
        horizontals_md = get_horizontal_submarkets(market)

    st.session_state["raw_markdown"] = f"{verticals_md}\n\n{horizontals_md}"

    # === Split & Parse Markdown
    vertical_table_md, horizontal_table_md = split_tables(st.session_state["raw_markdown"])
    vertical_df = markdown_table_to_dataframe(vertical_table_md)
    horizontal_df = markdown_table_to_dataframe(horizontal_table_md)

    st.session_state["vertical_df"] = vertical_df
    st.session_state["horizontal_df"] = horizontal_df

# === Global Market Overview
if "global_md" in st.session_state:
    st.markdown("## Market Overview")
    st.markdown(st.session_state["global_md"])

# === Display Vertical & Horizontal Tables
if "vertical_df" in st.session_state:
    st.markdown("## 🏗️ Vertical Sub-markets")
    st.dataframe(st.session_state["vertical_df"], use_container_width=True)

if "horizontal_df" in st.session_state:
    st.markdown("## 🔗 Horizontal Sub-markets")
    st.dataframe(st.session_state["horizontal_df"], use_container_width=True)

# === Markdown Download
if "raw_markdown" in st.session_state:
    st.download_button(
        label="📥 Download Markdown",
        data=st.session_state["raw_markdown"],
        file_name=f"{market.replace(' ', '_')}_submarkets.md" if market else "submarkets.md",
        mime="text/markdown"
    )

# === Drilldown Section in Sidebar
with st.sidebar:
    st.markdown("## 🔍 Sub-market Drilldown")

    vertical_df = st.session_state.get("vertical_df")
    horizontal_df = st.session_state.get("horizontal_df")

    if vertical_df is not None and not vertical_df.empty:
        vertical_col = vertical_df.columns[0]
        clicked_vertical = st.radio(
            "Select a vertical sub-market:",
            vertical_df[vertical_col].dropna().unique().tolist(),
            key="clicked_vertical"
        )

        if clicked_vertical:
            st.markdown(f"### 📈 Metrics for: {clicked_vertical}")
            st.markdown(get_detailed_metrics(clicked_vertical) or "⚠️ No metrics found.")

            st.markdown(f"### 🏢 Top Companies: {clicked_vertical}")
            st.markdown(get_top_companies(clicked_vertical) or "⚠️ No company data found.")

    else:
        st.markdown("⚠️ No vertical sub-markets available.")

    if horizontal_df is not None and not horizontal_df.empty:
        horiz_col = horizontal_df.columns[0]
        clicked_horizontal = st.radio(
            "Select a horizontal sub-market:",
            horizontal_df[horiz_col].dropna().unique().tolist(),
            key="clicked_horizontal"
        )

        if clicked_horizontal:
            st.markdown(f"### 📈 Metrics for: {clicked_horizontal}")
            st.markdown(get_detailed_metrics(clicked_horizontal) or "⚠️ No metrics found.")

            st.markdown(f"### 🏢 Top Companies: {clicked_horizontal}")
            st.markdown(get_top_companies(clicked_horizontal) or "⚠️ No company data found.")
    else:
        st.markdown("⚠️ No horizontal sub-markets available.")

# === M&A Explorer Section ===
with st.expander("🤝 Mergers & Acquisitions Explorer"):
    st.markdown("Explore recent M&A activity related to the market.")

    # Select market/topic
    ma_market = st.text_input("Enter the market or industry:", key="ma_market")

    # Choose timeframe
    col1, col2 = st.columns(2)
    with col1:
        timeframe_option = st.selectbox("Select timeframe:", ["Last 3 years", "Last 5 years", "Custom Range"])
    with col2:
        custom_range = st.text_input("If custom, enter range (e.g., 2018–2020):", key="custom_ma_range")

    # Trigger search
    if st.button("🔍 Search M&A Activity"):
        if not ma_market:
            st.warning("Please enter a market name.")
        else:
            # Determine timeframe string
            if timeframe_option == "Custom Range" and custom_range:
                timeframe_str = custom_range
            elif timeframe_option == "Last 3 years":
                timeframe_str = "last 3 years"
            elif timeframe_option == "Last 5 years":
                timeframe_str = "last 5 years"
            else:
                timeframe_str = ""

            with st.spinner("Searching for M&A activity..."):
                result = get_mergers_table(ma_market, timeframe_str)
                st.markdown(result or "⚠️ No data found.")


# === File-Augmented Market Analysis
st.markdown("## 📂 File-Augmented Market Insight")

with st.form("file_augmented_form"):
    st.markdown("Upload optional market reports (PDF, CSV, Excel) to enhance analysis:")
    uploaded_files = st.file_uploader("Upload files", accept_multiple_files=True, type=["pdf", "csv", "xlsx", "xls"])
    augmented_market_query = st.text_input("Enter a market to analyze (e.g., Plastic recycling in the US):", key="augmented_market_query")
    run_augmented = st.form_submit_button("Generate Augmented Report")

if run_augmented and augmented_market_query:
    with st.spinner("🔍 Analyzing market with uploaded documents and web search..."):
        try:
            report_md = get_file_augmented_market_report(augmented_market_query, uploaded_files)
            parsed_df = parse_markdown_table(report_md)

            st.markdown("### 📂 File-Augmented Market Report")

            if not parsed_df.empty:
                st.dataframe(parsed_df, use_container_width=True)
                st.download_button(
                    label="📥 Download Markdown",
                    data=report_md,
                    file_name=f"{augmented_market_query.replace(' ', '_')}_augmented_report.md",
                    mime="text/markdown"
                )
            else:
                st.warning("⚠️ Could not parse the table from the response.")
        except Exception as e:
            st.error(f"Something went wrong: {e}")

# === Manual Query Section
with st.expander("🔎 Manual Query: Explore Any Market"):
    custom_query = st.text_input("Enter any market (e.g. US plastic recycling, AI chips, etc.):", key="manual_input")
    if st.button("Run Custom Exploration"):
        with st.spinner("Fetching metrics and companies..."):
            st.markdown("### 📈 Custom Metrics")
            st.markdown(get_detailed_metrics(custom_query) or "⚠️ No metrics found.")
            st.markdown("### 🏢 Custom Companies")
            st.markdown(get_top_companies(custom_query) or "⚠️ No company data found.")


# === Reset Button
if st.button("♻️ Regenerate Everything"):
    st.session_state.clear()
    st.experimental_rerun()
'''