"""Validate source and build flat Lambda ZIP packages. Makes no AWS calls."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parent.parent
output = root / "dist"
output.mkdir(exist_ok=True)
for name in ("index-photos", "search-photos"):
    source = root / name / "lambda_function.py"
    compile(source.read_text(), str(source), "exec")
    destination = output / (name + ".zip")
    with ZipFile(destination, "w", compression=ZIP_DEFLATED) as archive:
        archive.write(source, "lambda_function.py")
    with ZipFile(destination) as archive:
        assert archive.namelist() == ["lambda_function.py"]
        assert archive.read("lambda_function.py") == source.read_bytes()
    print("Built and verified", destination.name)
