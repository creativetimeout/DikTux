from diktux.services.paste import PasteService, detect_session_type


def test_detect_session_type_wayland():
    assert detect_session_type({"XDG_SESSION_TYPE": "wayland"}) == "wayland"


def test_detect_session_type_x11_default():
    assert detect_session_type({}) == "x11"
    assert detect_session_type({"XDG_SESSION_TYPE": "x11"}) == "x11"


def test_copy_to_clipboard_x11():
    calls = []

    def runner(cmd, input=None):
        calls.append((cmd, input))
        return 0

    svc = PasteService(session_type="x11", runner=runner)
    svc.copy_to_clipboard("hallo")
    assert calls[0][0] == ["xclip", "-selection", "clipboard"]
    assert calls[0][1] == b"hallo"


def test_copy_to_clipboard_wayland():
    calls = []

    def runner(cmd, input=None):
        calls.append((cmd, input))
        return 0

    svc = PasteService(session_type="wayland", runner=runner)
    svc.copy_to_clipboard("hallo")
    assert calls[0][0] == ["wl-copy"]
    assert calls[0][1] == b"hallo"


def test_paste_x11_runs_xdotool():
    calls = []

    def runner(cmd, input=None):
        calls.append(cmd)
        return 0

    svc = PasteService(session_type="x11", runner=runner)
    svc.paste("text")
    assert ["xclip", "-selection", "clipboard"] in calls
    assert ["xdotool", "key", "ctrl+v"] in calls


def test_paste_wayland_runs_wtype():
    calls = []

    def runner(cmd, input=None):
        calls.append(cmd)
        return 0

    svc = PasteService(session_type="wayland", runner=runner)
    svc.paste("text")
    assert ["wtype", "-M", "ctrl", "v", "-m", "ctrl"] in calls


def test_paste_falls_back_to_ydotool_on_failure():
    calls = []

    def runner(cmd, input=None):
        calls.append(cmd)
        if cmd == ["xdotool", "key", "ctrl+v"]:
            return 1
        return 0

    svc = PasteService(session_type="x11", runner=runner)
    svc.paste("text")
    assert ["ydotool", "key", "29:1", "47:1", "47:0", "29:0"] in calls
