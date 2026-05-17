import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import networkx as nx
#from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
import os

# -------------------
# PAGE CONFIG
# -------------------

st.set_page_config(
    page_title="Production AI",
    layout="wide"
)
# -------------------
# PREMIUM UI STYLING
# -------------------

st.markdown(
    """

    <style>

    .stApp {

        background:
        linear-gradient(
            135deg,
            #0b1120,
            #111827,
            #1e293b
        );

        color: #f8fafc;
    }

    section[data-testid="stSidebar"] {

        background:
        linear-gradient(
            180deg,
            #111827,
            #0f172a
        );
    }

    h1 {

        color: #60a5fa !important;

        font-size: 48px !important;

        font-weight: 800 !important;
    }

    h2, h3 {

        color: #93c5fd !important;
    }

    p,
    label,
    .stMarkdown {

        color: #f8fafc !important;
    }

    div[data-testid="metric-container"] {

        background:
        rgba(255,255,255,0.08);

        border:
        1px solid rgba(255,255,255,0.12);

        padding: 20px;

        border-radius: 20px;

        backdrop-filter: blur(10px);

        box-shadow:
        0 8px 24px rgba(0,0,0,0.35);
    }

    .stButton button {

        background:
        linear-gradient(
            135deg,
            #2563eb,
            #1d4ed8
        );

        color: white !important;

        border-radius: 12px;

        border: none;

        padding: 10px 24px;

        font-weight: 700;
    }

    .stButton button:hover {

        background:
        linear-gradient(
            135deg,
            #3b82f6,
            #2563eb
        );
    }

    /* AI STATUS BANNER */

    .ai-banner {

        background:
        linear-gradient(
            135deg,
            rgba(37,99,235,0.25),
            rgba(6,182,212,0.20)
        );

        border:
        1px solid rgba(96,165,250,0.35);

        border-radius: 18px;

        padding: 18px;

        margin-bottom: 25px;

        box-shadow:
        0 0 24px rgba(59,130,246,0.25);

        animation:
        pulseGlow 3s infinite;
    }

    .ai-title {

        color: #f8fafc;

        font-size: 14px;

        font-weight: 600;
    }

    .ai-sub {

        color: #cbd5e1;

        margin-top: 6px;

        font-size: 10px;
        
    }

    @keyframes pulseGlow {

        0% {

            box-shadow:
            0 0 12px rgba(59,130,246,0.18);
        }

        50% {

            box-shadow:
            0 0 28px rgba(59,130,246,0.35);
        }

        100% {

            box-shadow:
            0 0 12px rgba(59,130,246,0.18);
        }
    }
    /* INSIGHT BANNER */

.insight-banner {

    background:
    linear-gradient(
        135deg,
        rgba(37,99,235,0.22),
        rgba(15,23,42,0.92)
    );

    border:
    1px solid rgba(96,165,250,0.35);

    border-radius: 18px;

    padding: 18px;

    margin-top: 20px;

    margin-bottom: 20px;

    color: #f8fafc;

    font-size: 16px;

    font-weight: 600;

    box-shadow:
    0 0 24px rgba(59,130,246,0.25);

    animation:
    insightGlow 2.5s infinite;
}

/* BLINKING GLOW */

@keyframes insightGlow {

    0% {

        box-shadow:
        0 0 10px rgba(59,130,246,0.15);
    }

    50% {

        box-shadow:
        0 0 28px rgba(59,130,246,0.40);
    }

    100% {

        box-shadow:
        0 0 10px rgba(59,130,246,0.15);
    }
}
    
    </style>
    """,

    unsafe_allow_html=True
)
st.title(
    "🏭 Production AI Copilot"
)

st.write(
    "KEY KPI'S"
)


# -------------------
# LOAD AI MODEL
# -------------------

@st.cache_resource
def load_model():

    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0,
        api_key=os.getenv(
            "OPENAI_API_KEY"
        )
    )

    return llm


llm = load_model()
# -------------------
# LOAD DATA
# -------------------

@st.cache_data
def load_data():

    production_df = pd.read_excel(
        "PRODUCTION_DATA.xlsx"
    )

    order_df = pd.read_excel(
        "ORDER_DATA.xlsx"
    )

    defect_df = pd.read_excel(
        "DEFECT_DATA.xlsx"
    )

    material_flow_df = pd.read_excel(
        "MATERIAL_FLOW_DATA.xlsx"
    )

    production_df[
        "PROD_DATE"
    ] = pd.to_datetime(
        production_df[
            "PROD_DATE"
        ]
    )

    master_df = (

        production_df

        .merge(
            order_df,
            on="ORDER_NO",
            how="left"
        )

        .merge(
            defect_df[
                [
                    "MAT_ID",
                    "DEFECT_NAME",
                    "BLOCKING_DEFECT"
                ]
            ],
            on="MAT_ID",
            how="left"
        )
    )

    return (
        production_df,
        master_df,
        material_flow_df
    )

production_df, master_df, material_flow_df = load_data()


# -------------------
# EXECUTIVE KPI DASHBOARD
# -------------------

