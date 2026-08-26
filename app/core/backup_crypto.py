"""Cifrado autenticado y administración local de llaves para respaldos SGPN."""

import base64
import binascii
import hashlib
import hmac
import os
from contextlib import suppress
from pathlib import Path
from tempfile import NamedTemporaryFile

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

BACKUP_MAGIC = b"SGPNBK01"
BACKUP_VERSION = 1
NONCE_SIZE = 12
KEY_ID_SIZE = 8
TAG_SIZE = 16
HEADER_SIZE = len(BACKUP_MAGIC) + 1 + KEY_ID_SIZE + NONCE_SIZE
CHUNK_SIZE = 1024 * 1024
KEY_FILE_HEADER = "SGPN_BACKUP_KEY_V1"


class BackupSecurityError(RuntimeError):
    """El respaldo o la llave no permiten una operación criptográfica segura."""


def _decode_key(value: str) -> bytes:
    candidate = str(value or "").strip()
    if "\n" in candidate or candidate.startswith(KEY_FILE_HEADER):
        fields = {}
        for line in candidate.splitlines():
            if "=" in line:
                name, content = line.split("=", maxsplit=1)
                fields[name.strip().lower()] = content.strip()
        candidate = fields.get("key", "")
    try:
        decoded = base64.b64decode(candidate.encode("ascii"), altchars=b"-_", validate=True)
    except (UnicodeEncodeError, ValueError, binascii.Error) as error:
        raise BackupSecurityError("La llave de recuperación no tiene un formato válido.") from error
    if len(decoded) != 32:
        raise BackupSecurityError("La llave de recuperación no tiene un formato válido.")
    return decoded


def encode_key(key: bytes) -> str:
    if len(key) != 32:
        raise BackupSecurityError("La llave de recuperación no tiene un formato válido.")
    return base64.urlsafe_b64encode(key).decode("ascii")


def key_fingerprint(key: bytes) -> str:
    digest = hashlib.sha256(key).hexdigest()[:16].upper()
    return "-".join(digest[index : index + 4] for index in range(0, len(digest), 4))


def recovery_key_document(key: bytes) -> bytes:
    content = (
        f"{KEY_FILE_HEADER}\n"
        f"fingerprint={key_fingerprint(key)}\n"
        f"key={encode_key(key)}\n"
    )
    return content.encode("ascii")


def default_key_path(database_path) -> Path:
    return Path(database_path).resolve().parent / ".backup_key"


def load_or_create_backup_key(*, database_path, key_path=None) -> tuple[bytes, str]:
    configured = os.environ.get("SGPN_BACKUP_KEY")
    if configured:
        return _decode_key(configured), "environment"

    target = Path(key_path or default_key_path(database_path)).resolve()
    if target.exists():
        if not target.is_file():
            raise BackupSecurityError("No se pudo abrir la llave de recuperación.")
        try:
            return _decode_key(target.read_text(encoding="ascii")), "file"
        except (OSError, UnicodeError) as error:
            raise BackupSecurityError("No se pudo abrir la llave de recuperación.") from error

    target.parent.mkdir(parents=True, exist_ok=True)
    key = os.urandom(32)
    try:
        with target.open("x", encoding="ascii", newline="\n") as key_file:
            key_file.write(recovery_key_document(key).decode("ascii"))
            key_file.flush()
            os.fsync(key_file.fileno())
        with suppress(OSError):
            target.chmod(0o600)
    except FileExistsError:
        return load_or_create_backup_key(database_path=database_path, key_path=target)
    except OSError as error:
        with suppress(OSError):
            target.unlink(missing_ok=True)
        raise BackupSecurityError("No se pudo crear la llave de recuperación.") from error
    return key, "file"


def backup_key_status(*, database_path, key_path=None) -> dict:
    key, source = load_or_create_backup_key(database_path=database_path, key_path=key_path)
    return {
        "fingerprint": key_fingerprint(key),
        "source": source,
        "exportable": source == "file",
    }


