"""Key rotation: re-encrypt a vault file with a new password."""

from __future__ import annotations

from pathlib import Path

from envault.crypto import decrypt, encrypt
from envault.keystore import KeyStore
from envault.audit import record_event


class RotationError(Exception):
    """Raised when key rotation fails."""


def rotate_key(
    env_file: Path,
    keystore: KeyStore,
    old_password: str,
    new_password: str,
    *,
    vault_dir: Path | None = None,
) -> Path:
    """Re-encrypt *env_file* with *new_password*.

    The encrypted file path is derived from *env_file* by appending '.enc'.
    The old ciphertext is decrypted with *old_password*, then immediately
    re-encrypted with *new_password* and written back to the same path.

    Parameters
    ----------
    env_file:     Path to the plaintext .env file (used to derive .enc path).
    keystore:     Active KeyStore instance (used to update stored key name).
    old_password: Password currently protecting the vault.
    new_password: Replacement password.
    vault_dir:    Override directory for audit log (defaults to env_file parent).

    Returns the path to the re-encrypted file.
    """
    enc_path = env_file.with_suffix(env_file.suffix + ".enc")

    if not enc_path.exists():
        raise RotationError(f"Encrypted file not found: {enc_path}")

    ciphertext = enc_path.read_bytes()

    try:
        plaintext = decrypt(ciphertext, old_password)
    except Exception as exc:
        raise RotationError("Failed to decrypt with old password — wrong password?") from exc

    new_ciphertext = encrypt(plaintext, new_password)
    enc_path.write_bytes(new_ciphertext)

    key_name = env_file.stem
    keystore.set(key_name, new_password)

    audit_dir = vault_dir or env_file.parent
    record_event(
        "rotate",
        {"env_file": str(env_file), "enc_file": str(enc_path)},
        vault_dir=audit_dir,
    )

    return enc_path
