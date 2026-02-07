"""Streamlit page — Lettershop Ireland address sorter."""

import io
import tempfile
import zipfile
from pathlib import Path

import pandas as pd
import streamlit as st

from src.build_address import add_combined_address
from src.classifier import Classifier
from src.detect_columns import detect_columns
from src.exceptions import ColumnDetectionError, ConfigError, FileFormatError
from src.ingest import load_file
from src.output import write_output

st.set_page_config(page_title="Lettershop - Ireland", page_icon="🇮🇪", layout="wide")

st.title("🇮🇪 Lettershop - Ireland")
st.markdown("Upload an Irish address file (.xlsx or .csv) to classify addresses into Lettershop and National routing buckets.")

# File upload
uploaded_file = st.file_uploader(
    "Choose an input file",
    type=["xlsx", "csv"],
    help="Upload an Excel (.xlsx) or CSV file with address data.",
)

if uploaded_file is not None:
    # Save uploaded file to temp location
    suffix = Path(uploaded_file.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name

    try:
        # 1. Load
        df = load_file(tmp_path)
        st.success(f"Loaded **{len(df)}** rows, **{len(df.columns)}** columns from `{uploaded_file.name}`")

        # 2. Detect columns
        col_map = detect_columns(list(df.columns))

        # Display detected mappings
        st.subheader("Detected Column Mappings")
        mapping_display = {
            k: v for k, v in col_map.__dict__.items() if v is not None
        }
        col1, col2 = st.columns(2)
        for i, (field, col_name) in enumerate(mapping_display.items()):
            target = col1 if i % 2 == 0 else col2
            target.markdown(f"**{field}** → `{col_name}`")

        unmapped = [c for c in df.columns if c not in col_map.mapped_columns()]
        if unmapped:
            with st.expander("Unmapped columns"):
                st.write(unmapped)

        # Preview
        with st.expander("Preview input data"):
            st.dataframe(df.head(10), use_container_width=True)

        # Process button
        if st.button("🔄 Process", type="primary"):
            with st.status("Processing...", expanded=True) as status:
                # 3. Build combined address
                st.write("Building combined addresses...")
                df = add_combined_address(df, col_map)

                # 4. Classify
                st.write("Classifying addresses...")
                total_rows = len(df)
                progress_bar = st.progress(0, text=f"Classifying row 0 / {total_rows}...")

                def on_progress(current: int, total: int) -> None:
                    progress_bar.progress(
                        current / total,
                        text=f"Classifying row {current} / {total}...",
                    )

                classifier = Classifier()
                df_classified, df_exceptions = classifier.classify(
                    df, col_map, progress_callback=on_progress
                )
                progress_bar.progress(1.0, text="Classification complete.")

                # 5. Write output to bytes buffer
                st.write("Writing output...")
                input_ext = Path(uploaded_file.name).suffix.lower()
                output_format = "csv" if input_ext == ".csv" else "xlsx"

                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{output_format}") as out_tmp:
                    out_path = out_tmp.name

                stats = write_output(out_path, df_classified, df_exceptions, format=output_format)

                # Read output for download
                if output_format == "csv":
                    # Zip the 3 CSV files for a single download
                    stem = Path(out_path).parent / Path(out_path).stem
                    csv_files = {
                        f"{Path(uploaded_file.name).stem}_data.csv": Path(f"{stem}_data.csv"),
                        f"{Path(uploaded_file.name).stem}_exceptions.csv": Path(f"{stem}_exceptions.csv"),
                        f"{Path(uploaded_file.name).stem}_summary.csv": Path(f"{stem}_summary.csv"),
                    }
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                        for arcname, filepath in csv_files.items():
                            zf.write(filepath, arcname)
                    output_bytes = zip_buffer.getvalue()
                    output_filename = Path(uploaded_file.name).stem + "_sorted.zip"
                    output_mime = "application/zip"
                else:
                    with open(out_path, "rb") as f:
                        output_bytes = f.read()
                    output_filename = Path(uploaded_file.name).stem + "_sorted.xlsx"
                    output_mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                status.update(label="Processing complete!", state="complete")

            # Summary
            st.subheader("Results")

            metric1, metric2, metric3 = st.columns(3)
            metric1.metric("Classified", stats.classified_rows)
            metric2.metric("Exceptions", stats.exception_rows)
            metric3.metric("Total", stats.total_rows)

            # Routing summary
            if stats.routing_counts:
                routing_cols = st.columns(len(stats.routing_counts))
                for col, (routing, count) in zip(routing_cols, sorted(stats.routing_counts.items())):
                    pct = (count / stats.classified_rows * 100) if stats.classified_rows > 0 else 0.0
                    col.metric(routing, f"{count} ({pct:.1f}%)")

            # Area breakdown
            if stats.area_counts:
                st.subheader("Area Breakdown")
                area_df = pd.DataFrame(
                    sorted(stats.area_counts.items()),
                    columns=["Area", "Count"],
                )
                st.dataframe(area_df, use_container_width=True, hide_index=True)

            # Preview classified
            with st.expander(f"Classified Data ({stats.classified_rows} rows)"):
                # Drop internal columns for display
                display_cols = [c for c in df_classified.columns if c != "combined_address"]
                st.dataframe(df_classified[display_cols].head(50), use_container_width=True)

            # Preview exceptions
            if stats.exception_rows > 0:
                with st.expander(f"Exceptions ({stats.exception_rows} rows)"):
                    display_cols = [c for c in df_exceptions.columns if c != "combined_address"]
                    st.dataframe(df_exceptions[display_cols], use_container_width=True)

            # Download button
            st.download_button(
                label="📥 Download Output",
                data=output_bytes,
                file_name=output_filename,
                mime=output_mime,
                type="primary",
            )

    except (FileFormatError, ColumnDetectionError, ConfigError) as e:
        st.error(f"Error: {e}")
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        st.exception(e)
