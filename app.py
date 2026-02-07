"""CLI entry point for the Data-Sorter pipeline."""

import argparse
import logging
import sys
from pathlib import Path

from src.build_address import add_combined_address
from src.classifier import Classifier
from src.detect_columns import detect_columns
from src.exceptions import ColumnDetectionError, ConfigError, FileFormatError
from src.ingest import load_file
from src.output import write_output


def main():
    parser = argparse.ArgumentParser(
        description="Data-Sorter: Classify addresses into routing buckets.",
    )
    parser.add_argument("input", help="Input file path (.xlsx or .csv)")
    parser.add_argument("output", help="Output file path (.xlsx or .csv)")
    parser.add_argument(
        "--config",
        default=None,
        help="Path to rules YAML config (default: config/rules.yaml)",
    )
    parser.add_argument(
        "--columns-config",
        default=None,
        help="Path to column aliases YAML config (default: config/columns.yaml)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    logger = logging.getLogger(__name__)

    config_path = Path(args.config) if args.config else None
    columns_config_path = Path(args.columns_config) if args.columns_config else None

    try:
        # 1. Load input file
        logger.info("Loading %s ...", args.input)
        df = load_file(args.input)
        logger.info("Loaded %d rows, %d columns", len(df), len(df.columns))

        # 2. Detect columns
        logger.info("Detecting columns ...")
        col_map = detect_columns(list(df.columns), columns_config_path)
        logger.info("Detected columns: %s", {
            k: v for k, v in col_map.__dict__.items() if v is not None
        })

        # 3. Build combined address
        logger.info("Building combined addresses ...")
        df = add_combined_address(df, col_map)

        # 4. Classify
        logger.info("Classifying addresses ...")
        classifier = Classifier(config_path)
        df_classified, df_exceptions = classifier.classify(df, col_map)
        logger.info(
            "Classified: %d rows, Exceptions: %d rows",
            len(df_classified),
            len(df_exceptions),
        )

        # 5. Write output — match format to input
        input_ext = Path(args.input).suffix.lower()
        output_format = "csv" if input_ext == ".csv" else "xlsx"

        logger.info("Writing output to %s ...", args.output)
        stats = write_output(args.output, df_classified, df_exceptions, format=output_format)

        # 6. Print summary
        if output_format == "csv":
            stem = Path(args.output).parent / Path(args.output).stem
            print(f"\nDone! Output written to:")
            print(f"  {stem}_data.csv")
            print(f"  {stem}_exceptions.csv")
            print(f"  {stem}_summary.csv")
        else:
            print(f"\nDone! Output written to: {args.output}")
        print(f"  Classified: {stats.classified_rows}")
        print(f"  Exceptions: {stats.exception_rows}")
        print(f"  Total:      {stats.total_rows}")
        if stats.area_counts:
            print("\n  Area breakdown:")
            for area, count in sorted(stats.area_counts.items()):
                print(f"    {area}: {count}")

    except (FileFormatError, ColumnDetectionError, ConfigError) as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        sys.exit(2)


if __name__ == "__main__":
    main()
