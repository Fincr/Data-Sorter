"""Streamlit config editor page — edit classification rules and column aliases."""

from pathlib import Path

import streamlit as st

from src.config_editor import (
    load_columns_config,
    load_rules_config,
    save_columns_config,
    save_rules_config,
)

st.set_page_config(page_title="Configuration", page_icon="⚙️", layout="wide")

CONFIG_DIR = Path(__file__).parent.parent / "config"
RULES_PATH = CONFIG_DIR / "rules.yaml"
COLUMNS_PATH = CONFIG_DIR / "columns.yaml"

st.title("⚙️ Configuration Editor")
st.info("Changes are saved to disk and take effect on the next processing run.")

# ---------------------------------------------------------------------------
# Session state helpers
# ---------------------------------------------------------------------------

def _init_rules_state():
    """Load rules config into session state if not already present."""
    if "rules_loaded" not in st.session_state:
        data = load_rules_config(RULES_PATH)
        ireland = data.get("countries", {}).get("ireland", {})

        st.session_state.country_patterns = ireland.get("country_patterns", [])

        # Eircode routing — list of (prefix, area) tuples for ordered editing
        eircode_dict = ireland.get("eircode_routing", {})
        st.session_state.eircode_rows = [
            {"prefix": k, "area": v} for k, v in eircode_dict.items()
        ]

        areas = ireland.get("areas", {})

        # Lettershop
        ls = areas.get("lettershop_areas", {})
        st.session_state.lettershop_keywords = [
            {"area": e["area"], "patterns": list(e.get("patterns", []))}
            for e in ls.get("keywords", [])
        ]

        # National
        na = areas.get("national_areas", {})
        st.session_state.national_keywords = [
            {"area": e["area"], "patterns": list(e.get("patterns", []))}
            for e in na.get("keywords", [])
        ]

        # Dublin districts (read-only)
        dd = areas.get("dublin_districts", {})
        st.session_state.dublin_districts = dd.get("districts", [])
        st.session_state.dublin_routing = dd.get("routing", "LETTERSHOP")

        # Ireland other fallback (read-only)
        io_cfg = areas.get("ireland_other", {})
        st.session_state.ireland_other_area = io_cfg.get("area", "Ireland Other")
        st.session_state.ireland_other_routing = io_cfg.get("routing", "NATIONAL")

        st.session_state.rules_loaded = True


def _init_columns_state():
    """Load columns config into session state if not already present."""
    if "columns_loaded" not in st.session_state:
        data = load_columns_config(COLUMNS_PATH)
        st.session_state.column_fields = {
            field: list(aliases) for field, aliases in data.items()
        }
        st.session_state.columns_loaded = True


def _build_rules_dict() -> dict:
    """Reconstruct the full rules YAML dict from session state."""
    eircode_routing = {
        row["prefix"]: row["area"] for row in st.session_state.eircode_rows
    }

    lettershop_keywords = [
        {"area": e["area"], "patterns": e["patterns"]}
        for e in st.session_state.lettershop_keywords
    ]

    national_keywords = [
        {"area": e["area"], "patterns": e["patterns"]}
        for e in st.session_state.national_keywords
    ]

    return {
        "countries": {
            "ireland": {
                "country_patterns": st.session_state.country_patterns,
                "eircode_routing": eircode_routing,
                "areas": {
                    "dublin_districts": {
                        "routing": st.session_state.dublin_routing,
                        "districts": st.session_state.dublin_districts,
                    },
                    "lettershop_areas": {
                        "routing": "LETTERSHOP",
                        "keywords": lettershop_keywords,
                    },
                    "national_areas": {
                        "routing": "NATIONAL",
                        "keywords": national_keywords,
                    },
                    "ireland_other": {
                        "routing": st.session_state.ireland_other_routing,
                        "area": st.session_state.ireland_other_area,
                    },
                },
            }
        }
    }


# ---------------------------------------------------------------------------
# Tab 1: Classification Rules
# ---------------------------------------------------------------------------

