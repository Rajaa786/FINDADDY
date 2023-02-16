import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import plotly.figure_factory as ff

st.set_page_config(page_title='BankStatement Dashboard',
                   page_icon=":bar_chart:",
                   layout="wide"
                   )

df = pd.read_excel(
    io='streamlit/BankStatement1.xlsx',
    engine='openpyxl',
    sheet_name='Transaction1'
)

df = df.drop(df.tail(2).index)
st.title(":bar_chart: BankStatement DashBoard")
st.markdown("##")
st.sidebar.header("Please Filter Here:")
Categories = st.sidebar.multiselect(
    'Select the Categories',
    options=df['Categories'].unique(),
    default=df['Categories'].unique()
)

chart_visual = st.sidebar.selectbox('Select Charts/Plot type',
                                    ('Line Chart', 'Bar Chart', 'Bubble Chart'))

selected_status = st.sidebar.selectbox('Select Smoking Status',
                                       options=['Debit',
                                                'Credit', 'Balance',
                                                ])

st.sidebar.header("Select Columns:")
all_columns = df.columns.tolist()
selected_columns = st.sidebar.multiselect(
    "Select columns",
    options=all_columns,
    default=all_columns
)

filtered_df = df[df['Categories'].isin(Categories)][selected_columns]

total_credit = round(float(filtered_df["Credit"].sum()), 2)
total_debit = round(float(filtered_df["Debit"].sum()), 2)
average_balance = round(float(filtered_df["Balance"].mean()), 2)

left_column, middle_column, right_column = st.columns(3)
with left_column:
    st.subheader("Total Credit:")
    st.subheader(f"	₹{total_credit:,}")
with middle_column:
    st.subheader("Total Debit")
    st.subheader(f"₹{total_debit:,}")
with right_column:
    st.subheader("Avg Balance")
    st.subheader(f"₹{average_balance:,}")

st.markdown("---")
# fig = go.Figure()
# if chart_visual == 'Line Chart':
#     if selected_status == 'Debit':
#         fig.add_trace(go.Scatter(x=df['Tran Date'], y=df['Debit'],
#                                  mode='lines',
#                                  name='Debit',
#                                  marker=dict(color='red')))
#     if selected_status == 'Credit':
#         fig.add_trace(go.Scatter(x=df['Tran Date'], y=df['Credit'],
#                                  mode='lines', name='Credit',
#                                  marker=dict(color='green')))
#     if selected_status == 'Balance':
#         fig.add_trace(go.Scatter(x=df['Tran Date'], y=df['Balance'],
#                                  mode='lines',
#                                  name='Balance',
#                                  marker=dict(color='blue')))
# elif chart_visual == 'Bar Chart':
#     if selected_status == 'Debit':
#         fig.add_trace(st.bar_chart(x=df['Tran Date'], y=df['Debit'],
#                                    use_container_width=True))
#     if selected_status == 'Credit':
#         fig.add_trace(st.bar_chart(x=df['Tran Date'], y=df['Credit'],
#                                    use_container_width=True))
#     if selected_status == 'Never_Smoked':
#         fig.add_trace(st.bar_chart(x=df['Tran Date'], y=df['Balance'],
#                                    use_container_width=True))
# elif chart_visual == 'Bubble Chart':
#     if selected_status == 'Debit':
#         fig.add_trace(go.Scatter(x=df['Tran Date'],
#                                  y=df['Debit'],
#                                  mode='markers',
#                                  marker_size=[40, 60, 80, 60, 40, 50],
#                                  name='Debit',
#                                  marker=dict(color='red')))
#
#     if selected_status == 'Credit':
#         fig.add_trace(go.Scatter(x=df['Tran Date'], y=df['Credit'],
#                                  mode='markers',
#                                  marker_size=[40, 60, 80, 60, 40, 50],
#                                  name='Credit',
#                                  marker=dict(color='green')))
#
#     if selected_status == 'Balance':
#         fig.add_trace(go.Scatter(x=df['Tran Date'],
#                                  y=df['Balance'],
#                                  mode='markers',
#                                  marker_size=[40, 60, 80, 60, 40, 50],
#                                  name='Balance',
#                                  marker=dict(color='blue')))
#
# st.plotly_chart(fig, use_container_width=True)

selected_status = st.selectbox(
    'Select the status:', ['Debit', 'Credit', 'Balance'])


chart_data = df[['Debit', 'Credit', 'Balance']]
if selected_status == 'Debit':
    st.bar_chart(chart_data['Debit'])
    st.write("Debit Chart")
elif selected_status == 'Credit':
    st.bar_chart(chart_data['Credit'])
    st.write("Credit Chart")
elif selected_status == 'Balance':
    st.bar_chart(chart_data['Balance'])
    st.write("Balance Chart")


# st.line_chart(df.groupby(["Tran Date"])["Balance"].sum())
# df_agg = df.groupby(["Tran Date"])["Credit", "Debit"].sum()
# st.line_chart(df_agg)


st.dataframe(filtered_df)

st.title("Bar Graph for Bank Transactions")

if st.checkbox("Show Data"):
    st.write(df)

categories = df['Categories'].value_counts()
st.bar_chart(categories)
