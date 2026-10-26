import streamlit as st



home_page = st.Page(
    page="sample.py",
    title ="Home Page",
    default = True,
)

sales_Analytics = st.Page(
    page="sales4.py",
    title ="sales Page",
)

pg = st.navigation(pages=[home_page,sales_Analytics])

pg.run()