def _render_rules_tab():
    _init_rules_state()

    # --- Country Patterns ---
    with st.expander("Country Patterns", expanded=False):
        st.caption("Patterns used to detect Ireland as the country (checked against country column and combined address).")
        patterns = st.session_state.country_patterns
        to_remove = None
        for i, pat in enumerate(patterns):
            cols = st.columns([5, 1])
            patterns[i] = cols[0].text_input(
                "Pattern", value=pat, key=f"cp_{i}", label_visibility="collapsed"
            )
            if cols[1].button("✕", key=f"cp_rm_{i}"):
                to_remove = i
        if to_remove is not None:
            patterns.pop(to_remove)
            st.rerun()
        if st.button("Add Pattern", key="cp_add"):
            patterns.append("")
            st.rerun()

    # --- Eircode Routing ---
    with st.expander("Eircode Routing", expanded=False):
        st.caption("Eircode prefix (first 3 characters) mapped to area name.")
        rows = st.session_state.eircode_rows
        to_remove = None
        for i, row in enumerate(rows):
            cols = st.columns([2, 4, 1])
            rows[i]["prefix"] = cols[0].text_input(
                "Prefix", value=row["prefix"], key=f"ec_p_{i}",
                max_chars=3, label_visibility="collapsed",
            )
            rows[i]["area"] = cols[1].text_input(
                "Area", value=row["area"], key=f"ec_a_{i}",
                label_visibility="collapsed",
            )
            if cols[2].button("✕", key=f"ec_rm_{i}"):
                to_remove = i
        if to_remove is not None:
            rows.pop(to_remove)
            st.rerun()
        if st.button("Add Eircode", key="ec_add"):
            rows.append({"prefix": "", "area": ""})
            st.rerun()

    # --- Lettershop Areas ---
    with st.expander("Lettershop Areas", expanded=False):
        st.caption("Areas within the Greater Dublin / Lettershop zone. Routing: **LETTERSHOP** (read-only).")
        keywords = st.session_state.lettershop_keywords
        area_to_remove = None
        for i, entry in enumerate(keywords):
            st.markdown(f"**Area {i + 1}**")
            entry["area"] = st.text_input(
                "Area Name", value=entry["area"], key=f"ls_area_{i}"
            )
            pats = entry["patterns"]
            pat_to_remove = None
            for j, pat in enumerate(pats):
                cols = st.columns([5, 1])
                pats[j] = cols[0].text_input(
                    "Pattern", value=pat, key=f"ls_pat_{i}_{j}",
                    label_visibility="collapsed",
                )
                if cols[1].button("✕", key=f"ls_pat_rm_{i}_{j}"):
                    pat_to_remove = j
            if pat_to_remove is not None:
                pats.pop(pat_to_remove)
                st.rerun()
            c1, c2 = st.columns(2)
            if c1.button("Add Pattern", key=f"ls_pat_add_{i}"):
                pats.append("")
                st.rerun()
            if c2.button("Remove Area", key=f"ls_area_rm_{i}"):
                area_to_remove = i
            st.divider()
        if area_to_remove is not None:
            keywords.pop(area_to_remove)
            st.rerun()
        if st.button("Add New Lettershop Area", key="ls_add"):
            keywords.append({"area": "", "patterns": [""]})
            st.rerun()

    # --- National Areas ---
    with st.expander("National Areas", expanded=False):
        st.caption(
            "Counties and cities outside Dublin. Routing: **NATIONAL** (read-only). "
            "Patterns are regex — special characters like `\\b` and `\\.?` are intentional."
        )
        keywords = st.session_state.national_keywords
        area_to_remove = None
        for i, entry in enumerate(keywords):
            st.markdown(f"**Area {i + 1}**")
            entry["area"] = st.text_input(
                "Area Name", value=entry["area"], key=f"na_area_{i}"
            )
            pats = entry["patterns"]
            pat_to_remove = None
            for j, pat in enumerate(pats):
                cols = st.columns([5, 1])
                pats[j] = cols[0].text_input(
                    "Pattern", value=pat, key=f"na_pat_{i}_{j}",
                    label_visibility="collapsed",
                )
                if cols[1].button("✕", key=f"na_pat_rm_{i}_{j}"):
                    pat_to_remove = j
            if pat_to_remove is not None:
                pats.pop(pat_to_remove)
                st.rerun()
            c1, c2 = st.columns(2)
            if c1.button("Add Pattern", key=f"na_pat_add_{i}"):
                pats.append("")
                st.rerun()
            if c2.button("Remove Area", key=f"na_area_rm_{i}"):
                area_to_remove = i
            st.divider()
        if area_to_remove is not None:
            keywords.pop(area_to_remove)
            st.rerun()
        if st.button("Add New National Area", key="na_add"):
            keywords.append({"area": "", "patterns": [""]})
            st.rerun()

    # --- Dublin Districts (read-only) ---
    with st.expander("Dublin Districts (read-only)", expanded=False):
        st.info(
            "Dublin districts are handled dynamically by `ireland.py` with "
            "special regex logic (negative lookahead guards). Editing them here "
            "would have no effect, so they are displayed as read-only."
        )
        st.write(f"**Routing:** {st.session_state.dublin_routing}")
        st.write(f"**Districts:** {', '.join(str(d) for d in st.session_state.dublin_districts)}")

    # --- Ireland Other Fallback (read-only) ---
    with st.expander("Ireland Other Fallback (read-only)", expanded=False):
        st.write(f"**Area:** {st.session_state.ireland_other_area}")
        st.write(f"**Routing:** {st.session_state.ireland_other_routing}")

    # --- Save ---
    if st.button("💾 Save Classification Rules", type="primary", key="save_rules"):
        data = _build_rules_dict()
        backup_path, errors = save_rules_config(RULES_PATH, data)
        if errors:
            for err in errors:
                st.error(err)
        else:
            st.success("Classification rules saved successfully.")
            st.caption(f"Backup saved to `{backup_path.name}`")


# ---------------------------------------------------------------------------
# Tab 2: Column Aliases
# ---------------------------------------------------------------------------

def _render_columns_tab():
    _init_columns_state()

    fields = st.session_state.column_fields

    for field, aliases in fields.items():
        with st.expander(field, expanded=False):
            to_remove = None
            for i, alias in enumerate(aliases):
                cols = st.columns([5, 1])
                aliases[i] = cols[0].text_input(
                    "Alias", value=alias, key=f"col_{field}_{i}",
                    label_visibility="collapsed",
                )
                if cols[1].button("✕", key=f"col_rm_{field}_{i}"):
                    to_remove = i
            if to_remove is not None:
                aliases.pop(to_remove)
                st.rerun()
            if st.button("Add Alias", key=f"col_add_{field}"):
                aliases.append("")
                st.rerun()

    if st.button("💾 Save Column Aliases", type="primary", key="save_columns"):
        data = dict(st.session_state.column_fields)
        backup_path, errors = save_columns_config(COLUMNS_PATH, data)
        if errors:
            for err in errors:
                st.error(err)
        else:
            st.success("Column aliases saved successfully.")
            st.caption(f"Backup saved to `{backup_path.name}`")


# ---------------------------------------------------------------------------
# Main layout
# ---------------------------------------------------------------------------

tab_rules, tab_columns = st.tabs(["Classification Rules", "Column Aliases"])

with tab_rules:
    _render_rules_tab()

with tab_columns:
    _render_columns_tab()
