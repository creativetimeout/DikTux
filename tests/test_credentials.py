from diktux.services.credentials import (
    API_KEY_NAME,
    CredentialsStore,
    InMemoryBackend,
)


def test_set_and_get_api_key():
    store = CredentialsStore(backend=InMemoryBackend())
    assert store.get_api_key() is None
    assert store.is_configured() is False

    store.set_api_key("sk-test-1234567890")
    assert store.get_api_key() == "sk-test-1234567890"
    assert store.is_configured() is True


def test_delete_api_key():
    store = CredentialsStore(backend=InMemoryBackend())
    store.set_api_key("sk-abc")
    store.delete_api_key()
    assert store.get_api_key() is None


def test_masked_api_key_long():
    store = CredentialsStore(backend=InMemoryBackend())
    store.set_api_key("sk-abcdefghij")
    masked = store.masked_api_key()
    assert masked.startswith("sk-a")
    assert "•" in masked


def test_masked_api_key_empty():
    store = CredentialsStore(backend=InMemoryBackend())
    assert store.masked_api_key() == ""


def test_api_key_name_constant():
    assert API_KEY_NAME == "openai_api_key"