def show_kpis():

    total_tonnage = (
        production_df[
            "TONNAGE"
        ]
        .sum()
    )

    total_coils = (
        production_df[
            "MAT_ID"
        ]
        .nunique()
    )

    blocked_coils = (
        master_df[
            master_df[
                "BLOCKING_DEFECT"
            ]
            .astype(str)
            .str.upper()
            ==
            "Y"
        ][
            "MAT_ID"
        ]
        .nunique()
    )

    top_defect_df = (
        master_df[
            "DEFECT_NAME"
        ]
        .value_counts()
    )

    if len(top_defect_df) > 0:

        top_defect = (
            top_defect_df
            .index[0]
        )

    else:

        top_defect = "NA"

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "🏭 Total Tonnage",
            f"{total_tonnage:,.2f}"
        )

    with col2:

        st.metric(
            "🧱 Total Coils",
            total_coils
        )

    with col3:

        st.metric(
            "🚫 Blocked Coils",
            blocked_coils
        )

    with col4:

        st.metric(
            "🔥 Top Defect",
            top_defect
        )

show_kpis()
st.markdown(
    """
<div class="ai-banner">

<div class="ai-title">
🟢 AI MANUFACTURING INTELLIGENCE SYSTEM ACTIVE
</div>

<div class="ai-sub">
Real-time production monitoring • Predictive analytics • Smart material flow intelligence
</div>

</div>
""",
    unsafe_allow_html=True
)
# -------------------
# AI INSIGHT BANNER
# -------------------

# -------------------
# AI INSIGHT BANNER
# -------------------




# -------------------
# EXECUTIVE SUMMARY
# -------------------
# -------------------
# EXECUTIVE SUMMARY
# -------------------

def generate_executive_summary(result_df):

    try:

        total_rows = len(result_df)

        if "TONNAGE" in result_df.columns:

            total_tonnage = (
                result_df[
                    "TONNAGE"
                ]
                .sum()
            )

        else:

            total_tonnage = 0

        summary = f"""
🧠 Executive Summary

• Records analyzed: {total_rows}

• Total tonnage impacted: {total_tonnage:,.2f}

• AI Observation:
Operational trends appear stable with active monitoring enabled.
"""

        st.markdown(
            f"""
<div class="insight-banner">
{summary}
</div>
""",
            unsafe_allow_html=True
        )

    except:

        pass
# -------------------
# AI RECOMMENDATION ENGINE
# -------------------

def show_ai_recommendation(message):

    st.markdown(
        f"""
<div class="insight-banner">

🧠 AI Recommendation

<br><br>

{message}

</div>
""",
        unsafe_allow_html=True
    )
# -------------------
# -------------------
# LIVE AI INSIGHTS
# -------------------

import time

insight_placeholder = st.empty()

total_blocked = (
    master_df[
        master_df[
            "BLOCKING_DEFECT"
        ]
        .astype(str)
        .str.upper()
        ==
        "Y"
    ][
        "MAT_ID"
    ]
    .nunique()
)

top_defect_df = (
    master_df[
        "DEFECT_NAME"
    ]
    .value_counts()
)

if len(top_defect_df) > 0:

    top_defect = (
        top_defect_df
        .index[0]
    )

else:

    top_defect = "NA"

top_hall_df = (
    production_df[
        "HALL_LOC"
    ]
    .value_counts()
)

if len(top_hall_df) > 0:

    top_hall = (
        top_hall_df
        .index[0]
    )

else:

    top_hall = "NA"

# -------------------
# SMART DELIVERY INSIGHT
# -------------------

late_orders = 0

if "PROMISED_DELIVERY_DATE" in master_df.columns:

    try:

        today = pd.Timestamp.today()

        active_df = (
            master_df[
                ~master_df[
                    "MAT_ID"
                ]
                .astype(str)
                .isin(
                    material_flow_df[
                        "MAT_ID_PREV"
                    ]
                    .astype(str)
                    .unique()
                )
            ]
        )

        active_df[
            "PROMISED_DELIVERY_DATE"
        ] = pd.to_datetime(
            active_df[
                "PROMISED_DELIVERY_DATE"
            ],
            errors="coerce"
        )

        late_orders = (
            active_df[
                active_df[
                    "PROMISED_DELIVERY_DATE"
                ]
                <
                today
            ]
            .shape[0]
        )

    except:

        late_orders = 0

# -------------------
# INSIGHTS LIST
# -------------------

insights = [

    f"🚫 Active blocked coils: {total_blocked}",

    f"🔥 Highest occurring defect: {top_defect}",

    f"🏭 Most active hall: {top_hall}",

    f"⚠ {late_orders} active coils nearing or crossing delivery target",

    "📈 Production trend remains operationally stable",

    "🧠 AI monitoring material movement intelligence"
]

selected_insight = (
    insights[
        int(time.time())
        %
        len(insights)
    ]
)

insight_placeholder.markdown(
    f"""
<div class="insight-banner">
{selected_insight}
</div>
""",
    unsafe_allow_html=True
)
# -------------------
# TRACE COIL FLOW
# -------------------

