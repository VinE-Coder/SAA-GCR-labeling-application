import pandas as pd
import plotly.graph_objects as go
import gdown
import streamlit as st

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

if "day_index" not in st.session_state:
    st.session_state.day_index = 0

# -------------------------
# HEADER
# -------------------------

st.title("SAA Manual Labeling Tool")

annotator = st.text_input("Volunteer Name")

# -------------------------
# DATE COLUMN
# -------------------------

df["date"] = df["UTC"].dt.date
days = sorted(df["date"].unique())

selected_day = days[st.session_state.day_index]

# -------------------------
# DAY NAVIGATION
# -------------------------

nav1, nav2 = st.columns(2)

with nav1:
    if st.button("Previous Day"):
        st.session_state.day_index = max(0, st.session_state.day_index - 1)

with nav2:
    if st.button("Next Day"):
        st.session_state.day_index = min(len(days) - 1, st.session_state.day_index + 1)

# -------------------------
# DAY DISPLAY
# -------------------------

st.subheader(
    f"Day {st.session_state.day_index + 1} of {len(days)}"
)

st.write(
    f"Date: {selected_day}"
)

# -------------------------
# PROGRESS
# -------------------------

completed = len(st.session_state.completed_days)

st.metric(
    "Completed Days",
    f"{completed}"
)

st.metric(
    "Volunteer Target",
    f"{completed}/10"
)

st.progress(min(completed / 10, 1.0))

# -------------------------
# INSTRUCTIONS
# -------------------------

st.info("""
Instructions

1. Look for a large radiation peak.
2. Identify where the SAA pass begins.
3. Identify where the SAA pass ends.
4. Enter ONLY the times below.
5. Click Save Label.
6. Mark the day complete when finished.

Time Format

HH:MM:SS

Examples

17:02:00
17:14:00

The selected day is automatically added.
Do NOT enter the date.

Rules

• Use UTC time.
• Start time must be before end time.
• One row = one SAA pass.
• Multiple SAA passes can be labeled on the same day.
""")

# -------------------------
# FILTER DAY
# -------------------------

day_df = df[df["date"] == selected_day]
plot_df = day_df.iloc[::10]

# -------------------------
# NASA OVERLAY
# -------------------------

show_nasa = st.checkbox("Show NASA SRAG Labels", value=True)

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

    nasa_df = plot_df[plot_df["SAA"] == 1]

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

st.plotly_chart(fig, use_container_width=True)

# -------------------------
# LABEL ENTRY
# -------------------------

st.write(f"Currently labeling: {selected_day}")

st.subheader("Add SAA Label")

col1, col2 = st.columns(2)

with col1:
    start_time = st.text_input(
        "Start Time (UTC)",
        placeholder="17:02:00"
    )

with col2:
    end_time = st.text_input(
        "End Time (UTC)",
        placeholder="17:14:00"
    )

if st.button("Save Label"):

    try:

        start_dt = pd.to_datetime(
            f"{selected_day} {start_time}",
            utc=True
        )

        end_dt = pd.to_datetime(
            f"{selected_day} {end_time}",
            utc=True
        )

        if start_dt >= end_dt:

            st.error("Start time must be before end time.")

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

            st.success("Label Saved")

    except:

        st.error("Invalid time format. Use HH:MM:SS")

# -------------------------
# COMPLETE DAY
# -------------------------

if st.button("Mark Day Complete"):

    st.session_state.completed_days.add(str(selected_day))

    st.success(f"{selected_day} marked complete.")

# -------------------------
# SAVED LABELS
# -------------------------

st.subheader("Saved Labels")

labels_df = pd.DataFrame(st.session_state.labels)

if len(labels_df) > 0:

    st.write(f"Total Labels: {len(st.session_state.labels)}")

    st.dataframe(labels_df, use_container_width=True)

    csv = labels_df.to_csv(index=False).encode()

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
        sorted(st.session_state.completed_days),
        columns=["Day"]
    )

    st.dataframe(completed_df, use_container_width=True)
