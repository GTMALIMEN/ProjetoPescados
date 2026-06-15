from src.services.mapas_service import _linear_colormap


def test_linear_colormap_viridis_compatible():
    cmap = _linear_colormap("viridis", 0, 10)
    assert cmap is not None
    assert hasattr(cmap, "__call__")


def test_linear_colormap_ylgnbu_compatible():
    cmap = _linear_colormap("ylgnbu", 0, 10)
    assert cmap is not None
    assert hasattr(cmap, "__call__")
