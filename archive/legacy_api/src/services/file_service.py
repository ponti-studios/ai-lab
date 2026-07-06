import os

from conf import ROOT_DIR


def get_file_contents(filepath: str):
    abs_filepath = os.path.join(ROOT_DIR, filepath)
    try:
        with open(abs_filepath, "r") as file:
            content = file.read()
            return content
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: {filepath} does not exist in the {dir} folder.")
    except Exception as e:
        return f"An error occurred: {str(e)}"
