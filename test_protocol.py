#!/usr/bin/env python3
"""
Unit tests for the protocol module.

Tests encoding/decoding, CRC verification, and edge cases.
"""

import unittest
from protocol import Frame, encode_frame, decode_frame, crc16_ccitt, compute_sha256


class TestCRC16(unittest.TestCase):
    """Test CRC-16 checksum calculation."""

    def test_empty_data(self):
        """Test CRC of empty data."""
        result = crc16_ccitt(b"")
        self.assertIsInstance(result, int)
        self.assertEqual(result, 0xFFFF)

    def test_known_values(self):
        """Test CRC with known values."""
        # These are standard test vectors for CRC-16-CCITT
        result = crc16_ccitt(b"123456789")
        self.assertEqual(result, 0x29B1)

    def test_different_data_different_crc(self):
        """Verify different data produces different CRCs."""
        crc1 = crc16_ccitt(b"Hello")
        crc2 = crc16_ccitt(b"World")
        self.assertNotEqual(crc1, crc2)


class TestSHA256(unittest.TestCase):
    """Test SHA256 hash calculation."""

    def test_empty_data(self):
        """Test SHA256 of empty data."""
        result = compute_sha256(b"")
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        self.assertEqual(result, expected)

    def test_known_value(self):
        """Test SHA256 with known value."""
        result = compute_sha256(b"Hello, World!")
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        self.assertEqual(result, expected)


class TestFrameEncoding(unittest.TestCase):
    """Test frame encoding."""

    def test_basic_encoding(self):
        """Test basic frame encoding."""
        frame = Frame(seq=0, payload=b"Hello, World!")
        encoded = encode_frame(frame)

        # Should start with !
        self.assertTrue(encoded.startswith("!"))

        # Should contain colons
        self.assertEqual(encoded.count(":"), 2)

        # Should be ASCII
        self.assertTrue(encoded.isascii())

    def test_sequence_number_formatting(self):
        """Test sequence number is properly formatted."""
        frame = Frame(seq=255, payload=b"test")
        encoded = encode_frame(frame)
        # Sequence should be 4-digit hex: 00FF
        self.assertTrue(encoded.startswith("!00FF:"))

    def test_max_sequence(self):
        """Test maximum sequence number."""
        frame = Frame(seq=0xFFFF, payload=b"test")
        encoded = encode_frame(frame)
        self.assertTrue(encoded.startswith("!FFFF:"))

    def test_invalid_sequence_low(self):
        """Test sequence number below range."""
        frame = Frame(seq=-1, payload=b"test")
        with self.assertRaises(ValueError):
            encode_frame(frame)

    def test_invalid_sequence_high(self):
        """Test sequence number above range."""
        frame = Frame(seq=0x10000, payload=b"test")
        with self.assertRaises(ValueError):
            encode_frame(frame)

    def test_empty_payload(self):
        """Test encoding empty payload."""
        frame = Frame(seq=0, payload=b"")
        encoded = encode_frame(frame)
        # Should still be valid format
        parts = encoded.split(":")
        self.assertEqual(len(parts), 3)

    def test_binary_payload(self):
        """Test encoding binary data."""
        frame = Frame(seq=0, payload=bytes(range(256)))
        encoded = encode_frame(frame)
        # Should be ASCII despite binary payload
        self.assertTrue(encoded.isascii())


