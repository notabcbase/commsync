#!/usr/bin/env python3
# receiver.py (run on Computer B - the remote/VNC target machine)
"""
Receiver script for Computer B (VNC target).

This script:
1. Reads encoded frames from stdin (typed via VNC)
2. Decodes and verifies each frame using CRC-16
3. Assembles the complete data
4. Verifies integrity using SHA256 hash
5. Outputs the recovered data

Usage:
    # To receive and save to file:
    python receiver.py > received.bin

    # To receive and view as text:
    python receiver.py --output received.txt --encoding utf-8

    # To receive and display to console:
    python receiver.py --encoding utf-8

The script will provide detailed status information on stderr,
so redirecting stdout won't hide progress messages.
"""

import sys
import argparse
from typing import Optional
from protocol import decode_frame, compute_sha256


class TransferSession:
    """Manages a single transfer session."""

    def __init__(self, output_file: Optional[str] = None, encoding: Optional[str] = None):
        """
        Initialize transfer session.

        Args:
            output_file: Optional file path to write received data
            encoding: Optional text encoding (if set, decode and display as text)
        """
        self.output_file = output_file
        self.encoding = encoding
        self.expected_size: Optional[int] = None
        self.expected_sha256: Optional[str] = None
        self.collected = bytearray()
        self.in_session = False
        self.frame_count = 0

    def parse_session_header(self, line: str) -> bool:
        """
        Parse session header line.

        Format: #SESSION:size=<bytes>:sha256=<hash>

        Args:
            line: Header line to parse

        Returns:
            True if header was valid and parsed successfully
        """
        if not line.startswith("#SESSION:"):
            return False

        try:
            parts = line.split(":")
            size_part = next(p for p in parts if p.startswith("size="))
            hash_part = next(p for p in parts if p.startswith("sha256="))

            self.expected_size = int(size_part.split("=", 1)[1])
            self.expected_sha256 = hash_part.split("=", 1)[1]
            self.in_session = True

            print(
                f"[INFO] Session started. Expecting {self.expected_size} bytes",
                file=sys.stderr
            )
            return True
        except Exception as e:
            print(f"[ERROR] Invalid session header: {e}", file=sys.stderr)
            return False

    def process_frame(self, line: str) -> bool:
        """
        Process a single frame line.

        Args:
            line: Frame line to process

        Returns:
            True if frame was valid and processed successfully

        Raises:
            ValueError: If frame CRC check fails
        """
        try:
            frame = decode_frame(line)
        except ValueError as e:
            print(f"[ERROR] Bad frame (CRC mismatch): {e}", file=sys.stderr)
            raise

        if frame is None:
            # Not a frame line
            print(
                f"[ERROR] Non-frame line inside session: {line[:50]}...",
                file=sys.stderr
            )
            return False

        self.collected.extend(frame.payload)
        self.frame_count += 1

        # Progress indicator every 10 frames
        if self.frame_count % 10 == 0:
            print(
                f"[INFO] Received {self.frame_count} frames, {len(self.collected)} bytes",
                file=sys.stderr
            )

        return True

    def verify_and_save(self) -> bool:
        """
        Verify received data integrity and save/output.

        Returns:
            True if verification passed and data was saved successfully
        """
        if self.expected_size is None or self.expected_sha256 is None:
            print("[ERROR] No valid session header received.", file=sys.stderr)
            return False

        actual_size = len(self.collected)
        actual_hash = compute_sha256(self.collected)

        print(f"[INFO] Received {actual_size} bytes in {self.frame_count} frames", file=sys.stderr)

        # Verify size
        if actual_size != self.expected_size:
            print(
                f"[ERROR] Size mismatch: expected {self.expected_size}, got {actual_size}",
                file=sys.stderr
            )
            return False

        # Verify hash
        if actual_hash != self.expected_sha256:
            print(
                f"[ERROR] SHA256 mismatch:\n"
                f"  expected: {self.expected_sha256}\n"
                f"  got:      {actual_hash}",
                file=sys.stderr
            )
            return False

        print("[OK] Transfer verified successfully!", file=sys.stderr)

        # Output the data
        data = bytes(self.collected)

        if self.output_file:
            # Write to file
            with open(self.output_file, "wb") as f:
                f.write(data)
            print(f"[INFO] Data written to: {self.output_file}", file=sys.stderr)
        else:
            # Write to stdout
            if self.encoding:
                # Decode as text
                try:
                    text = data.decode(self.encoding)
                    sys.stdout.write(text)
                except UnicodeDecodeError as e:
                    print(f"[ERROR] Failed to decode as {self.encoding}: {e}", file=sys.stderr)
                    return False
            else:
                # Write raw bytes
                sys.stdout.buffer.write(data)

        return True


def receive_transfer(session: TransferSession):
    """
    Main receive loop.

    Args:
        session: TransferSession instance

    Raises:
        ValueError: If frame verification fails
    """
    for raw_line in sys.stdin:
        line = raw_line.rstrip("\n")

        # Check for session header
        if line.startswith("#SESSION:"):
            if not session.parse_session_header(line):
                sys.exit(1)
            continue

        # Check for session end
        if line.strip() == "#END":
            print("[INFO] Session END marker received.", file=sys.stderr)
            break

        # Ignore lines before session starts
        if not session.in_session:
            continue

        # Process frame
        if not session.process_frame(line):
            sys.exit(1)

    # Verify and save
    if not session.verify_and_save():
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Receive data from Computer A via VNC keystroke transfer"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: stdout)"
    )
    parser.add_argument(
        "-e", "--encoding",
        help="Text encoding to decode with (e.g., utf-8). If not set, outputs raw bytes."
    )

    args = parser.parse_args()

    # Create session
    session = TransferSession(
        output_file=args.output,
        encoding=args.encoding
    )

    print("[INFO] Waiting for transfer to begin...", file=sys.stderr)
    print("[INFO] (Sender should type session header)", file=sys.stderr)

    try:
        receive_transfer(session)
    except KeyboardInterrupt:
        print("\n[INFO] Transfer cancelled by user", file=sys.stderr)
        sys.exit(1)
    except ValueError:
        # Already logged
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
