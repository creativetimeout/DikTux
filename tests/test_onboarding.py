from diktux.config import Config
from diktux.services.credentials import CredentialsStore, InMemoryBackend
from diktux.ui.onboarding import (
    OnboardingViewModel,
    input_group_ok,
    missing_cli_tools,
    required_cli_tools,
)


def test_input_group_ok():
    assert input_group_ok(["users", "input"]) is True
    assert input_group_ok(["users"]) is False


def test_required_cli_tools_per_session():
    assert required_cli_tools("wayland") == ["wl-copy", "wtype"]
    assert required_cli_tools("x11") == ["xclip", "xdotool"]


def test_missing_cli_tools_uses_which():
    present = {"xclip"}
    missing = missing_cli_tools("x11", which=lambda name: name if name in present else None)
    assert missing == ["xdotool"]


def test_should_show_when_unconfigured():
    vm = OnboardingViewModel(
        config=Config(), credentials=CredentialsStore(backend=InMemoryBackend())
    )
    assert vm.should_show() is True


def test_should_not_show_after_complete():
    vm = OnboardingViewModel(
        config=Config(),
        credentials=CredentialsStore(backend=InMemoryBackend()),
        save=lambda cfg: None,
    )
    vm.save_api_key("sk-test")
    vm.complete()
    assert vm.should_show() is False


def test_configured_when_api_key_set():
    creds = CredentialsStore(backend=InMemoryBackend())
    creds.set_api_key("sk-test")
    vm = OnboardingViewModel(config=Config(), credentials=creds, save=lambda cfg: None)
    assert vm.is_configured() is True
    assert vm.should_show() is False
