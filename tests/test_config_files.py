from pathlib import Path
import json


ROOT_DIR = Path(__file__).resolve().parents[1]


def test_comex_ncm_config_is_valid_json():
    path = ROOT_DIR / "config/comex_pescados_ncm.json"
    assert path.exists(), "config/comex_pescados_ncm.json não encontrado"

    data = json.loads(path.read_text(encoding="utf-8"))

    assert "groups" in data
    assert "salmao" in data["groups"]
    assert "bacalhau" in data["groups"]
    assert "camarao" in data["groups"]

    for group_name, group in data["groups"].items():
        assert "ncms" in group, f"Grupo sem NCMs: {group_name}"
        assert isinstance(group["ncms"], list)
        assert len(group["ncms"]) > 0
