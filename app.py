import streamlit as st
import pandas as pd
import plotly.graph_objects as go
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

st.title(
    "🏭 Production AI Copilot"
)

st.write(
    "Ask production-related questions"
)

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


(
    production_df,
    master_df,
    material_flow_df
) = load_data()

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

def create_sankey(
    coil_id
):

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

    labels = []

    for _, row in (
        journey.iterrows()
    ):

        labels.append(
            f"{row['PROD_UNIT']}\n{row['MAT_ID']}"
        )

    source = list(
        range(
            len(labels)-1
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

    fig = go.Figure(
        data=[
            go.Sankey(
                node=dict(
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
        title_text=f"Coil Flow: {coil_id}",
        font_size=12,
        template="plotly_dark"
    )

    return fig


# -------------------
# QUESTION ENGINE
# -------------------

def ask_question(
    question
):

    q = question.lower()

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