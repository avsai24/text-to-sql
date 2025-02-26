import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import google.generativeai as genai

genai.configure(api_key="AIzaSyApH0l3NSqDZd5wtdRD4ISR0Y6V5v0ZtWA")  

DATABASES = ["student.db","employees.db","sales.db"]

PROMPT = """
You are an expert in converting English questions into SQL queries and determining the correct database.

Databases and their tables:
1. student.db → STUDENT (NAME, CLASS, AGE, MARKS)
2. employees.db → EMPLOYEES (NAME, DEPARTMENT, SALARY, EXPERIENCE)
3. sales.db → SALES (PRODUCT, REGION, SALES, REVENUE)

For each question, return the **correct database name** and **valid SQL query**.
**Do not include the database name in the SQL query itself.** 

Format:
<DB_NAME> | <SQL_QUERY>

### Examples:
1. **User:** How many students are in AI class?
   **Response:** student.db | SELECT COUNT(*) FROM STUDENT WHERE CLASS='AI';

2. **User:** What is the average salary of IT employees?
   **Response:** employees.db | SELECT AVG(SALARY) FROM EMPLOYEES WHERE DEPARTMENT='IT';

3. **User:** Total revenue in North region?
   **Response:** sales.db | SELECT SUM(REVENUE) FROM SALES WHERE REGION='North';
"""

def get_sql_query_and_db(question):
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content([PROMPT, question])
    output = response.text.strip()
    # st.markdown(f"**Output:** {output}")
    try:
        db_name, sql_query = output.split(" | ")
        if db_name in DATABASES:
            return db_name, sql_query
    except ValueError:
        st.error("Failed to extract database or SQL query from AI response.")
        return None, None

def get_response_from_db(sql_query, db_path):
    
    try:
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(sql_query, conn)
            return df
    except Exception as e:
        st.error(f"SQL Error: {e}")
        return None

def chart_type_from_question(question):
    if "bar" in question:
        return "bar"
    elif "histogram" in question:
        return "histogram"
    elif "scatter" in question:
        return "scatter"
    elif "line" in question:
        return "line"
    elif "pie" in question:
        return "pie"
    else:
        return None

def determine_chart_type(df):
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

    if len(numeric_cols) == 0:
        return None 

    if categorical_cols and numeric_cols:
        if len(numeric_cols) == 1:  
            if len(df[categorical_cols[0]].unique()) <= 3: 
                return "pie"
        return "bar" 
    elif len(numeric_cols) == 1:
        return "histogram" 
    elif len(numeric_cols) == 2:
        return "scatter" 
    elif len(numeric_cols) > 2:
        return "line"  

    return None 

def display_message(chart_type_question, chart_type):
    if chart_type_question is None and chart_type is None:
        st.markdown("**Cannot provide any chart diagrams** due to insufficient data.")
    elif chart_type_question is None and chart_type is not None:
        st.markdown(f"**You did not mention any chart type in your prompt.** We suggest using a **{chart_type} chart** based on the data.")
    elif chart_type_question != chart_type:
        st.markdown(f"**The requested {chart_type_question} chart is not suitable for the data.** Instead, we suggest a **{chart_type} chart.**")
    else:
        st.markdown(f"**Here is your requested {chart_type_question} chart.**")

def generate_chart(df, chart_type):
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

    if df.empty or chart_type == None:
        st.warning("The DataFrame is empty or No chart to display.")
        return

    fig, ax = plt.subplots(figsize=(8, 5))

    if chart_type == "bar":
        if categorical_cols and numeric_cols:
            df.plot(kind="bar", x=categorical_cols[0], y=numeric_cols[0], ax=ax)
        else:
            st.warning("Bar chart requires at least one categorical and one numeric column.")

    elif chart_type == "line":
        if len(numeric_cols) >= 2:
            df.plot(kind="line", x=numeric_cols[0], y=numeric_cols[1], ax=ax)
        else:
            st.warning("Line chart requires at least two numeric columns.")

    elif chart_type == "scatter":
        if len(numeric_cols) >= 2:
            df.plot(kind="scatter", x=numeric_cols[0], y=numeric_cols[1], ax=ax)
        else:
            st.warning("Scatter plot requires at least two numeric columns.")

    elif chart_type == "histogram":
        if len(numeric_cols) >= 1:
            df[numeric_cols[0]].plot(kind="hist", ax=ax, bins=10)
        else:
            st.warning("Histogram requires at least one numeric column.")

    elif chart_type == "pie":
        if categorical_cols and len(df[categorical_cols[0]].unique()) <= 10:
            df.set_index(categorical_cols[0])[numeric_cols[0]].plot(kind="pie", autopct="%1.1f%%", ax=ax)
            plt.ylabel("") 
        else:
            st.warning("Pie chart requires a categorical column with ≤10 unique values.")
            



    plt.xticks(rotation=45)
    plt.grid(True)
    st.pyplot(fig)

st.title("Multi-Database AI Query and Visualization")

question = st.text_input("Enter your question")
submit = st.button("Generate")

if submit:
    db_path, sql_query = get_sql_query_and_db(question)
    
    if db_path and sql_query:
        st.markdown(f"**Database Selected:** {db_path}")
        st.markdown(f"**SQL Query:** {sql_query}")

        df = get_response_from_db(sql_query, db_path)
        if df is not None and not df.empty:
            st.table(df)

            chart_type_question = chart_type_from_question(question)
            chart_type = determine_chart_type(df)
            st.markdown(f"**Chart Type In Question:** {chart_type_question}")
            st.markdown(f"**Chart Type Detected:** {chart_type}")

            display_message(chart_type_question,chart_type)
            
            if chart_type:
                st.markdown("### Data Visualization")
                generate_chart(df, chart_type)
            else:
                st.warning("No suitable chart type found for the retrieved data.")