"""Credential storage backed by the system keyring via secretstorage."""

from __future__ import annotations

from typing import Protocol

API_KEY_NAME = "openai_api_key"
_SERVICE = "diktux"
_BULLET = "•"
_UNICODE_DASHES = str.maketrans({
    "‐": "-",  # hyphen
    "‑": "-",  # non-breaking hyphen
    "‒": "-",  # figure dash
    "–": "-",  # en dash
    "—": "-",  # em dash
    "―": "-",  # horizontal bar
    "﹘": "-",  # small em dash
    "－": "-",  # fullwidth hyphen-minus
})


class CredentialsBackend(Protocol):
    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str) -> None: ...
    def delete(self, key: str) -> None: ...


class InMemoryBackend:
    """Backend used in tests; keeps secrets in a dict."""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self._store.get(key)

    def set(self, key: str, value: str) -> None:
        self._store[key] = value

    def delete(self, key: str) -> None:
        self._store.pop(key, None)


class SecretStorageBackend:
    """Backend using the freedesktop Secret Service (GNOME Keyring / KDE Wallet)."""

    def __init__(self) -> None:
        import secretstorage

        self._secretstorage = secretstorage
        self._connection = secretstorage.dbus_init()
        self._collection = secretstorage.get_default_collection(self._connection)

    def _attributes(self, key: str) -> dict[str, str]:
        return {"service": _SERVICE, "key": key}

    def get(self, key: str) -> str | None:
        if self._collection.is_locked():
            self._collection.unlock()
        items = list(self._collection.search_items(self._attributes(key)))
        if not items:
            return None
        secret = items[0].get_secret()
        return secret.decode("utf-8") if secret else None

    def set(self, key: str, value: str) -> None:
        if self._collection.is_locked():
            self._collection.unlock()
        for item in self._collection.search_items(self._attributes(key)):
            item.delete()
        self._collection.create_item(
            f"DikTux {key}",
            self._attributes(key),
            value.encode("utf-8"),
            replace=True,
        )

    def delete(self, key: str) -> None:
        if self._collection.is_locked():
            self._collection.unlock()
        for item in self._collection.search_items(self._attributes(key)):
            item.delete()


class CredentialsStore:
    def __init__(self, backend: CredentialsBackend | None = None) -> None:
        self._backend = backend or SecretStorageBackend()

    @staticmethod
    def _sanitize_key(value: str) -> str:
        return value.translate(_UNICODE_DASHES).strip()

    def get_api_key(self) -> str | None:
        value = self._backend.get(API_KEY_NAME)
        if value is None or value == "":
            return None
        return self._sanitize_key(value)

    def set_api_key(self, value: str) -> None:
        self._backend.set(API_KEY_NAME, self._sanitize_key(value))

    def delete_api_key(self) -> None:
        self._backend.delete(API_KEY_NAME)

    def is_configured(self) -> bool:
        return self.get_api_key() is not None

    def masked_api_key(self) -> str:
        value = self.get_api_key()
        if not value:
            return ""
        if len(value) > 8:
            return value[:4] + " " + _BULLET * 8
        return _BULLET * 8
