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
API_URL = "https://soravectors.com/api/agent-query"  # Change to your deployed URL when ready

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
        st.session_state["conversation_id"] = str(uuid.uuid4())  # reset ID if needed
        st.session_state["messages"] = []  # ensure messages list is empty
        st.experimental_rerun = lambda: None  # noop, avoids crash


    st.markdown(f"**Conversation ID:** `{st.session_state.conversation_id}`")

# -------------------
# DISPLAY CHAT HISTORY
# -------------------
for msg in st.session_state.messages:
    role = msg["role"]
    content = msg["content"]
    with st.chat_message(role):
        st.markdown(content)

# -------------------
# CHAT INPUT (NEW MESSAGE)
# -------------------
if prompt := st.chat_input("Ask about your data..."):
    # 1️⃣ Show user message immediately
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

    # 3️⃣ Process backend response
    if data.get("final_answer"):
        answer = data["final_answer"]
        with st.chat_message("assistant"):
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})

    # 4️⃣ Display visualization (if provided)
    if data.get("chart_instructions_json") and data.get("result_df"):
        try:
            result_data = json.loads(data["result_df"])
            df = pd.DataFrame(result_data["data"], columns=result_data["columns"])
            instructions = json.loads(data["chart_instructions_json"])
            chart_type = instructions.get("chart_type", "bar").lower()

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

            # Optional: show data table
            st.markdown("#### 🧾 Data Table")
            st.dataframe(df)
        except Exception as e:
            st.error(f"Chart rendering failed: {e}")

    # 5️⃣ Show SQL query (for transparency)
    if data.get("sql_query"):
        with st.expander("Show Generated SQL Query"):
            st.code(data["sql_query"], language="sql")

