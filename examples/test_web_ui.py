#!/usr/bin/env python3
"""
Test script for the Web UI receiver.

This script generates sample transfer data that can be pasted into the web UI
for testing without needing to set up VNC or the sender.

Usage:
    1. Start the web receiver: python web_receiver.py
    2. Run this script: python examples/test_web_ui.py
    3. Copy the output and paste it into the web UI input area
"""

import sys
import os

# Add parent directory to path to import protocol
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from protocol import Frame, encode_frame, compute_sha256


def generate_test_transfer(text: str, chunk_size: int = 48) -> str:
    """
    Generate a complete transfer stream for testing.

    Args:
        text: Text to transfer
        chunk_size: Bytes per frame

    Returns:
        Complete transfer stream as string
    """
    data = text.encode('utf-8')
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

    return "\n".join(lines)


def main():
    print("=" * 70)
    print("CommSync Web UI Test Data Generator")
    print("=" * 70)
    print()

    # Sample text options
    samples = {
        '1': ("Short message", "Hello from CommSync Web UI!"),
        '2': ("Multi-line text", """This is a multi-line message.
It contains several lines of text.
Perfect for testing the web UI receiver.
The quick brown fox jumps over the lazy dog."""),
        '3': ("Lorem Ipsum", """Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum."""),
        '4': ("Unicode test", "Hello 世界! Привет мир! ¡Hola mundo! 🌍🚀✨"),
        '5': ("JSON data", """{
    "name": "CommSync",
    "version": "1.0",
    "features": [
        "Lossless transfer",
        "CRC verification",
        "SHA256 validation"
    ],
    "status": "active"
}""")
    }

    print("Select sample text to generate:")
    for key, (name, _) in samples.items():
        print(f"  {key}. {name}")
    print()

    choice = input("Enter choice (1-5) or 'c' for custom text: ").strip()

    if choice.lower() == 'c':
        print("\nEnter your custom text (press Ctrl+D or Ctrl+Z when done):")
        print("---")
        try:
            custom_lines = []
            while True:
                line = input()
                custom_lines.append(line)
        except EOFError:
            pass
        text = "\n".join(custom_lines)
    elif choice in samples:
        text = samples[choice][1]
    else:
        print("Invalid choice. Using default.")
        text = samples['1'][1]

    print()
    print("=" * 70)
    print("TRANSFER DATA - Copy everything below this line")
    print("=" * 70)

    transfer_data = generate_test_transfer(text)
    print(transfer_data)

    print("=" * 70)
    print("END OF TRANSFER DATA")
    print("=" * 70)
    print()
    print("Instructions:")
    print("1. Copy all lines between the separators")
    print("2. Open the web UI at http://localhost:5000")
    print("3. Click 'Start Receiving'")
    print("4. Paste the copied data into the input area")
    print("5. Watch the real-time verification!")
    print()

    # Save to file for convenience
    output_file = "/tmp/commsync_test_data.txt"
    with open(output_file, 'w') as f:
        f.write(transfer_data)
    print(f"Data also saved to: {output_file}")
    print("You can paste it from there if needed.")


if __name__ == "__main__":
    main()
