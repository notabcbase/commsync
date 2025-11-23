#!/usr/bin/env python3
"""
End-to-end simulation test.

Simulates the complete sender-receiver workflow without actual keyboard/clipboard.
"""

import io
import sys
from protocol import Frame, encode_frame, compute_sha256


def simulate_transfer(data: bytes, chunk_size: int = 48) -> str:
    """
    Simulate the sender creating the full transfer stream.

    Args:
        data: Data to transfer
        chunk_size: Bytes per frame

    Returns:
        Complete transfer as a string (what would be typed)
    """
    total_size = len(data)
    sha256_hex = compute_sha256(data)

    lines = []

    # Session header
    lines.append(f"#SESSION:size={total_size}:sha256={sha256_hex}")

    # Data frames
    seq = 0
    for i in range(0, total_size, chunk_size):
        chunk = data[i:i + chunk_size]
        frame = Frame(seq=seq, payload=chunk)
        frame_line = encode_frame(frame)
        lines.append(frame_line)
        seq = (seq + 1) & 0xFFFF

    # End marker
    lines.append("#END")

    return "\n".join(lines) + "\n"


def simulate_receive(transfer_stream: str) -> tuple[bool, bytes, str]:
    """
    Simulate the receiver processing the transfer stream.

    Args:
        transfer_stream: The complete transfer stream

    Returns:
        Tuple of (success, data, error_message)
    """
    from protocol import decode_frame

    expected_size = None
    expected_sha256 = None
    collected = bytearray()
    in_session = False

    lines = transfer_stream.strip().split("\n")

    for line in lines:
        line = line.strip()

        # Session header
        if line.startswith("#SESSION:"):
            try:
                parts = line.split(":")
                size_part = next(p for p in parts if p.startswith("size="))
                hash_part = next(p for p in parts if p.startswith("sha256="))

                expected_size = int(size_part.split("=", 1)[1])
                expected_sha256 = hash_part.split("=", 1)[1]
                in_session = True
            except Exception as e:
                return False, b"", f"Invalid session header: {e}"
            continue

        # Session end
        if line == "#END":
            break

        if not in_session:
            continue

        # Decode frame
        try:
            frame = decode_frame(line)
        except ValueError as e:
            return False, b"", f"Frame CRC error: {e}"

        if frame is None:
            return False, b"", f"Invalid frame: {line[:50]}"

        collected.extend(frame.payload)

    # Verify
    if expected_size is None or expected_sha256 is None:
        return False, b"", "No session header"

    actual_size = len(collected)
    if actual_size != expected_size:
        return False, bytes(collected), f"Size mismatch: expected {expected_size}, got {actual_size}"

    actual_hash = compute_sha256(collected)
    if actual_hash != expected_sha256:
        return False, bytes(collected), f"SHA256 mismatch"

    return True, bytes(collected), ""


def test_basic_transfer():
    """Test basic text transfer."""
    print("Test: Basic text transfer")
    original = b"Hello, World!"

    stream = simulate_transfer(original)
    success, recovered, error = simulate_receive(stream)

    assert success, f"Transfer failed: {error}"
    assert recovered == original, "Data mismatch"
    print("  ✓ Passed")


def test_empty_transfer():
    """Test empty data transfer."""
    print("Test: Empty data transfer")
    original = b""

    stream = simulate_transfer(original)
    success, recovered, error = simulate_receive(stream)

    assert success, f"Transfer failed: {error}"
    assert recovered == original, "Data mismatch"
    print("  ✓ Passed")


def test_large_transfer():
    """Test larger data transfer."""
    print("Test: Large data transfer (10KB)")
    original = b"The quick brown fox jumps over the lazy dog.\n" * 200

    stream = simulate_transfer(original, chunk_size=64)
    success, recovered, error = simulate_receive(stream)

    assert success, f"Transfer failed: {error}"
    assert recovered == original, "Data mismatch"
    print("  ✓ Passed")


