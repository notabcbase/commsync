#!/usr/bin/env python3
# sender.py (run on Computer A - the controlling machine)
"""
Sender script for Computer A (VNC controller).

This script:
1. Reads text from the system clipboard
2. Encodes it using the robust protocol
3. Types it character-by-character into the focused window (VNC terminal)

Usage:
    1. Copy text to clipboard (Ctrl/Cmd+C)
    2. Open VNC window with receiver.py running on Computer B
    3. Run: python sender.py
    4. Quickly focus the VNC window (5 second delay)
    5. Watch the transfer happen

Dependencies:
    - pynput: for keyboard emulation
    - pyperclip: for clipboard access
"""

import time
import sys
import argparse
import pyperclip
from pynput.keyboard import Controller, Key
from protocol import Frame, encode_frame, compute_sha256


class KeyboardTyper:
    """Handles typing characters into the focused window."""

    def __init__(self, char_delay: float = 0.01):
        """
        Initialize keyboard controller.

        Args:
            char_delay: Delay between characters in seconds (adjust if VNC drops chars)
        """
        self.keyboard = Controller()
        self.char_delay = char_delay

    def type_char(self, c: str):
        """
        Type a single character.

        Args:
            c: Character to type (or '\n' for Enter)
        """
        if c == "\n":
            self.keyboard.press(Key.enter)
            self.keyboard.release(Key.enter)
            time.sleep(self.char_delay)
            return

        self.keyboard.press(c)
        self.keyboard.release(c)
        time.sleep(self.char_delay)

    def type_string(self, s: str):
        """
        Type a complete string character-by-character.

        Args:
            s: String to type
        """
        for ch in s:
            self.type_char(ch)


def read_clipboard_bytes(encoding: str = "utf-8") -> bytes:
    """
    Read text from clipboard and encode to bytes.

    Args:
        encoding: Text encoding to use (default: utf-8)

    Returns:
        Encoded bytes from clipboard

    Raises:
        UnicodeEncodeError: If text cannot be encoded with specified encoding
    """
    text = pyperclip.paste()
    if text is None or text == "":
        raise ValueError("Clipboard is empty")
    return text.encode(encoding)


def send_data(data: bytes, typer: KeyboardTyper, chunk_size: int = 48, focus_delay: float = 5.0):
    """
    Send data by typing it into the focused window.

    Args:
        data: Bytes to send
        typer: KeyboardTyper instance
        chunk_size: Payload bytes per frame before base64 encoding
        focus_delay: Seconds to wait before starting (to focus VNC window)
    """
    total_size = len(data)
    sha256_hex = compute_sha256(data)

    print(f"[INFO] Data size: {total_size} bytes")
    print(f"[INFO] SHA256: {sha256_hex}")
    print(f"[INFO] You have {focus_delay} seconds to focus the VNC terminal window...")
    time.sleep(focus_delay)

    print("[INFO] Starting transfer...")

    # Send session header
    header_line = f"#SESSION:size={total_size}:sha256={sha256_hex}\n"
    typer.type_string(header_line)

    # Send data frames
    seq = 0
    total_frames = (total_size + chunk_size - 1) // chunk_size

    for i in range(0, total_size, chunk_size):
        chunk = data[i:i + chunk_size]
        frame = Frame(seq=seq, payload=chunk)
        frame_line = encode_frame(frame) + "\n"
        typer.type_string(frame_line)

        seq = (seq + 1) & 0xFFFF

        # Progress indicator
        frame_num = (i // chunk_size) + 1
        if frame_num % 10 == 0 or frame_num == total_frames:
            print(f"[INFO] Progress: {frame_num}/{total_frames} frames sent")

    # Send end marker
    end_line = "#END\n"
    typer.type_string(end_line)

    print("[INFO] Transfer complete! Check receiver output on Computer B.")


def main():
    parser = argparse.ArgumentParser(
        description="Send clipboard text to Computer B via VNC keystroke emulation"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=48,
        help="Payload bytes per frame (default: 48)"
    )
    parser.add_argument(
        "--char-delay",
        type=float,
        default=0.01,
        help="Delay between characters in seconds (default: 0.01)"
    )
    parser.add_argument(
        "--focus-delay",
        type=float,
        default=5.0,
        help="Seconds to wait before starting transfer (default: 5.0)"
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Text encoding (default: utf-8)"
    )

    args = parser.parse_args()

    try:
        # Read clipboard
        data = read_clipboard_bytes(encoding=args.encoding)

        # Create typer
        typer = KeyboardTyper(char_delay=args.char_delay)

        # Send data
        send_data(
            data=data,
            typer=typer,
            chunk_size=args.chunk_size,
            focus_delay=args.focus_delay
        )

    except ValueError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[INFO] Transfer cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
