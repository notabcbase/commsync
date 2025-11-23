# CommSync - Lossless Inter-Computer Communication via Keystrokes

A robust Python-based system for transferring text between two computers using only keyboard input (e.g., via VNC). This system guarantees **lossless** data transfer through comprehensive error detection and verification.

## Overview

CommSync enables reliable one-way communication from Computer A to Computer B where:
- **Computer A** (controller): Reads text from clipboard and emulates keystrokes into a VNC window
- **Computer B** (target): Receives keystrokes in a terminal and reconstructs the original text

### Key Features

✅ **Lossless Transfer**: Guarantees bit-perfect data recovery
✅ **Strong Verification**: Per-frame CRC-16 + end-to-end SHA256
✅ **Error Detection**: Immediate failure on any corruption
✅ **Simple Setup**: Pure Python with minimal dependencies
✅ **Configurable**: Adjustable chunk sizes and timing parameters

## How It Works

### Protocol Design

The system uses a robust frame-based protocol:

1. **Session Header**: Announces total size and SHA256 hash
   ```
   #SESSION:size=<bytes>:sha256=<hex>
   ```

2. **Data Frames**: Each frame contains:
   - Start marker: `!`
   - Sequence number: 4-digit hex (0000-FFFF)
   - Base64-encoded payload
   - CRC-16 checksum: 4-digit hex
   ```
   !<seq>:<base64_payload>:<crc16>
   Example: !0000:SGVsbG8gV29ybGQ=:A1B2
   ```

3. **Session End**: Marks transfer completion
   ```
   #END
   ```

### Verification Layers

1. **Per-Frame CRC-16**: Detects any corruption within individual frames
2. **Sequence Numbers**: Helps identify missing or duplicate frames
3. **End-to-End SHA256**: Verifies complete data integrity
4. **Byte Count**: Confirms all data was received

If ANY verification fails, the transfer is rejected with a clear error message.

## Installation

### Computer A (Sender)

Install dependencies for clipboard access and keyboard emulation:

```bash
pip install -r requirements-sender.txt
# or
pip install pynput pyperclip
```

Copy to Computer A:
- `protocol.py`
- `sender.py`

### Computer B (Receiver)

**No external dependencies required!** Uses only Python standard library.

Copy to Computer B:
- `protocol.py`
- `receiver.py`

## Usage

### Basic Workflow

#### Step 1: Start Receiver on Computer B

Open a terminal on Computer B and run:

```bash
# Save to file
python receiver.py > received.bin

# Or save as text file
python receiver.py -o received.txt -e utf-8

# Or display directly to console
python receiver.py -e utf-8
```

The receiver will wait for the transfer to begin.

#### Step 2: Prepare Sender on Computer A

1. Copy the text you want to send to your clipboard (Ctrl+C / Cmd+C)
2. Open your VNC client and connect to Computer B
3. Ensure the terminal running `receiver.py` is visible

#### Step 3: Send Data from Computer A

```bash
python sender.py
```

The script will:
1. Read your clipboard
2. Display transfer information
3. Give you 5 seconds to focus the VNC window
4. Type the data character-by-character into the VNC window

#### Step 4: Verify on Computer B

Once complete, Computer B will display:
```
[OK] Transfer verified successfully!
```

If there's any error, you'll see a detailed error message explaining what went wrong.

## Advanced Usage

### Sender Options

```bash
# Adjust chunk size (larger = fewer frames, more data per frame)
python sender.py --chunk-size 64

# Slow down typing (if VNC drops characters)
python sender.py --char-delay 0.02

# Change focus delay
python sender.py --focus-delay 10.0

# Use different text encoding
python sender.py --encoding latin-1

# Combine options
python sender.py --chunk-size 32 --char-delay 0.015 --focus-delay 8.0
```

### Receiver Options

```bash
# Save to specific file
python receiver.py -o output.txt -e utf-8

# Receive binary data
python receiver.py -o image.png

# Display as text with specific encoding
python receiver.py -e utf-8
```

## Examples

### Example 1: Transfer Code Snippet

On Computer A:
```bash
# Copy code to clipboard
cat mycode.py | xclip -selection clipboard  # Linux
# or pbcopy < mycode.py  # macOS

# Send via VNC
python sender.py
```

On Computer B:
```bash
python receiver.py -o received_code.py -e utf-8
```

### Example 2: Transfer JSON Configuration

On Computer A:
```bash
# Copy JSON to clipboard
cat config.json | xclip -selection clipboard

python sender.py
```

On Computer B:
```bash
python receiver.py -o config.json -e utf-8
```

### Example 3: Transfer Binary Data (Base64 Encoded)

On Computer A:
```bash
# First base64 encode the binary file
base64 image.png | xclip -selection clipboard

python sender.py
```

On Computer B:
```bash
# Receive and decode
python receiver.py -e utf-8 | base64 -d > image.png
```

## Troubleshooting

### Problem: Characters are being dropped

**Solution**: Increase the character delay on the sender:
```bash
python sender.py --char-delay 0.02
```

### Problem: Transfer is too slow

**Solution**: Decrease character delay and increase chunk size:
```bash
python sender.py --char-delay 0.005 --chunk-size 64
```