def test_binary_data():
    """Test binary data transfer."""
    print("Test: Binary data (all byte values)")
    original = bytes(range(256)) * 10

    stream = simulate_transfer(original)
    success, recovered, error = simulate_receive(stream)

    assert success, f"Transfer failed: {error}"
    assert recovered == original, "Data mismatch"
    print("  ✓ Passed")


def test_unicode_text():
    """Test unicode text transfer."""
    print("Test: Unicode text")
    text = "Hello 世界 🌍 Привет мир ¡Hola mundo!"
    original = text.encode("utf-8")

    stream = simulate_transfer(original)
    success, recovered, error = simulate_receive(stream)

    assert success, f"Transfer failed: {error}"
    assert recovered == original, "Data mismatch"

    recovered_text = recovered.decode("utf-8")
    assert recovered_text == text, "Text mismatch"
    print("  ✓ Passed")


def test_corrupted_payload():
    """Test detection of corrupted payload."""
    print("Test: Corrupted payload detection")
    original = b"Hello, World!"

    stream = simulate_transfer(original)

    # Corrupt one character in the stream
    lines = stream.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("!"):
            # Corrupt the payload part
            parts = line.split(":")
            if len(parts[1]) > 2:
                parts[1] = "X" + parts[1][1:]  # Change first char of base64
                lines[i] = ":".join(parts)
                break

    corrupted_stream = "\n".join(lines)
    success, recovered, error = simulate_receive(corrupted_stream)

    assert not success, "Should have detected corruption"
    assert "CRC" in error or "Invalid" in error, f"Unexpected error: {error}"
    print("  ✓ Passed")


def test_missing_data():
    """Test detection of missing data."""
    print("Test: Missing data detection")
    original = b"A" * 1000

    stream = simulate_transfer(original, chunk_size=48)

    # Remove one frame
    lines = stream.split("\n")
    frame_count = sum(1 for line in lines if line.startswith("!"))
    if frame_count > 1:
        # Find and remove second frame
        removed = 0
        for i in range(len(lines)):
            if lines[i].startswith("!"):
                removed += 1
                if removed == 2:
                    lines.pop(i)
                    break

    incomplete_stream = "\n".join(lines)
    success, recovered, error = simulate_receive(incomplete_stream)

    assert not success, "Should have detected missing data"
    assert "Size mismatch" in error or "SHA256" in error, f"Unexpected error: {error}"
    print("  ✓ Passed")


def test_different_chunk_sizes():
    """Test various chunk sizes."""
    print("Test: Different chunk sizes")
    original = b"Test data " * 50

    for chunk_size in [16, 32, 48, 64, 128]:
        stream = simulate_transfer(original, chunk_size=chunk_size)
        success, recovered, error = simulate_receive(stream)

        assert success, f"Failed with chunk_size={chunk_size}: {error}"
        assert recovered == original, f"Data mismatch with chunk_size={chunk_size}"

    print("  ✓ Passed")


def test_sequence_wraparound():
    """Test sequence number wraparound."""
    print("Test: Sequence number wraparound")

    # Create data that will require >65536 frames
    # Each frame with chunk_size=1 carries 1 byte
    # So we need >65536 bytes
    original = b"X" * 70000

    stream = simulate_transfer(original, chunk_size=1)
    success, recovered, error = simulate_receive(stream)

    assert success, f"Transfer failed: {error}"
    assert recovered == original, "Data mismatch"
    print("  ✓ Passed")


def run_all_tests():
    """Run all end-to-end tests."""
    print("=" * 60)
    print("End-to-End Simulation Tests")
    print("=" * 60)
    print()

    tests = [
        test_basic_transfer,
        test_empty_transfer,
        test_large_transfer,
        test_binary_data,
        test_unicode_text,
        test_corrupted_payload,
        test_missing_data,
        test_different_chunk_sizes,
        test_sequence_wraparound,
    ]

    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"  ✗ Failed: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ Error: {e}")
            failed += 1

    print()
    print("=" * 60)
    if failed == 0:
        print(f"All {len(tests)} tests passed!")
        print("=" * 60)
        return 0
    else:
        print(f"{failed}/{len(tests)} tests failed")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
