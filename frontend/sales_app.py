import streamlit as st



home_page = st.Page(
    page ="Pages/home.py",
    title ="Home Page",
    default = True,
)

sales_Analytics = st.Page(
    page ="frontend/sales4.py",
    title ="sales Page",
)

pg = st.navigation(pages=[home_page,sales_Analytics])

pg.run()