"""Tests for crypto and keystore modules."""

import json
import pytest
from pathlib import Path
from cryptography.fernet import InvalidToken

from envault.crypto import encrypt, decrypt
from envault.keystore import KeyStore


# ---------------------------------------------------------------------------
# Crypto tests
# ---------------------------------------------------------------------------

class TestCrypto:
    PASSWORD = "super-secret-passphrase"
    PLAINTEXT = "DB_URL=postgres://localhost/mydb\nAPI_KEY=abc123"

    def test_encrypt_returns_bytes(self):
        result = encrypt(self.PLAINTEXT, self.PASSWORD)
        assert isinstance(result, bytes)

    def test_round_trip(self):
        ciphertext = encrypt(self.PLAINTEXT, self.PASSWORD)
        assert decrypt(ciphertext, self.PASSWORD) == self.PLAINTEXT

    def test_different_salts_each_call(self):
        c1 = encrypt(self.PLAINTEXT, self.PASSWORD)
        c2 = encrypt(self.PLAINTEXT, self.PASSWORD)
        assert c1 != c2  # random salt ensures unique ciphertexts

    def test_wrong_password_raises(self):
        ciphertext = encrypt(self.PLAINTEXT, self.PASSWORD)
        with pytest.raises(InvalidToken):
            decrypt(ciphertext, "wrong-password")


# ---------------------------------------------------------------------------
# KeyStore tests
# ---------------------------------------------------------------------------

class TestKeyStore:
    def test_set_and_get(self, tmp_path):
        ks = KeyStore(path=tmp_path / "keystore.json")
        ks.set("my-project", "p@ssw0rd")
        assert ks.get("my-project") == "p@ssw0rd"

    def test_get_missing_returns_none(self, tmp_path):
        ks = KeyStore(path=tmp_path / "keystore.json")
        assert ks.get("nonexistent") is None

    def test_persistence(self, tmp_path):
        path = tmp_path / "keystore.json"
        ks = KeyStore(path=path)
        ks.set("proj", "secret")
        ks2 = KeyStore(path=path)
        assert ks2.get("proj") == "secret"

    def test_delete_existing(self, tmp_path):
        ks = KeyStore(path=tmp_path / "keystore.json")
        ks.set("proj", "secret")
        assert ks.delete("proj") is True
        assert ks.get("proj") is None

    def test_delete_nonexistent(self, tmp_path):
        ks = KeyStore(path=tmp_path / "keystore.json")
        assert ks.delete("ghost") is False

    def test_list_projects(self, tmp_path):
        ks = KeyStore(path=tmp_path / "keystore.json")
        ks.set("alpha", "a")
        ks.set("beta", "b")
        assert sorted(ks.list_projects()) == ["alpha", "beta"]
