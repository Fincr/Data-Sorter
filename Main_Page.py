"""Data Sorter — landing page with carrier selection."""

import streamlit as st

st.set_page_config(page_title="Data Sorter", page_icon="📬", layout="wide")

st.title("📬 Data Sorter")
st.markdown("Select a carrier sorter to get started.")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Lettershop - Ireland")
    st.markdown(
        "Classify Irish addresses into **Lettershop** and **National** "
        "routing buckets. Supports Eircode, Dublin district, and keyword-based "
        "area matching."
    )
    if st.button("Open", key="open_lettershop_ireland", type="primary"):
        st.switch_page("pages/1_Lettershop_Ireland.py")