class TestFrameDecoding(unittest.TestCase):
    """Test frame decoding."""

    def test_roundtrip(self):
        """Test encode-decode roundtrip."""
        original = Frame(seq=42, payload=b"Hello, World!")
        encoded = encode_frame(original)
        decoded = decode_frame(encoded)

        self.assertIsNotNone(decoded)
        self.assertEqual(decoded.seq, original.seq)
        self.assertEqual(decoded.payload, original.payload)

    def test_with_newline(self):
        """Test decoding with trailing newline."""
        frame = Frame(seq=0, payload=b"test")
        encoded = encode_frame(frame) + "\n"
        decoded = decode_frame(encoded)

        self.assertIsNotNone(decoded)
        self.assertEqual(decoded.payload, b"test")

    def test_invalid_start_marker(self):
        """Test decoding line without start marker."""
        result = decode_frame("#SESSION:size=100")
        self.assertIsNone(result)

    def test_corrupted_crc(self):
        """Test detection of CRC corruption."""
        frame = Frame(seq=0, payload=b"Hello")
        encoded = encode_frame(frame)

        # Corrupt the CRC
        parts = encoded.split(":")
        parts[2] = "DEAD"  # Wrong CRC
        corrupted = ":".join(parts)

        with self.assertRaises(ValueError) as ctx:
            decode_frame(corrupted)
        self.assertIn("CRC mismatch", str(ctx.exception))

    def test_corrupted_payload(self):
        """Test detection of payload corruption."""
        frame = Frame(seq=0, payload=b"Hello")
        encoded = encode_frame(frame)

        # Corrupt the payload (but keep structure)
        parts = encoded.split(":")
        # Change one character in base64
        payload_b64 = parts[1]
        if len(payload_b64) > 0:
            corrupted_b64 = "X" + payload_b64[1:]
            parts[1] = corrupted_b64
            corrupted = ":".join(parts)

            with self.assertRaises(ValueError):
                decode_frame(corrupted)

    def test_malformed_structure(self):
        """Test decoding malformed frame."""
        result = decode_frame("!ABCD:PAYLOAD")  # Missing CRC
        self.assertIsNone(result)

    def test_invalid_base64(self):
        """Test decoding invalid base64."""
        result = decode_frame("!0000:!!!INVALID!!!:1234")
        self.assertIsNone(result)


class TestBinaryPayloads(unittest.TestCase):
    """Test handling of various binary payloads."""

    def test_null_bytes(self):
        """Test payload with null bytes."""
        frame = Frame(seq=0, payload=b"\x00\x00\x00")
        encoded = encode_frame(frame)
        decoded = decode_frame(encoded)

        self.assertEqual(decoded.payload, b"\x00\x00\x00")

    def test_all_byte_values(self):
        """Test payload with all possible byte values."""
        frame = Frame(seq=0, payload=bytes(range(256)))
        encoded = encode_frame(frame)
        decoded = decode_frame(encoded)

        self.assertEqual(decoded.payload, bytes(range(256)))

    def test_unicode_text(self):
        """Test payload with UTF-8 encoded unicode."""
        text = "Hello 世界 🌍"
        payload = text.encode("utf-8")

        frame = Frame(seq=0, payload=payload)
        encoded = encode_frame(frame)
        decoded = decode_frame(encoded)

        recovered_text = decoded.payload.decode("utf-8")
        self.assertEqual(recovered_text, text)


class TestSequenceWrapAround(unittest.TestCase):
    """Test sequence number wrap-around behavior."""

    def test_sequence_wraparound(self):
        """Test that sequence can wrap from FFFF to 0000."""
        # This is expected behavior for the protocol
        frame1 = Frame(seq=0xFFFF, payload=b"last")
        frame2 = Frame(seq=0x0000, payload=b"first")

        encoded1 = encode_frame(frame1)
        encoded2 = encode_frame(frame2)

        decoded1 = decode_frame(encoded1)
        decoded2 = decode_frame(encoded2)

        self.assertEqual(decoded1.seq, 0xFFFF)
        self.assertEqual(decoded2.seq, 0x0000)


def run_tests():
    """Run all tests and report results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCRC16))
    suite.addTests(loader.loadTestsFromTestCase(TestSHA256))
    suite.addTests(loader.loadTestsFromTestCase(TestFrameEncoding))
    suite.addTests(loader.loadTestsFromTestCase(TestFrameDecoding))
    suite.addTests(loader.loadTestsFromTestCase(TestBinaryPayloads))
    suite.addTests(loader.loadTestsFromTestCase(TestSequenceWrapAround))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    exit(run_tests())
