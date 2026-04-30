"""Tests for envault.rotate — key rotation."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.crypto import encrypt, decrypt
from envault.keystore import KeyStore
from envault.rotate import rotate_key, RotationError


OLD_PASS = "old-secret"
NEW_PASS = "new-secret"
PLAINTEXT = b"API_KEY=abc123\nDEBUG=true\n"


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def env_file(env_dir: Path) -> Path:
    f = env_dir / ".env"
    f.write_bytes(PLAINTEXT)
    return f


@pytest.fixture()
def enc_file(env_file: Path) -> Path:
    enc = env_file.with_suffix(".env.enc")
    enc.write_bytes(encrypt(PLAINTEXT, OLD_PASS))
    return enc


@pytest.fixture()
def ks(env_dir: Path) -> KeyStore:
    store = KeyStore(env_dir / "keystore.json")
    store.set(".env", OLD_PASS)
    return store


class TestRotateKey:
    def test_returns_enc_path(self, env_file, enc_file, ks, env_dir):
        result = rotate_key(env_file, ks, OLD_PASS, NEW_PASS, vault_dir=env_dir)
        assert result == enc_file

    def test_enc_file_differs_after_rotation(self, env_file, enc_file, ks, env_dir):
        original_bytes = enc_file.read_bytes()
        rotate_key(env_file, ks, OLD_PASS, NEW_PASS, vault_dir=env_dir)
        assert enc_file.read_bytes() != original_bytes

    def test_new_ciphertext_decryptable_with_new_password(self, env_file, enc_file, ks, env_dir):
        rotate_key(env_file, ks, OLD_PASS, NEW_PASS, vault_dir=env_dir)
        recovered = decrypt(enc_file.read_bytes(), NEW_PASS)
        assert recovered == PLAINTEXT

    def test_old_password_no_longer_works(self, env_file, enc_file, ks, env_dir):
        rotate_key(env_file, ks, OLD_PASS, NEW_PASS, vault_dir=env_dir)
        with pytest.raises(Exception):
            decrypt(enc_file.read_bytes(), OLD_PASS)

    def test_keystore_updated_with_new_password(self, env_file, enc_file, ks, env_dir):
        rotate_key(env_file, ks, OLD_PASS, NEW_PASS, vault_dir=env_dir)
        assert ks.get(".env") == NEW_PASS

    def test_wrong_old_password_raises_rotation_error(self, env_file, enc_file, ks, env_dir):
        with pytest.raises(RotationError, match="wrong password"):
            rotate_key(env_file, ks, "totally-wrong", NEW_PASS, vault_dir=env_dir)

    def test_missing_enc_file_raises_rotation_error(self, env_file, ks, env_dir):
        # enc_file fixture NOT used — file doesn't exist
        with pytest.raises(RotationError, match="Encrypted file not found"):
            rotate_key(env_file, ks, OLD_PASS, NEW_PASS, vault_dir=env_dir)

    def test_audit_event_recorded(self, env_file, enc_file, ks, env_dir):
        from envault.audit import get_events
        rotate_key(env_file, ks, OLD_PASS, NEW_PASS, vault_dir=env_dir)
        events = get_events(vault_dir=env_dir)
        assert any(e["action"] == "rotate" for e in events)
