"""Vault — high-level lock / unlock / sync operations with audit logging."""

from pathlib import Path

from envault.crypto import encrypt, decrypt
from envault.env_parser import parse_env, serialize_env, merge_env
from envault.keystore import KeyStore
from envault import audit

ENC_SUFFIX = ".enc"


class Vault:
    """Manages encryption and synchronisation of a single .env file."""

    def __init__(self, env_path: Path, keystore: KeyStore) -> None:
        self.env_path = Path(env_path)
        self.enc_path = self.env_path.with_suffix(ENC_SUFFIX)
        self.keystore = keystore
        self._vault_dir = self.env_path.parent

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def lock(self, password: str) -> Path:
        """Encrypt *env_path* → *enc_path*, record audit event, return enc path."""
        plaintext = self.env_path.read_bytes()
        ciphertext = encrypt(plaintext, password)
        self.enc_path.write_bytes(ciphertext)
        self.keystore.set(str(self.env_path), password)
        audit.record_event(
            self._vault_dir,
            action="lock",
            env_file=self.env_path.name,
        )
        return self.enc_path

    def unlock(self, password: str) -> Path:
        """Decrypt *enc_path* → *env_path*, record audit event, return env path."""
        ciphertext = self.enc_path.read_bytes()
        plaintext = decrypt(ciphertext, password)
        self.env_path.write_bytes(plaintext)
        audit.record_event(
            self._vault_dir,
            action="unlock",
            env_file=self.env_path.name,
        )
        return self.env_path

    def sync(self, target_path: Path, password: str) -> Path:
        """Merge decrypted secrets into *target_path*, record audit event.

        Keys present in the vault take precedence over those in *target_path*.
        Missing keys from *target_path* are preserved.
        """
        target_path = Path(target_path)

        ciphertext = self.enc_path.read_bytes()
        plaintext = decrypt(ciphertext, password)
        vault_env = parse_env(plaintext.decode())

        existing_env: dict = {}
        if target_path.exists():
            existing_env = parse_env(target_path.read_text(encoding="utf-8"))

        merged = merge_env(existing_env, vault_env)
        target_path.write_text(serialize_env(merged), encoding="utf-8")

        audit.record_event(
            self._vault_dir,
            action="sync",
            env_file=self.env_path.name,
            extra={"target": str(target_path)},
        )
        return target_path
