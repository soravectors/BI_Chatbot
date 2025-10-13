import streamlit as st
import pandas as pd
import requests
import json
import plotly.express as px

st.set_page_config(page_title="Agentic BI", layout="wide")
st.title("🤖 Agentic BI Platform")
API_URL = "https://soravectors.com/api/agent-query"

st.markdown("### 💡 Ask a question about your data")

# --- Use st.form for "submit on enter" functionality ---
with st.form(key='query_form'):
    query = st.text_input("Your question:", value="What is the total loan amount across all states?")
    submit_button = st.form_submit_button(label='Get Answer')

if submit_button and query:
    with st.spinner("Engaging agent team..."):
        try:
            response = requests.post(API_URL, json={"query": query})
            response.raise_for_status()
            data = response.json()
            
            st.subheader("Results")
            
            # Display the final text answer if it exists
            if data.get("final_answer"):
                st.markdown(data['final_answer'])

            df = None
            if data.get("result_df"):
                result_data = json.loads(data['result_df'])
                df = pd.DataFrame(result_data['data'], columns=result_data['columns'])
            
            # Display chart if instructions are provided
            if data.get("chart_instructions_json") and df is not None and not df.empty:
                st.markdown("#### Generated Chart")
                instructions = json.loads(data['chart_instructions_json'])
                try:
                    # (Chart rendering logic is unchanged)
                    chart_type = instructions.get('chart_type', 'bar').lower()
                    fig = None
                    if chart_type == 'bar':
                        fig = px.bar(df, x=instructions['x_axis'], y=instructions['y_axis'], title=instructions['title'])
                    elif chart_type == 'line':
                        fig = px.line(df, x=instructions['x_axis'], y=instructions['y_axis'], title=instructions['title'])
                    elif chart_type == 'pie':
                        fig = px.pie(df, names=instructions['x_axis'], values=instructions['y_axis'][0], title=instructions['title'])
                    
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Failed to build chart from instructions: {e}")

            # Optionally, always show the data table if a chart was created
            if data.get("chart_instructions_json") and df is not None:
                 st.markdown("#### Data Table")
                 st.dataframe(df)

            # # Show the SQL query for transparency
            # if data.get("sql_query"):
            #     with st.expander("Show Generated SQL Query"):
            #         st.code(data['sql_query'], language='sql')

        except requests.exceptions.RequestException as e:
            st.error(f"API Connection Error: Is the backend running? {e}")
        except Exception as e:
            st.error(f"An error occurred: {e}")