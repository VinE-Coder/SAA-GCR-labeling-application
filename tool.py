import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gdown

st.set_page_config(
    page_title="SAA Labeling Tool",
    layout="wide"
)

# -------------------------
# DATA
# -------------------------

@st.cache_data
def load_data():

    file_id = "1gpqXHXpY7BEdvzvAqR4PKHRmxHYzph4K"

    gdown.download(
        f"https://drive.google.com/uc?id={file_id}",
        "data.csv",
        quiet=True
    )

    df = pd.read_csv("data.csv")

    df["UTC"] = pd.to_datetime(
        df["UTC"],
        format="mixed",
        utc=True
    )

    df = df.sort_values("UTC")

    return df


df = load_data()

# -------------------------
# SESSION STATE
# -------------------------

if "labels" not in st.session_state:
    st.session_state.labels = []

if "completed_days" not in st.session_state:
    st.session_state.completed_days = set()

# -------------------------
# TITLE
# -------------------------

st.title("SAA Manual Labeling Tool")

annotator = st.text_input(
    "Volunteer Name"
)

# -------------------------
# DAY HANDLING
# -------------------------

df["date"] = df["UTC"].dt.date

days = sorted(df["date"].unique())

if "day_index" not in st.session_state:
    st.session_state.day_index = 0

col_prev, col_next = st.columns(2)

with col_prev:
    if st.button("Previous Day"):
        st.session_state.day_index = max(
            0,
            st.session_state.day_index - 1
        )

with col_next:
    if st.button("Next Day"):
        st.session_state.day_index = min(
            len(days) - 1,
            st.session_state.day_index + 1
        )

selected_day = days[
    st.session_state.day_index
]

st.write(f"Current Day: {selected_day}")

# -------------------------
# PROGRESS
# -------------------------

completed = len(
    st.session_state.completed_days
)

st.metric(
    "Days Completed",
    f"{completed}/10"
)

st.progress(
    min(completed / 10, 1.0)
)

# -------------------------
# INSTRUCTIONS
# -------------------------

st.info("""
Instructions

1. Use Previous Day / Next Day to navigate.
2. Inspect the radiation flux graph.
3. Identify SAA regions.
4. Enter start and end UTC times.
5. Save the label.
6. Mark the day complete.
7. Continue until you complete roughly 10 days.

Example Format

2020-10-17 17:02:00+00:00
2020-10-17 17:14:00+00:00
""")

# -------------------------
# FILTER DAY
# -------------------------

day_df = df[
    df["date"] == selected_day
]

plot_df = day_df.iloc[::10]

# -------------------------
# NASA TOGGLE
# -------------------------

show_nasa = st.checkbox(
    "Show NASA SRAG Labels",
    value=True
)

# -------------------------
# GRAPH
# -------------------------

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=plot_df["UTC"],
        y=plot_df["flux"],
        mode="lines",
        name="Flux"
    )
)

if show_nasa and "SAA" in plot_df.columns:

    nasa_df = plot_df[
        plot_df["SAA"] == 1
    ]

    fig.add_trace(
        go.Scatter(
            x=nasa_df["UTC"],
            y=nasa_df["flux"],
            mode="markers",
            name="NASA SAA"
        )
    )

fig.update_layout(
    height=700,
    yaxis_type="log",
    xaxis_title="UTC",
    yaxis_title="Flux",
    dragmode="zoom"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# -------------------------
# LABEL ENTRY
# -------------------------

st.subheader("Add SAA Label")

col1, col2 = st.columns(2)

with col1:
    start_time = st.text_input(
        "Start Time UTC",
        placeholder="2020-10-17 17:02:00+00:00"
    )

with col2:
    end_time = st.text_input(
        "End Time UTC",
        placeholder="2020-10-17 17:14:00+00:00"
    )

if st.button("Save Label"):

    st.session_state.labels.append(
        {
            "annotator": annotator,
            "date": str(selected_day),
            "start": start_time,
            "end": end_time,
            "label": "SAA"
        }
    )

    st.success("Label Saved")

# -------------------------
# COMPLETE DAY
# -------------------------

if st.button("Mark Day Complete"):

    st.session_state.completed_days.add(
        str(selected_day)
    )

    st.success(
        f"{selected_day} marked complete"
    )

# -------------------------
# SAVED LABELS
# -------------------------

st.subheader("Saved Labels")

labels_df = pd.DataFrame(
    st.session_state.labels
)

if len(labels_df) > 0:

    st.dataframe(
        labels_df,
        use_container_width=True
    )

    csv = labels_df.to_csv(
        index=False
    ).encode()

    st.download_button(
        "Download Labels CSV",
        csv,
        file_name="saa_labels.csv",
        mime="text/csv"
    )

# -------------------------
# COMPLETED DAYS
# -------------------------

if len(st.session_state.completed_days) > 0:

    st.subheader("Completed Days")

    for day in sorted(
        st.session_state.completed_days
    ):
        st.write(day)