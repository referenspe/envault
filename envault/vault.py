"""High-level Vault API: encrypt/decrypt .env files using the KeyStore."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional

from envault.crypto import encrypt, decrypt
from envault.env_parser import parse_env, serialize_env, merge_env
from envault.keystore import KeyStore


DEFAULT_VAULT_EXT = '.enc'


class Vault:
    """Encrypts and decrypts .env files, storing ciphertext alongside the
    original file (e.g. ``.env`` → ``.env.enc``).
    """

    def __init__(self, keystore: KeyStore, vault_ext: str = DEFAULT_VAULT_EXT):
        self._ks = keystore
        self._ext = vault_ext

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def lock(self, env_path: str | Path, profile: str = 'default') -> Path:
        """Encrypt *env_path* and write ciphertext to ``<env_path><ext>``.

        Returns the path of the encrypted file.
        """
        env_path = Path(env_path)
        password = self._ks.get(profile)
        if password is None:
            raise KeyError(f"No key found for profile '{profile}'")

        plaintext = env_path.read_bytes()
        ciphertext = encrypt(plaintext, password)

        enc_path = env_path.with_suffix(env_path.suffix + self._ext)
        enc_path.write_bytes(ciphertext)
        return enc_path

    def unlock(
        self,
        enc_path: str | Path,
        dest_path: Optional[str | Path] = None,
        profile: str = 'default',
    ) -> Path:
        """Decrypt *enc_path* and write plaintext to *dest_path*.

        If *dest_path* is omitted the ``<ext>`` suffix is stripped.
        Returns the path of the decrypted file.
        """
        enc_path = Path(enc_path)
        if dest_path is None:
            name = enc_path.name
            if name.endswith(self._ext):
                name = name[: -len(self._ext)]
            dest_path = enc_path.with_name(name)
        dest_path = Path(dest_path)

        password = self._ks.get(profile)
        if password is None:
            raise KeyError(f"No key found for profile '{profile}'")

        ciphertext = enc_path.read_bytes()
        plaintext = decrypt(ciphertext, password)
        dest_path.write_bytes(plaintext)
        return dest_path

    def sync(
        self,
        enc_path: str | Path,
        env_path: str | Path,
        profile: str = 'default',
    ) -> Dict[str, str]:
        """Decrypt *enc_path*, merge new values into *env_path*, and
        re-encrypt the merged result.

        Returns the dict of changed keys.
        """
        enc_path = Path(enc_path)
        env_path = Path(env_path)

        password = self._ks.get(profile)
        if password is None:
            raise KeyError(f"No key found for profile '{profile}'")

        remote_text = decrypt(enc_path.read_bytes(), password).decode()
        remote_env = parse_env(remote_text)

        local_env: Dict[str, str] = {}
        if env_path.exists():
            local_env = parse_env(env_path.read_text())

        merged, changed = merge_env(local_env, remote_env)
        env_path.write_text(serialize_env(merged))

        # Re-lock with the merged content
        enc_path.write_bytes(encrypt(serialize_env(merged).encode(), password))
        return changed
