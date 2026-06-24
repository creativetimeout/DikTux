import diktux.ui.settings_window as sw


def test_open_settings_window_callable_exists():
    assert callable(sw.open_settings_window)


def test_gtk_available_flag_is_bool():
    assert isinstance(sw.GTK_AVAILABLE, bool)
