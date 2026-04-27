"""Integration tests for envault.vault.Vault."""

import pytest
from pathlib import Path

from envault.keystore import KeyStore
from envault.vault import Vault


@pytest.fixture()
def ks(tmp_path):
    store_file = tmp_path / 'keys.json'
    ks = KeyStore(str(store_file))
    ks.set('default', 'supersecret')
    return ks


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / '.env'
    p.write_text('DB_HOST=localhost\nDB_PORT=5432\nSECRET=abc123\n')
    return p


class TestVaultLockUnlock:
    def test_lock_creates_enc_file(self, ks, env_file):
        vault = Vault(ks)
        enc = vault.lock(env_file)
        assert enc.exists()
        assert enc.suffix == '.enc'

    def test_encrypted_file_differs_from_original(self, ks, env_file):
        vault = Vault(ks)
        enc = vault.lock(env_file)
        assert enc.read_bytes() != env_file.read_bytes()

    def test_unlock_restores_original(self, ks, env_file, tmp_path):
        vault = Vault(ks)
        enc = vault.lock(env_file)
        dest = tmp_path / '.env.restored'
        vault.unlock(enc, dest_path=dest)
        assert dest.read_bytes() == env_file.read_bytes()

    def test_unlock_auto_dest_path(self, ks, env_file, tmp_path):
        vault = Vault(ks)
        enc = vault.lock(env_file)
        # Remove original to prove unlock recreates it
        original_content = env_file.read_bytes()
        env_file.unlink()
        vault.unlock(enc)
        assert env_file.read_bytes() == original_content

    def test_wrong_profile_raises(self, ks, env_file):
        vault = Vault(ks)
        with pytest.raises(KeyError):
            vault.lock(env_file, profile='nonexistent')


class TestVaultSync:
    def test_sync_adds_new_keys(self, ks, env_file, tmp_path):
        vault = Vault(ks)
        enc = vault.lock(env_file)

        local = tmp_path / '.env.local'
        local.write_text('DB_HOST=remotehost\n')

        changed = vault.sync(enc, local)
        from envault.env_parser import parse_env
        merged = parse_env(local.read_text())
        assert merged['DB_PORT'] == '5432'
        assert 'DB_PORT' in changed

    def test_sync_unchanged_keys_not_reported(self, ks, env_file, tmp_path):
        vault = Vault(ks)
        enc = vault.lock(env_file)

        local = tmp_path / '.env.local'
        local.write_text('DB_HOST=localhost\nDB_PORT=5432\nSECRET=abc123\n')

        changed = vault.sync(enc, local)
        assert changed == {}

    def test_sync_creates_local_if_missing(self, ks, env_file, tmp_path):
        vault = Vault(ks)
        enc = vault.lock(env_file)

        new_local = tmp_path / 'brand_new.env'
        vault.sync(enc, new_local)
        assert new_local.exists()
        from envault.env_parser import parse_env
        assert parse_env(new_local.read_text())['SECRET'] == 'abc123'