def encrypt_file(source, destination, key: bytes) -> None:
    source_path = Path(source).resolve()
    destination_path = Path(destination).resolve()
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    nonce = os.urandom(NONCE_SIZE)
    identifier = hashlib.sha256(key).digest()[:KEY_ID_SIZE]
    header = BACKUP_MAGIC + bytes((BACKUP_VERSION,)) + identifier + nonce
    temporary = destination_path.with_name(f".{destination_path.name}.{os.getpid()}.tmp")
    temporary.unlink(missing_ok=True)
    encryptor = Cipher(algorithms.AES(key), modes.GCM(nonce)).encryptor()
    encryptor.authenticate_additional_data(header)
    try:
        with source_path.open("rb") as source_file, temporary.open("xb") as encrypted_file:
            encrypted_file.write(header)
            while chunk := source_file.read(CHUNK_SIZE):
                encrypted_file.write(encryptor.update(chunk))
            encrypted_file.write(encryptor.finalize())
            encrypted_file.write(encryptor.tag)
            encrypted_file.flush()
            os.fsync(encrypted_file.fileno())
        temporary.replace(destination_path)
        with suppress(OSError):
            destination_path.chmod(0o600)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def decrypt_file(source, destination, key: bytes) -> None:
    source_path = Path(source).resolve()
    destination_path = Path(destination).resolve()
    if not source_path.is_file() or source_path.stat().st_size <= HEADER_SIZE + TAG_SIZE:
        raise BackupSecurityError("La copia está dañada o incompleta.")

    try:
        with source_path.open("rb") as encrypted_file:
            header = encrypted_file.read(HEADER_SIZE)
            if header[: len(BACKUP_MAGIC)] != BACKUP_MAGIC or header[len(BACKUP_MAGIC)] != BACKUP_VERSION:
                raise BackupSecurityError("La copia no tiene un formato compatible.")
            identifier_start = len(BACKUP_MAGIC) + 1
            identifier = header[identifier_start : identifier_start + KEY_ID_SIZE]
            expected_identifier = hashlib.sha256(key).digest()[:KEY_ID_SIZE]
            if not hmac.compare_digest(identifier, expected_identifier):
                raise BackupSecurityError("Esta copia necesita otra llave de recuperación.")
            nonce = header[-NONCE_SIZE:]
            encrypted_file.seek(-TAG_SIZE, os.SEEK_END)
            tag = encrypted_file.read(TAG_SIZE)
            ciphertext_size = source_path.stat().st_size - HEADER_SIZE - TAG_SIZE
            encrypted_file.seek(HEADER_SIZE)
            decryptor = Cipher(algorithms.AES(key), modes.GCM(nonce, tag)).decryptor()
            decryptor.authenticate_additional_data(header)
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination_path.with_name(f".{destination_path.name}.{os.getpid()}.tmp")
            temporary.unlink(missing_ok=True)
            try:
                remaining = ciphertext_size
                with temporary.open("xb") as decrypted_file:
                    while remaining:
                        chunk = encrypted_file.read(min(CHUNK_SIZE, remaining))
                        if not chunk:
                            raise BackupSecurityError("La copia está dañada o incompleta.")
                        remaining -= len(chunk)
                        decrypted_file.write(decryptor.update(chunk))
                    decrypted_file.write(decryptor.finalize())
                    decrypted_file.flush()
                    os.fsync(decrypted_file.fileno())
                temporary.replace(destination_path)
                with suppress(OSError):
                    destination_path.chmod(0o600)
            except Exception:
                temporary.unlink(missing_ok=True)
                raise
    except BackupSecurityError:
        raise
    except Exception as error:
        raise BackupSecurityError("La copia está dañada, fue modificada o usa otra llave.") from error


def temporary_decrypted_path(directory: Path):
    with NamedTemporaryFile(prefix=".sgpn-verify-", suffix=".db", dir=directory, delete=False) as handle:
        path = Path(handle.name)
    path.unlink(missing_ok=True)
    return path
