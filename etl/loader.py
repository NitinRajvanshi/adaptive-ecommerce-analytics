from pathlib import Path
from typing import BinaryIO

import pandas as pd

MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


class DataLoadError(Exception):
    """Raised when a dataset cannot be loaded safely."""


def validate_file_size(file_size: int) -> None:
    """
    Validate that the uploaded file does not exceed the maximum size.

    Args:
        file_size: File size in bytes.

    Raises:
        DataLoadError: If the file is too large.
    """

    if file_size <= 0:
        raise DataLoadError("The uploaded file is empty.")

    if file_size > MAX_FILE_SIZE_BYTES:
        raise DataLoadError(
            f"File is too large. Maximum allowed size is "
            f"{MAX_FILE_SIZE_MB} MB."
        )


def validate_file_extension(filename: str) -> None:
    """
    Validate that the uploaded file has a CSV extension.

    Args:
        filename: Name of the uploaded file.

    Raises:
        DataLoadError: If the file is not a CSV.
    """

    if not filename:
        raise DataLoadError("The uploaded file has no filename.")

    if Path(filename).suffix.lower() != ".csv":
        raise DataLoadError(
            "Unsupported file type. Please upload a CSV file."
        )


def load_csv(
    file_source: str | Path | BinaryIO,
) -> pd.DataFrame:
    """
    Load a CSV file into a Pandas DataFrame.

    Args:
        file_source: CSV path or file-like object.

    Returns:
        Loaded Pandas DataFrame.

    Raises:
        DataLoadError: If the CSV cannot be loaded.
    """

    try:
        if isinstance(file_source, (str, Path)):
            path = Path(file_source)

            if not path.exists():
                raise DataLoadError(
                    f"File not found: {path}"
                )

            if not path.is_file():
                raise DataLoadError(
                    f"Path is not a file: {path}"
                )

            validate_file_extension(path.name)
            validate_file_size(path.stat().st_size)

            df = pd.read_csv(path)

        else:
            filename = getattr(
                file_source,
                "name",
                "uploaded_file.csv",
            )

            validate_file_extension(filename)

            file_source.seek(0)

            data = file_source.read()

            validate_file_size(len(data))

            file_source.seek(0)

            df = pd.read_csv(file_source)

    except DataLoadError:
        raise

    except pd.errors.EmptyDataError as exc:
        raise DataLoadError(
            "The CSV file does not contain any data."
        ) from exc

    except pd.errors.ParserError as exc:
        raise DataLoadError(
            "The CSV file could not be parsed. "
            "Check that the file is a valid CSV."
        ) from exc

    except UnicodeDecodeError as exc:
        raise DataLoadError(
            "The CSV encoding could not be read. "
            "Please save the file as UTF-8 CSV."
        ) from exc

    except Exception as exc:
        raise DataLoadError(
            f"Unable to load the CSV file: {exc}"
        ) from exc

    if df.empty:
        raise DataLoadError(
            "The CSV file contains headers but no data rows."
        )

    if len(df.columns) == 0:
        raise DataLoadError(
            "The CSV file does not contain any columns."
        )

    return df


def load_sample_dataset(
    sample_path: str | Path = "data/sample_sales.csv",
) -> pd.DataFrame:
    """
    Load the project's sample e-commerce dataset.

    Args:
        sample_path: Path to the sample CSV.

    Returns:
        Sample dataset as a Pandas DataFrame.

    Raises:
        DataLoadError: If the sample dataset cannot be loaded.
    """

    return load_csv(sample_path)


def get_dataset_summary(df: pd.DataFrame) -> dict[str, int]:
    """
    Return basic information about a loaded dataset.

    Args:
        df: Dataset to summarize.

    Returns:
        Dictionary containing row and column counts.
    """

    return {
        "rows": len(df),
        "columns": len(df.columns),
    }