def trace_coil_flow(
    start_mat_id
):

    flow = []

    current_id = str(
        start_mat_id
    )

    while True:

        flow.append(
            current_id
        )

        next_row = (
            material_flow_df[
                material_flow_df[
                    "MAT_ID_PREV"
                ]
                .astype(str)
                ==
                current_id
            ]
        )

        if next_row.empty:
            break

        current_id = str(
            next_row.iloc[0][
                "MAT_ID_NEXT"
            ]
        )

    return flow


# -------------------
# CREATE SANKEY
# -------------------

# -------------------
# CREATE SANKEY
# -------------------

def create_sankey(coil_id):

    flow = trace_coil_flow(
        coil_id
    )

    journey = (
        production_df[
            production_df[
                "MAT_ID"
            ]
            .astype(str)
            .isin(flow)
        ]
    )

    if len(journey) < 2:

        return None

    journey = (
        journey
        .sort_values(
            "PROD_DATE"
        )
    )

    labels = [

        f"{row['PROD_UNIT']}<br>{row['MAT_ID']}"

        for _, row
        in journey.iterrows()
    ]

    source = list(
        range(
            len(labels) - 1
        )
    )

    target = list(
        range(
            1,
            len(labels)
        )
    )

    values = (
        journey[
            "TONNAGE"
        ]
        .fillna(1)
        .iloc[:-1]
        .tolist()
    )

    # -------------------
    # NODE COLORS
    # -------------------

    node_colors = [

        "#3b82f6",  # blue
        "#06b6d4",  # cyan
        "#10b981",  # emerald
        "#f59e0b",  # amber
        "#ef4444",  # red
        "#8b5cf6",  # violet
        "#ec4899",  # pink
        "#14b8a6"   # teal
    ]

    node_color_list = [

        node_colors[
            i % len(node_colors)
        ]

        for i in range(
            len(labels)
        )
    ]

    # -------------------
    # LINK COLORS
    # -------------------

    link_colors = [

        "rgba(59,130,246,0.45)",
        "rgba(6,182,212,0.45)",
        "rgba(16,185,129,0.45)",
        "rgba(245,158,11,0.45)",
        "rgba(239,68,68,0.45)",
        "rgba(139,92,246,0.45)"
    ]

    link_color_list = [

        link_colors[
            i % len(link_colors)
        ]

        for i in range(
            len(values)
        )
    ]

    fig = go.Figure(

        data=[
            go.Sankey(

                arrangement="snap",

                node=dict(

                    pad=30,

                    thickness=28,

                    line=dict(
                        color="#e2e8f0",
                        width=1.5
                    ),

                    label=labels,

                    color=node_color_list,

                    hovertemplate=
                    "%{label}<extra></extra>"
                ),

                link=dict(

                    source=source,

                    target=target,

                    value=values,

                    color=link_color_list,

                    hovertemplate=
                    "Flow: %{value}<extra></extra>"
                )
            )
        ]
    )

    fig.update_layout(

        title_text=
        f"🌊 AI Material Flow Intelligence : {coil_id}",

        font_size=14,

        template="plotly_dark",

        height=650,

        paper_bgcolor=
        "rgba(0,0,0,0)",

        plot_bgcolor=
        "rgba(0,0,0,0)",

        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20
        )
    )

    return fig


# QUESTION ENGINE
# -------------------

