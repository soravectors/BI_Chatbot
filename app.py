import streamlit as st
import pandas as pd
import requests
import json
import plotly.express as px
import uuid

# -------------------
# BASIC CONFIGURATION
# -------------------
st.set_page_config(page_title="Agentic BI", layout="wide")
st.title("🤖 Agentic BI Platform")
API_URL = "https://soravectors.com/api/agent-query"  # Change to your deployed URL

# -------------------
# SESSION MANAGEMENT
# -------------------
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

# -------------------
# SIDEBAR CONTROLS
# -------------------
with st.sidebar:
    st.markdown("### 💬 Conversation Controls")
    if st.button("🧹 Clear Conversation"):
        st.session_state.clear()
        st.session_state["conversation_id"] = str(uuid.uuid4())
        st.session_state["messages"] = []
        st.experimental_rerun()

    st.markdown(f"**Conversation ID:** `{st.session_state.conversation_id}`")

# -------------------
# DISPLAY CHAT HISTORY
# -------------------
for msg in st.session_state.messages:
    role = msg["role"]
    with st.chat_message(role):
        st.markdown(msg["content"])
        # display chart/table if stored in the message
        if "chart_data" in msg:
            df = pd.DataFrame(msg["chart_data"]["data"], columns=msg["chart_data"]["columns"])
            st.markdown("#### 📊 Chart (from history)")
            st.plotly_chart(msg["chart_obj"], use_container_width=True)
        if "table_data" in msg:
            df = pd.DataFrame(msg["table_data"]["data"], columns=msg["table_data"]["columns"])
            st.markdown("#### 🧾 Data Table (from history)")
            st.dataframe(df)

# -------------------
# CHAT INPUT
# -------------------
if prompt := st.chat_input("Ask about your data..."):
    # 1️⃣ Show user message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2️⃣ Send to backend
    with st.spinner("Engaging agent team..."):
        try:
            response = requests.post(
                API_URL,
                json={
                    "query": prompt,
                    "conversation_id": st.session_state.conversation_id
                },
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            st.error(f"API error: {e}")
            st.stop()

    # 3️⃣ Build assistant response
    assistant_msg = {"role": "assistant", "content": ""}

    # Text / final answer
    if data.get("final_answer"):
        answer = data["final_answer"]
        assistant_msg["content"] = answer
        with st.chat_message("assistant"):
            st.markdown(answer)

    # 4️⃣ Handle chart/table output
    if data.get("result_df"):
        try:
            result_data = json.loads(data["result_df"])
            df = pd.DataFrame(result_data["data"], columns=result_data["columns"])

            chart_instructions = data.get("chart_instructions_json")
            show_chart = False
            show_table = False

            if chart_instructions:
                try:
                    instructions = json.loads(chart_instructions)
                    chart_type = instructions.get("chart_type", "").lower()
                    show_chart = True
                except Exception:
                    show_chart = False

            with st.chat_message("assistant"):
                if show_chart:
                    st.markdown("#### 📊 Generated Chart")
                    if chart_type == "bar":
                        fig = px.bar(df, x=instructions["x_axis"], y=instructions["y_axis"], title=instructions["title"])
                    elif chart_type == "line":
                        fig = px.line(df, x=instructions["x_axis"], y=instructions["y_axis"], title=instructions["title"])
                    elif chart_type == "pie":
                        fig = px.pie(df, names=instructions["x_axis"], values=instructions["y_axis"][0], title=instructions["title"])
                    else:
                        fig = None

                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                        assistant_msg["chart_data"] = result_data
                        assistant_msg["chart_obj"] = fig
                    else:
                        st.warning("Unknown chart type.")

                # show table if chart missing or both are needed
                if not show_chart or data.get("show_table", True):
                    st.markdown("#### 🧾 Data Table")
                    st.dataframe(df)
                    assistant_msg["table_data"] = result_data

        except Exception as e:
            st.error(f"Chart/Table rendering failed: {e}")

    # 5️⃣ Show SQL query
    if data.get("sql_query"):
        with st.expander("Show Generated SQL Query"):
            st.code(data["sql_query"], language="sql")

    # 6️⃣ Save assistant response to history
    st.session_state.messages.append(assistant_msg)