### Problem: CRC mismatch errors

**Causes**:
- VNC connection is unstable
- Character delay is too low
- Network latency issues

**Solution**:
1. Increase `--char-delay`
2. Ensure stable VNC connection
3. Reduce `--chunk-size` for smaller frames

### Problem: Size or SHA256 mismatch

**Causes**:
- Frames were lost during transfer
- Transfer was interrupted

**Solution**:
- Check that VNC window maintained focus
- Restart both receiver and sender
- Increase delays if network is slow

## Protocol Specifications

### Frame Format

```
!<SEQ>:<PAYLOAD>:<CRC>
```

- `!`: Literal start marker (1 byte)
- `<SEQ>`: Sequence number in hex, 4 digits (0000-FFFF)
- `<PAYLOAD>`: Base64-encoded data (variable length)
- `<CRC>`: CRC-16-CCITT checksum in hex, 4 digits

### Session Flow

```
1. Sender → #SESSION:size=N:sha256=HASH
2. Sender → !0000:PAYLOAD:CRC
3. Sender → !0001:PAYLOAD:CRC
   ...
N. Sender → !XXXX:PAYLOAD:CRC
N+1. Sender → #END

Receiver verifies:
- Each frame CRC matches payload
- Total bytes == size
- SHA256(all_bytes) == HASH
```

### Error Handling

The receiver will exit with error code 1 and detailed message if:
- Any frame fails CRC verification
- Non-frame data appears inside session
- Final byte count doesn't match header
- Final SHA256 doesn't match header

## Architecture

```
┌─────────────┐                    ┌─────────────┐
│ Computer A  │                    │ Computer B  │
│  (Sender)   │                    │ (Receiver)  │
│             │                    │             │
│  ┌────────┐ │                    │  ┌────────┐ │
│  │Clipboard│ │                    │  │Terminal│ │
│  └───┬────┘ │                    │  └───▲────┘ │
│      │      │                    │      │      │
│  ┌───▼────┐ │   VNC Keystrokes   │  ┌───┴────┐ │
│  │Protocol│ ├────────────────────┤  │Protocol│ │
│  │Encoder │ │                    │  │Decoder │ │
│  └───┬────┘ │                    │  └───┬────┘ │
│      │      │                    │      │      │
│  ┌───▼────┐ │                    │  ┌───▼────┐ │
│  │Keyboard│ │                    │  │  File  │ │
│  │Emulator│ │                    │  │ Output │ │
│  └────────┘ │                    │  └────────┘ │
└─────────────┘                    └─────────────┘
```

## Performance

Approximate transfer speeds (will vary based on VNC latency and settings):

| Char Delay | Chunk Size | Approx Speed | Use Case |
|------------|------------|--------------|----------|
| 0.01s      | 48 bytes   | ~100 chars/s | Default (reliable) |
| 0.005s     | 64 bytes   | ~200 chars/s | Fast network |
| 0.02s      | 32 bytes   | ~50 chars/s  | Slow/unstable network |

For a 10KB text file:
- Default settings: ~2 minutes
- Fast settings: ~1 minute
- Slow settings: ~3-4 minutes

## Security Considerations

- **Data Visibility**: All data is typed in plain text into the VNC window and visible on screen
- **No Encryption**: This protocol does not encrypt data; use VNC's built-in encryption for confidentiality
- **Integrity Only**: CRC and SHA256 provide integrity verification, not authentication
- **Trusted Path**: Assumes both computers and the VNC connection are trusted

## Testing

A test suite is provided to verify functionality:

```bash
# Run basic protocol tests
python test_protocol.py

# Run end-to-end simulation tests
python test_e2e.py
```

## Contributing

Contributions are welcome! Areas for improvement:

- Bidirectional communication support
- Automatic retry mechanism
- Progress bar in sender
- Support for file metadata (filename, permissions)
- Compression support
- Alternative encoding schemes

## License

MIT License - see LICENSE file for details

## Acknowledgments

Built using:
- [pynput](https://github.com/moses-palmer/pynput) - Keyboard control
- [pyperclip](https://github.com/asweigart/pyperclip) - Clipboard access
- Python standard library for protocol implementation

## FAQ

**Q: Why not use file transfer tools like scp, rsync, or VNC file transfer?**
A: This tool is designed for scenarios where only keyboard input is available or allowed, such as highly restricted environments or specific VNC configurations.

**Q: Can this transfer binary files?**
A: Yes, but you need to base64 encode them first. The protocol transfers text data losslessly.

**Q: What's the maximum transfer size?**
A: No hard limit, but practical limits depend on patience and VNC session stability. Tested with files up to several MB.

**Q: Can I use this over SSH instead of VNC?**
A: Yes! The same approach works. Just run the receiver on the SSH target and type into the SSH terminal.

**Q: Why CRC-16 instead of CRC-32?**
A: CRC-16 provides sufficient error detection for our frame sizes while keeping the frame format compact and human-readable.

**Q: Can Computer B send acknowledgments back?**
A: Not in the current design. The protocol is one-way. For bidirectional communication, you'd need to run instances in both directions or add a visual ACK mechanism.
