import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gdown

st.set_page_config(
    page_title="SAA Manual Labeling Tool",
    layout="wide"
)

# -------------------------
# LOAD DATA
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
# HEADER
# -------------------------

st.title("SAA Manual Labeling Tool")

annotator = st.text_input(
    "Volunteer Name"
)

# -------------------------
# DATE COLUMN
# -------------------------

df["date"] = df["UTC"].dt.date

days = sorted(df["date"].unique())

# -------------------------
# DAY NAVIGATION
# -------------------------

if "day_index" not in st.session_state:
    st.session_state.day_index = 0

nav1, nav2 = st.columns(2)

with nav1:
    if st.button("Previous Day"):
        st.session_state.day_index = max(
            0,
            st.session_state.day_index - 1
        )

with nav2:
    if st.button("Next Day"):
        st.session_state.day_index = min(
            len(days) - 1,
            st.session_state.day_index + 1
        )

selected_day = days[
    st.session_state.day_index
]

st.subheader(f"Current Day: {selected_day}")

# -------------------------
# PROGRESS
# -------------------------

completed = len(
    st.session_state.completed_days
)

st.metric(
    "Progress",
    f"{completed}/10 Days"
)

st.progress(
    min(completed / 10, 1.0)
)

# -------------------------
# INSTRUCTIONS
# -------------------------

st.info("""
How to Label an SAA Pass

1. Look for a large radiation peak on the graph.
2. Identify where the SAA pass begins.
3. Identify where the SAA pass ends.
4. Enter the UTC timestamps.
5. Click Save Label.

Timestamp Format

YYYY-MM-DD HH:MM:SS

Example

2020-10-17 17:02:00

2020-10-17 17:14:00

Rules

• Use UTC timestamps only.
• Start time must be before end time.
• One row = one SAA pass.
• Multiple passes can be labeled on the same day.
""")

# -------------------------
# FILTER DAY
# -------------------------

day_df = df[
    df["date"] == selected_day
]

plot_df = day_df.iloc[::10]

# -------------------------
# NASA OVERLAY
# -------------------------

show_nasa = st.checkbox(
    "Show NASA SRAG Labels",
    value=True
)

# -------------------------
# PLOT
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
    yaxis_title="Flux"
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
        placeholder="2020-10-17 17:02:00"
    )

with col2:
    end_time = st.text_input(
        "End Time UTC",
        placeholder="2020-10-17 17:14:00"
    )

if st.button("Save Label"):

    try:

        start_dt = pd.to_datetime(
            start_time,
            utc=True
        )

        end_dt = pd.to_datetime(
            end_time,
            utc=True
        )

        if start_dt >= end_dt:

            st.error(
                "Start time must be before end time."
            )

        else:

            st.session_state.labels.append(
                {
                    "annotator": annotator,
                    "date": str(selected_day),
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat(),
                    "label": "SAA"
                }
            )

            st.success(
                "Label Saved"
            )

    except:

        st.error(
            "Invalid timestamp format. Use YYYY-MM-DD HH:MM:SS"
        )

# -------------------------
# COMPLETE DAY
# -------------------------

if st.button("Mark Day Complete"):

    st.session_state.completed_days.add(
        str(selected_day)
    )

    st.success(
        f"{selected_day} marked complete."
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

    completed_df = pd.DataFrame(
        sorted(
            st.session_state.completed_days
        ),
        columns=["Day"]
    )

    st.dataframe(
        completed_df,
        use_container_width=True
    )