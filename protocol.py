# protocol.py
"""
Shared protocol module for lossless text transfer via keystrokes.

This module provides the core encoding/decoding functionality for transferring
data between two computers using only keyboard input (e.g., via VNC).

Protocol Format:
- Session header: #SESSION:size=<bytes>:sha256=<hash>
- Data frames: !<seq>:<base64_payload>:<crc16>
- Session end: #END

Each frame includes CRC-16 checksum for integrity verification.
The entire session includes SHA256 hash for end-to-end verification.
"""

import base64
import binascii
import hashlib
from dataclasses import dataclass
from typing import Optional


def crc16_ccitt(data: bytes, seed: int = 0xFFFF) -> int:
    """
    Calculate CRC-16-CCITT checksum using binascii.crc_hqx.

    Args:
        data: Bytes to checksum
        seed: Initial CRC value (default 0xFFFF)

    Returns:
        16-bit CRC checksum
    """
    return binascii.crc_hqx(data, seed) & 0xFFFF


@dataclass
class Frame:
    """Represents a single data frame in the transfer protocol."""
    seq: int  # Sequence number (0-65535)
    payload: bytes  # Raw payload data


def encode_frame(frame: Frame) -> str:
    """
    Encode a frame to a single-line ASCII string.

    Format: !<seq_hex>:<base64_payload>:<crc_hex>
    Example: !0000:SGVsbG8=:A1B2

    Args:
        frame: Frame to encode

    Returns:
        Encoded frame string (without newline)

    Raises:
        ValueError: If sequence number is out of range
    """
    if not (0 <= frame.seq <= 0xFFFF):
        raise ValueError("seq out of range 0..65535")

    payload_b64 = base64.b64encode(frame.payload).decode("ascii")
    checksum = crc16_ccitt(frame.payload)
    return f"!{frame.seq:04X}:{payload_b64}:{checksum:04X}"


def decode_frame(line: str) -> Optional[Frame]:
    """
    Decode a frame line back into a Frame object.

    Args:
        line: Encoded frame string

    Returns:
        Decoded Frame object, or None if line is not a valid frame

    Raises:
        ValueError: If checksum verification fails
    """
    line = line.strip()
    if not line.startswith("!"):
        return None

    try:
        _, rest = line[0], line[1:]
        seq_hex, payload_b64, crc_hex = rest.split(":", 2)
        seq = int(seq_hex, 16)
        expected_crc = int(crc_hex, 16)
    except Exception:
        return None

    try:
        payload = base64.b64decode(payload_b64.encode("ascii"), validate=True)
    except Exception:
        return None

    actual_crc = crc16_ccitt(payload)
    if actual_crc != expected_crc:
        raise ValueError(
            f"CRC mismatch: got {actual_crc:04X}, expected {expected_crc:04X}"
        )

    return Frame(seq=seq, payload=payload)


def compute_sha256(data: bytes) -> str:
    """
    Compute SHA256 hash of data.

    Args:
        data: Bytes to hash

    Returns:
        Hexadecimal SHA256 hash string
    """
    return hashlib.sha256(data).hexdigest()
