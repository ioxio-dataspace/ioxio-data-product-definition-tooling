import json
from pathlib import Path

from converter import convert_data_product_definitions


def test_air_quality(tmpdir, json_snapshot):
    out_dir = tmpdir.mkdir("output")
    convert_data_product_definitions(Path(__file__).parent / "data", Path(out_dir))

    dest_file = out_dir / "AirQuality" / "Current.json"
    assert dest_file.exists()

    dest_spec = json.loads(dest_file.read_text("utf-8"))
    assert json_snapshot == dest_spec
