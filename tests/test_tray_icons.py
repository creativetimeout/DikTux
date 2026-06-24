from PIL import Image

from diktux.state import TrayStatus
from diktux.ui.tray_icons import frame_count, make_icon


def test_make_icon_returns_rgba_image():
    img = make_icon(TrayStatus.IDLE)
    assert isinstance(img, Image.Image)
    assert img.mode == "RGBA"
    assert img.size == (64, 64)


def test_make_icon_custom_size():
    img = make_icon(TrayStatus.RECORDING, frame=1, size=32)
    assert img.size == (32, 32)


def test_make_icon_has_visible_pixels():
    img = make_icon(TrayStatus.SUCCESS)
    alpha = img.getchannel("A")
    assert alpha.getextrema()[1] > 0


def test_frame_count():
    assert frame_count(TrayStatus.RECORDING) == 4
    assert frame_count(TrayStatus.PROCESSING) == 4
    assert frame_count(TrayStatus.IDLE) == 1
    assert frame_count(TrayStatus.SUCCESS) == 1
    assert frame_count(TrayStatus.ERROR) == 1
