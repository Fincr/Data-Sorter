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

with col2:
    st.subheader("Correos - Spain")
    st.markdown(
        "Classify Spanish addresses into **D1** and **D2** routing "
        "based on postal codes. D1 covers capitals, administrations, "
        "and cities with over 50,000 inhabitants."
    )
    if st.button("Open", key="open_correos_spain", type="primary"):
        st.switch_page("pages/3_Correos_Spain.py")
