import streamlit as st
import pandas as pd
import plotly.express as px
import uuid

st.set_page_config(layout="wide")

st.title("📊 Advanced CSV Comparison Dashboard")

# =====================================================
# UPLOAD MULTIPLE CSV
# =====================================================
uploaded_files = st.file_uploader(
    "Upload 1 or more csv",
    type=["csv"],
    accept_multiple_files=True
)

if not uploaded_files:
    st.info("CUpload at least one csv")
    st.stop()

# =====================================================
# MERGE DATASET
# =====================================================
dataframes = []
for file in uploaded_files:
    df_temp = pd.read_csv(file)
    df_temp["source_file"] = file.name
    dataframes.append(df_temp)

df = pd.concat(dataframes, ignore_index=True)
columns = df.columns.tolist()

# =====================================================
# SIDEBAR CONFIGURATION
# =====================================================
st.sidebar.header("⚙️ Configuration")

num_charts = st.sidebar.number_input(
    "Number of graphs",
    min_value=1,
    max_value=6,
    value=1
)

# =====================================================
# DYNAMIC GLOBAL FILTERS
# =====================================================
st.sidebar.header("🔎 Filters")

filtered_df = df.copy()

for col in columns:
    if filtered_df[col].dtype == "object":
        unique_vals = filtered_df[col].dropna().unique()
        if len(unique_vals) < 20:
            selected_vals = st.sidebar.multiselect(
                f"Filter {col}",
                unique_vals,
                default=unique_vals
            )
            filtered_df = filtered_df[
                filtered_df[col].isin(selected_vals)
            ]

# =====================================================
# COLOR PICKER FOR CSV 
# =====================================================
color_map = {}

if "source_file" in filtered_df.columns:

    st.sidebar.header("🎨 Colors CSV")

    unique_sources = filtered_df["source_file"].unique()

    # palette automatica plotly
    default_palette = px.colors.qualitative.Plotly

    for idx, src in enumerate(unique_sources):

        default_color = default_palette[idx % len(default_palette)]

        color_map[src] = st.sidebar.color_picker(
            f"Color for {src}",
            value=default_color,  # colore automatico
            key=f"color_{src}"
        )

# =====================================================
# CREATION MULTI-GRAPH
# =====================================================
for i in range(num_charts):

    st.markdown("---")
    st.subheader(f"Graph {i+1}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        x_axis = st.selectbox(
            f"Axis X",
            columns,
            key=f"x_{i}"
        )

    with col2:
        y_axis = st.selectbox(
            f"Axis Y",
            columns,
            key=f"y_{i}"
        )

    with col3:
        color_col = st.selectbox(
            f"Color/ Group",
            ["None"] + columns,
            key=f"colorcol_{i}"
        )

    with col4:
        chart_type = st.selectbox(
            f"Graph Type",
            ["Line", "Scatter", "Bar", "Boxplot"],
            key=f"type_{i}"
        )

    if color_col == "None":
        color_col = None

    # =====================================================
    # GENERATE FIGURE
    # =====================================================
    if chart_type == "Line":
        fig = px.line(
            filtered_df,
            x=x_axis,
            y=y_axis,
            color=color_col,
            markers=True,
            color_discrete_map=color_map if color_col == "source_file" else None
        )

    elif chart_type == "Scatter":
        fig = px.scatter(
            filtered_df,
            x=x_axis,
            y=y_axis,
            color=color_col,
            color_discrete_map=color_map if color_col == "source_file" else None
        )

    elif chart_type == "Bar":
        fig = px.bar(
            filtered_df,
            x=x_axis,
            y=y_axis,
            color=color_col,
            barmode="group",
            color_discrete_map=color_map if color_col == "source_file" else None
        )

    elif chart_type == "Boxplot":
        fig = px.box(
            filtered_df,
            x=x_axis,
            y=y_axis,
            color=color_col,
            color_discrete_map=color_map if color_col == "source_file" else None
        )

    fig.update_layout(
        height=600,
        template="plotly_white"
    )

    st.plotly_chart(fig, use_container_width=True)

    # =====================================================
    # EXPORT PNG
    # =====================================================
    if st.button(f"Download PNG Graph {i+1}", key=f"btn_{i}"):

        filename = f"graph_{uuid.uuid4().hex}.png"
        fig.write_image(filename)

        with open(filename, "rb") as file:
            st.download_button(
                label="Download PNG",
                data=file,
                file_name=filename,
                mime="image/png",
                key=f"download_{i}"
            )

# =====================================================
# Data Table
# =====================================================
with st.expander("📄 View filtered data"):
    st.dataframe(filtered_df)
