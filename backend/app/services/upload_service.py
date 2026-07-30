import os
import shutil
import pandas as pd


UPLOAD_FOLDER = "uploads"


def save_file(file):
    """
    Save the uploaded file to the uploads folder.
    """

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return file_path


def analyze_dataset(file_path):
    """
    Read the uploaded dataset and return basic information.
    """

    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path)

    elif file_path.endswith(".xlsx"):
        df = pd.read_excel(file_path)

    else:
        raise ValueError("Unsupported file format")

    return {
        "filename": os.path.basename(file_path),
        "rows": len(df),
        "columns": len(df.columns),
        "status": "success"
    }