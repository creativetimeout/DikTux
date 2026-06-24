import diktux


def test_package_has_version():
    assert isinstance(diktux.__version__, str)
    assert diktux.__version__ != ""