def ask_question(question):

    q = question.lower()

    # -------------------
       # -------------------
        # -------------------
    # INTERACTIVE HALL MAP
    # -------------------

    if (
        "hall map" in q
        or
        "digital twin" in q
        or
        "hall network" in q
    ):

        flow_df = (
            material_flow_df
            .merge(
                production_df[
                    [
                        "MAT_ID",
                        "HALL_LOC"
                    ]
                ],
                left_on=
                "MAT_ID_PREV",

                right_on=
                "MAT_ID",

                how=
                "left"
            )
            .rename(
                columns={
                    "HALL_LOC":
                    "FROM_HALL"
                }
            )
            .merge(
                production_df[
                    [
                        "MAT_ID",
                        "HALL_LOC"
                    ]
                ],
                left_on=
                "MAT_ID_NEXT",

                right_on=
                "MAT_ID",

                how=
                "left"
            )
            .rename(
                columns={
                    "HALL_LOC":
                    "TO_HALL"
                }
            )
        )

        flow_df = (
            flow_df[
                (
                    flow_df[
                        "FROM_HALL"
                    ]
                    !=
                    flow_df[
                        "TO_HALL"
                    ]
                )
            ]
        )

        hall_moves = (
            flow_df
            .groupby(
                [
                    "FROM_HALL",
                    "TO_HALL"
                ]
            )
            .size()
            .reset_index(
                name=
                "MOVE_COUNT"
            )
        )

        G = nx.DiGraph()

        for _, row in hall_moves.iterrows():

            G.add_edge(
                row["FROM_HALL"],
                row["TO_HALL"],
                weight=
                row["MOVE_COUNT"]
            )

        pos = nx.spring_layout(
            G,
            seed=42
        )

        edge_x = []
        edge_y = []

        for edge in G.edges():

            x0, y0 = pos[edge[0]]

            x1, y1 = pos[edge[1]]

            edge_x.extend(
                [x0, x1, None]
            )

            edge_y.extend(
                [y0, y1, None]
            )

        edge_trace = go.Scatter(

            x=edge_x,

            y=edge_y,

            line=dict(
                width=2,
                color='#60a5fa'
            ),

            hoverinfo='none',

            mode='lines'
        )

        node_x = []
        node_y = []
        node_text = []

        for node in G.nodes():

            x, y = pos[node]

            node_x.append(x)

            node_y.append(y)

            node_text.append(node)

        node_trace = go.Scatter(

            x=node_x,

            y=node_y,

            mode='markers+text',

            text=node_text,

            textposition="top center",

            hoverinfo='text',

            marker=dict(

                size=40,

                color='#2563eb',

                line=dict(
                    width=2,
                    color='white'
                )
            )
        )

        fig = go.Figure(

            data=[
                edge_trace,
                node_trace
            ]
        )

        fig.update_layout(

            title=
            "🏭 Interactive Hall Movement Network",

            template=
            "plotly_dark",

            showlegend=False,

            height=700,

            margin=dict(
                l=20,
                r=20,
                t=60,
                b=20
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        generate_executive_summary(
            hall_moves
        )

        return hall_moves
    # ROOT CAUSE ANALYSIS
    # -------------------

    if (
        "why" in q
        and
        (
            "delay" in q
            or
            "problem" in q
            or
            "issue" in q
            or
            "blocked" in q
        )
    ):

        blocked_df = (
            master_df[
                master_df[
                    "BLOCKING_DEFECT"
                ]
                .astype(str)
                .str.upper()
                ==
                "Y"
            ]
        )

        # -------------------
        # ACTIVE COILS ONLY
        # -------------------

        consumed_coils = (
            material_flow_df[
                "MAT_ID_PREV"
            ]
            .astype(str)
            .unique()
        )

        blocked_df = (
            blocked_df[
                ~blocked_df[
                    "MAT_ID"
                ]
                .astype(str)
                .isin(consumed_coils)
            ]
        )

        total_blocked = (
            blocked_df[
                "MAT_ID"
            ]
            .nunique()
        )

        top_defect_df = (
            blocked_df[
                "DEFECT_NAME"
            ]
            .value_counts()
        )

        if len(top_defect_df) > 0:

            top_defect = (
                top_defect_df
                .index[0]
            )

        else:

            top_defect = "NA"

        hall_df = (
            blocked_df[
                "HALL_LOC"
            ]
            .value_counts()
        )

        if len(hall_df) > 0:

            top_hall = (
                hall_df
                .index[0]
            )

        else:

            top_hall = "NA"

        total_tonnage = (
            blocked_df[
                "TONNAGE"
            ]
            .sum()
        )

        root_cause = f'''

        🧠 AI Root Cause Analysis

        • Active blocked coils:
          {total_blocked}

        • Major contributing defect:
          {top_defect}

        • Highest impacted hall:
          {top_hall}

        • Potential impacted tonnage:
          {total_tonnage:,.2f}

        • AI Observation:
          Operational delays are primarily driven by active blocking defects and unresolved hall congestion.
        '''

        st.markdown(
            f'''
            <div class="insight-banner">
                {root_cause}
            </div>
            ''',
            unsafe_allow_html=True
        )

        return blocked_df[
            [
                "MAT_ID",
                "DEFECT_NAME",
                "HALL_LOC",
                "TONNAGE"
            ]
        ]

    # -------------------
    # TRACK COIL FLOW
    # -------------------
    # -------------------
    # TRACK COIL FLOW
    # -------------------
    if (

        "track" in q

        or

        "flow" in q

        or

        "trace" in q

        or

        "journey" in q

    ):

        words = question.split()

        coil_id = None

        for word in words:

            if any(
                c.isdigit()
                for c in word
            ):

                coil_id = word
                break

        if coil_id:

            flow = trace_coil_flow(
                coil_id
            )

            result = (
                production_df[
                    production_df[
                        "MAT_ID"
                    ]
                    .astype(str)
                    .isin(flow)
                ]
            )

            fig = create_sankey(
                coil_id
            )

            if fig:

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )
            generate_executive_summary(result)

            return result[
                [
                    "MAT_ID",
                    "PROD_DATE",
                    "PROD_UNIT",
                    "TONNAGE"
                ]
            ]

    # -------------------
    # TOTAL TONNAGE
    # -------------------
    elif (
        "total tonnage"
        in q
    ):

        total = (
            production_df[
                "TONNAGE"
            ].sum()
        )

        st.subheader(
            "🏭 Total Tonnage"
        )

        st.metric(
            label="Total Production",
            value=f"{total:.2f}"
        )

        graph_df = (
            production_df
            .groupby(
                "PROD_UNIT"
            )[
                "TONNAGE"
            ]
            .sum()
            .reset_index()
        )

        fig = go.Figure(
            data=[
                go.Bar(
                    x=graph_df[
                        "PROD_UNIT"
                    ],
                    y=graph_df[
                        "TONNAGE"
                    ],
                    text=graph_df[
                        "TONNAGE"
                    ].round(2),
                    textposition='outside'
                )
            ]
        )

        fig.update_layout(
            template="plotly_dark",
            height=500
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )
        
        return graph_df

    # -------------------
    # DEFECT QUERIES
    # -------------------
    elif (

        "defect" in q

        or

        "defects" in q

    ):

        if (
            "unit" in q
            or
            "prod unit" in q
        ):

            result = (
                master_df
                .groupby(
                    [
                        "PROD_UNIT",
                        "DEFECT_NAME"
                    ],
                    dropna=False
                )
                .size()
                .reset_index(
                    name="COUNT"
                )
                .sort_values(
                    "COUNT",
                    ascending=False
                )
            )
            generate_executive_summary(result)
            return result

        else:

            result = (
                master_df
                .groupby(
                    "DEFECT_NAME",
                    dropna=False
                )
                .size()
                .reset_index(
                    name="COUNT"
                )
                .sort_values(
                    "COUNT",
                    ascending=False
                )
            )
            generate_executive_summary(result)
            return result

    # -------------------
    # TONNAGE BY UNIT BY MONTH
    # -------------------
    elif (

        "tonnage" in q

        and

        "unit" in q

        and

        "month" in q

    ):

        temp_df = (
            production_df
            .copy()
        )

        temp_df[
            "MONTH"
        ] = (
            temp_df[
                "PROD_DATE"
            ]
            .dt.strftime(
                "%Y-%m"
            )
        )

        result = (
            temp_df
            .groupby(
                [
                    "MONTH",
                    "PROD_UNIT"
                ]
            )[
                "TONNAGE"
            ]
            .sum()
            .reset_index()
        )

        st.subheader(
            "📊 Monthly Tonnage by Production Unit"
        )

        fig = go.Figure()

        units = (
            result[
                "PROD_UNIT"
            ]
            .unique()
        )

        for unit in units:

            unit_df = (
                result[
                    result[
                        "PROD_UNIT"
                    ]
                    ==
                    unit
                ]
            )

            fig.add_trace(
                go.Scatter(
                    x=unit_df[
                        "MONTH"
                    ],
                    y=unit_df[
                        "TONNAGE"
                    ],
                    mode='lines+markers',
                    name=str(unit)
                )
            )

        fig.update_layout(
            height=600,
            xaxis_title="Month",
            yaxis_title="Tonnage",
            template="plotly_dark"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )
        generate_executive_summary(result)
        return result

    # -------------------
    # TONNAGE BY DAY
    # -------------------
    elif (

        "daily" in q

        and

        "tonnage" in q

    ):

        temp_df = (
            production_df
            .copy()
        )

        temp_df[
            "DAY"
        ] = (
            temp_df[
                "PROD_DATE"
            ]
            .dt.strftime(
                "%Y-%m-%d"
            )
        )

        result = (
            temp_df
            .groupby(
                "DAY"
            )[
                "TONNAGE"
            ]
            .sum()
            .reset_index()
        )

        st.subheader(
            "📅 Daily Tonnage Trend"
        )

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=result[
                    "DAY"
                ],
                y=result[
                    "TONNAGE"
                ],
                mode='lines+markers',
                fill='tozeroy'
            )
        )

        fig.update_layout(
            height=500,
            template="plotly_dark",
            xaxis_title="Day",
            yaxis_title="Tonnage"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )
        generate_executive_summary(result)
        return result
      # -------------------
    # COIL MOVEMENT BETWEEN HALLS BY WEEK
    # -------------------
    elif (

        (
            "hall" in q
            and
            "movement" in q
        )

        or

        (
            "moving between hall"
            in q
        )

        or

        (
            "hall transfer"
            in q
        )

    ):

        movement_df = (
            material_flow_df
            .copy()
        )

        # PREVIOUS COIL DETAILS
        prev_df = (
            production_df[
                [
                    "MAT_ID",
                    "HALL_LOC",
                    "TONNAGE",
                    "PROD_DATE"
                ]
            ]
            .rename(
                columns={
                    "MAT_ID":
                    "MAT_ID_PREV",

                    "HALL_LOC":
                    "FROM_HALL",

                    "TONNAGE":
                    "TONNAGE",

                    "PROD_DATE":
                    "MOVE_DATE"
                }
            )
        )

        # NEXT COIL DETAILS
        next_df = (
            production_df[
                [
                    "MAT_ID",
                    "HALL_LOC"
                ]
            ]
            .rename(
                columns={
                    "MAT_ID":
                    "MAT_ID_NEXT",

                    "HALL_LOC":
                    "TO_HALL"
                }
            )
        )

        movement_df = (
            movement_df
            .merge(
                prev_df,
                on="MAT_ID_PREV",
                how="left"
            )
            .merge(
                next_df,
                on="MAT_ID_NEXT",
                how="left"
            )
        )

        # REMOVE SAME HALL MOVEMENTS
        movement_df = (
            movement_df[
                movement_df[
                    "FROM_HALL"
                ]
                !=
                movement_df[
                    "TO_HALL"
                ]
            ]
        )

        movement_df[
            "WEEK"
        ] = (
            pd.to_datetime(
                movement_df[
                    "MOVE_DATE"
                ]
            )
            .dt.strftime(
                "%Y-W%U"
            )
        )

        result = (
            movement_df
            .groupby(
                [
                    "WEEK",
                    "FROM_HALL",
                    "TO_HALL"
                ]
            )
            .agg(
                COIL_COUNT=(
                    "MAT_ID_PREV",
                    "count"
                ),

                TOTAL_TONNAGE=(
                    "TONNAGE",
                    "sum"
                )
            )
            .reset_index()
            .sort_values(
                "TOTAL_TONNAGE",
                ascending=False
            )
        )

        st.subheader(
            "🏭 Coil Movement Between Halls by Week"
        )

        st.dataframe(
            result,
            use_container_width=True
        )

                # -------------------
        # SANKEY GRAPH
        # -------------------

        sankey_df = (
            result
            .groupby(
                [
                    "FROM_HALL",
                    "TO_HALL"
                ]
            )[
                "TOTAL_TONNAGE"
            ]
            .sum()
            .reset_index()
        )

        labels = list(
            pd.concat(
                [
                    sankey_df[
                        "FROM_HALL"
                    ],

                    sankey_df[
                        "TO_HALL"
                    ]
                ]
            )
            .unique()
        )

        source = (
            sankey_df[
                "FROM_HALL"
            ]
            .apply(
                lambda x:
                labels.index(x)
            )
            .tolist()
        )

        target = (
            sankey_df[
                "TO_HALL"
            ]
            .apply(
                lambda x:
                labels.index(x)
            )
            .tolist()
        )

        values = (
            sankey_df[
                "TOTAL_TONNAGE"
            ]
            .tolist()
        )

        fig = go.Figure(
            data=[
                go.Sankey(
                    node=dict(
                        pad=20,
                        thickness=20,
                        label=labels
                    ),

                    link=dict(
                        source=source,
                        target=target,
                        value=values
                    )
                )
            ]
        )

        fig.update_layout(
            title=
            "🏭 Hall Movement Sankey Flow",

            template="plotly_dark",

            height=700
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )
        st.plotly_chart(
            fig,
            use_container_width=True
        )
        generate_executive_summary(result)
        return result
    # -------------------
    # TONNAGE BY WEEK
    # -------------------
    elif (

        "week" in q

        and

        "tonnage" in q

    ):

        temp_df = (
            production_df
            .copy()
        )

        temp_df[
            "WEEK"
        ] = (
            temp_df[
                "PROD_DATE"
            ]
            .dt.strftime(
                "%Y-W%U"
            )
        )

        result = (
            temp_df
            .groupby(
                "WEEK"
            )[
                "TONNAGE"
            ]
            .sum()
            .reset_index()
        )

        st.subheader(
            "📆 Weekly Tonnage Trend"
        )

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=result[
                    "WEEK"
                ],
                y=result[
                    "TONNAGE"
                ],
                text=result[
                    "TONNAGE"
                ].round(2),
                textposition='outside'
            )
        )

        fig.update_layout(
            height=500,
            template="plotly_dark",
            xaxis_title="Week",
            yaxis_title="Tonnage"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )
        generate_executive_summary(result)
        return result

    # -------------------
    # TONNAGE BY MONTH
    # -------------------
    elif (

        "month" in q

        and

        "tonnage" in q

    ):

        monthly_df = (
            production_df
            .copy()
        )

        monthly_df[
            "MONTH"
        ] = (
            monthly_df[
                "PROD_DATE"
            ]
            .dt.strftime(
                "%Y-%m"
            )
        )

        result = (
            monthly_df
            .groupby(
                "MONTH"
            )[
                "TONNAGE"
            ]
            .sum()
            .reset_index()
        )

        st.subheader(
            "📈 Monthly Production Trend"
        )

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=result[
                    "MONTH"
                ],
                y=result[
                    "TONNAGE"
                ],
                mode='lines+markers',
                fill='tozeroy'
            )
        )

        fig.update_layout(
            height=500,
            xaxis_title="Month",
            yaxis_title="Tonnage",
            template="plotly_dark"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )
        generate_executive_summary(result)
        return result

    # -------------------
    # TONNAGE BY UNIT
    # -------------------
    elif (

        (
            "tonnage" in q
            and
            "unit" in q
        )

        or

        "tonnage by unit"
        in q

        or

        "production unit tonnage"
        in q

    ):

        result = (
            production_df
            .groupby(
                "PROD_UNIT",
                dropna=False
            )[
                "TONNAGE"
            ]
            .sum()
            .reset_index()
        )

        st.subheader(
            "🏭 Tonnage by Production Unit"
        )

        fig = go.Figure(
            data=[
                go.Bar(
                    x=result[
                        "PROD_UNIT"
                    ],
                    y=result[
                        "TONNAGE"
                    ],
                    text=result[
                        "TONNAGE"
                    ].round(2),
                    textposition='outside'
                )
            ]
        )

        fig.update_layout(
            height=500,
            xaxis_title="Production Unit",
            yaxis_title="Tonnage",
            template="plotly_dark"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )
        generate_executive_summary(result)
        return result

      # -------------------
    # BLOCKED COILS FOR GALVANIZING
    # -------------------
    elif (

        "galvan" in q

        and

        (
            "blocked" in q
            or
            "blocking" in q
        )

    ):

        blocked_df = (
            master_df[
                master_df[
                    "BLOCKING_DEFECT"
                ]
                .astype(str)
                .str.upper()
                ==
                "Y"
            ]
            .copy()
        )

        # ONLY COILS HAVING GALVANIZING IN ROUTE
        blocked_df = (
            blocked_df[
                blocked_df[
                    "ROUTE"
                ]
                .astype(str)
                .str.upper()
                .str.contains(
                    "GALV",
                    na=False
                )
            ]
        )

        # REMOVE ALREADY CONSUMED COILS
        consumed_coils = (
            material_flow_df[
                "MAT_ID_PREV"
            ]
            .astype(str)
            .unique()
        )

        blocked_df = (
            blocked_df[
                ~blocked_df[
                    "MAT_ID"
                ]
                .astype(str)
                .isin(
                    consumed_coils
                )
            ]
        )

        result = (
            blocked_df[
                [
                    "MAT_ID",
                    "ROUTE",
                    "DEFECT_NAME",
                    "PROD_UNIT",
                    "TONNAGE"
                ]
            ]
        )

        st.subheader(
            "🚫 Active Blocked Coils for Galvanizing"
        )

        st.dataframe(
            result,
            use_container_width=True
        )

        # VISUALIZATION
        graph_df = (
            result
            .groupby(
                "PROD_UNIT"
            )[
                "TONNAGE"
            ]
            .sum()
            .reset_index()
        )

        fig = go.Figure(
            data=[
                go.Bar(
                    x=graph_df[
                        "PROD_UNIT"
                    ],
                    y=graph_df[
                        "TONNAGE"
                    ],
                    text=graph_df[
                        "TONNAGE"
                    ].round(2),
                    textposition='outside'
                )
            ]
        )

        fig.update_layout(
            title="🚫 Active Blocked Galvanizing Coils by Unit",
            template="plotly_dark",
            height=500,
            xaxis_title="Production Unit",
            yaxis_title="Blocked Tonnage"
        )

        
        generate_executive_summary(result)
        show_ai_recommendation(

                "Prioritize blocked upstream coils before galvanizing to reduce downstream production congestion and delivery risk."
        )
        st.plotly_chart(
            fig,
            use_container_width=True
        )
        return result

    # -------------------
    # BLOCKING DEFECTS
    # -------------------
    elif (

        "blocking"
        in q

        or

        "blocked"
        in q

    ):

        result = (
            master_df[
                master_df[
                    "BLOCKING_DEFECT"
                ]
                .astype(str)
                .str.upper()
                == "Y"
            ]
        )

        return result[
            [
                "MAT_ID",
                "DEFECT_NAME",
                "PROD_UNIT"
            ]
        ]

    # -------------------
    # DEFECT HEATMAP
    # -------------------
    elif (

        "heatmap" in q

        or

        "defect map" in q

    ):

        heatmap_df = (
            master_df
            .groupby(
                [
                    "PROD_UNIT",
                    "DEFECT_NAME"
                ]
            )
            .size()
            .reset_index(
                name="COUNT"
            )
        )

        pivot_df = (
            heatmap_df
            .pivot(
                index="DEFECT_NAME",
                columns="PROD_UNIT",
                values="COUNT"
            )
            .fillna(0)
        )

        fig = go.Figure(
            data=go.Heatmap(
                z=pivot_df.values,
                x=pivot_df.columns,
                y=pivot_df.index
            )
        )

        fig.update_layout(
            title="🔥 Defect Heatmap",
            height=700,
            template="plotly_dark"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        return heatmap_df

    # -------------------
    # ORDER DETAIL QUERY
    # -------------------
    elif "order" in q:

        words = question.split()

        order_id = None

        for word in words:

            if any(
                c.isdigit()
                for c in word
            ):

                order_id = word
                break

        if order_id:

            result = (
                master_df[
                    master_df[
                        "ORDER_NO"
                    ]
                    .astype(str)
                    ==
                    order_id
                ]
            )
            generate_executive_summary(result)
            return result

    # -------------------
    # COIL DETAIL QUERY
    # -------------------
    elif any(
        c.isdigit()
        for c in q
    ):

        words = question.split()

        coil_id = None

        for word in words:

            if any(
                c.isdigit()
                for c in word
            ):

                coil_id = word
                break

        if coil_id:

            result = (
                master_df[
                    master_df[
                        "MAT_ID"
                    ]
                    .astype(str)
                    ==
                    coil_id
                ]
            )

            return result
    # -------------------
    # HALL HEAT MAP
    # -------------------

    elif (
        "heat map" in q
        or
        "heatmap" in q
    ):

        hall_df = (
            production_df
            .groupby(
                "HALL_LOC"
            )[
                "TONNAGE"
            ]
            .sum()
            .reset_index()
        )

        fig = go.Figure(
            go.Treemap(

                labels=
                hall_df[
                    "HALL_LOC"
                ],

                parents=
                [""] * len(hall_df),

                values=
                hall_df[
                    "TONNAGE"
                ],

                textinfo=
                "label+value",

                marker=dict(
                    colors=
                    hall_df[
                        "TONNAGE"
                    ],
                    colorscale=
                    "Blues"
                )
            )
        )

        fig.update_layout(

            title=
            "🏭 Hall Tonnage Heat Map",

            template=
            "plotly_dark",

            height=600
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        generate_executive_summary(
            hall_df
        )

        return hall_df    # -------------------
    # PREDICTIVE INTELLIGENCE
    # -------------------

    if (
        "predict" in q
        or
        "future risk" in q
        or
        "bottleneck" in q
    ):

        blocked_df = (
            master_df[
                master_df[
                    "BLOCKING_DEFECT"
                ]
                .astype(str)
                .str.upper()
                ==
                "Y"
            ]
        )

        # ACTIVE COILS ONLY

        consumed_coils = (
            material_flow_df[
                "MAT_ID_PREV"
            ]
            .astype(str)
            .unique()
        )

        blocked_df = (
            blocked_df[
                ~blocked_df[
                    "MAT_ID"
                ]
                .astype(str)
                .isin(consumed_coils)
            ]
        )

        hall_risk_df = (

            blocked_df
            .groupby(
                "HALL_LOC"
            )
            .agg({

                "MAT_ID": "count",

                "TONNAGE": "sum"
            })
            .reset_index()
        )

        hall_risk_df.columns = [

            "HALL_LOC",

            "BLOCKED_COILS",

            "TOTAL_TONNAGE"
        ]

        high_risk = (
            hall_risk_df[
                hall_risk_df[
                    "BLOCKED_COILS"
                ]
                >
                hall_risk_df[
                    "BLOCKED_COILS"
                ]
                .mean()
            ]
        )

        risk_summary = f"""

🧠 Predictive Intelligence Report

• High-risk halls detected:
  {len(high_risk)}

• Total active blocked tonnage:
  {hall_risk_df['TOTAL_TONNAGE'].sum():,.2f}

• AI Observation:
  Rising blocked coil concentration indicates potential future bottlenecks and production delays.

"""

        st.markdown(
            f"""
<div class="insight-banner">
{risk_summary}
</div>
""",
            unsafe_allow_html=True
        )

        fig = go.Figure(

            data=[
                go.Bar(

                    x=
                    hall_risk_df[
                        "HALL_LOC"
                    ],

                    y=
                    hall_risk_df[
                        "BLOCKED_COILS"
                    ],

                    text=
                    hall_risk_df[
                        "BLOCKED_COILS"
                    ],

                    textposition="outside",

                    marker_color=
                    "#ef4444"
                )
            ]
        )

        fig.update_layout(

            title=
            "⚠ Predicted Bottleneck Risk by Hall",

            template=
            "plotly_dark",

            height=550
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        return hall_risk_df


    # -------------------
    # AI FALLBACK
    # -------------------
    else:

        prompt = f"""
You are a manufacturing data analyst.

Dataframe name:
master_df

Columns:
{list(master_df.columns)}

Important meanings:

MAT_ID = coil id / coil number
ORDER_NO = production order number
TONNAGE = production weight
PROD_UNIT = production unit
DEFECT_NAME = defect
BLOCKING_DEFECT = blocked
PROMISED_DELIVERY_DATE = due date

Question:
{question}

Rules:
1. Write ONLY executable pandas code
2. Use dataframe master_df
3. ALWAYS assign final output to variable result
4. Do not explain anything
5. Do not use markdown
"""

        response = llm.invoke(
            prompt
        )

        generated_code = (
            response.content
        )

        generated_code = (
            generated_code
            .replace(
                "```python",
                ""
            )
            .replace(
                "```",
                ""
            )
            .strip()
        )

        if (
            "result ="
            not in generated_code
        ):

            generated_code = (
                "result = "
                + generated_code
            )

        st.code(
            generated_code,
            language="python"
        )

        local_scope = {
            "master_df":
            master_df,
            "pd": pd
        }

        try:

            exec(
                generated_code,
                {},
                local_scope
            )

            return local_scope[
                "result"
            ]

        except Exception as e:

            return (
                f"AI generated invalid code:\n\n{e}"
            )


# -------------------
# USER INTERFACE
# -------------------

question = st.text_input(
    "Ask a question"
)

if st.button(
    "Ask"
):

    with st.spinner(
        "Thinking..."
    ):

        result = ask_question(
            question
        )

        st.write(
            result
        )