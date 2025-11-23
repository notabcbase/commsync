# Quick Start Guide

Get up and running with CommSync in 5 minutes.

## Prerequisites

- Python 3.7 or higher on both computers
- VNC connection from Computer A to Computer B
- On Computer A: `pip install pynput pyperclip`

## Setup

### Computer B (Receiver - VNC Target)

1. Copy files to Computer B:
   ```bash
   # Copy these files:
   protocol.py
   receiver.py
   ```

2. Open a terminal on Computer B

3. Start the receiver:
   ```bash
   python receiver.py -o received.txt -e utf-8
   ```

   You should see:
   ```
   [INFO] Waiting for transfer to begin...
   ```

### Computer A (Sender - VNC Controller)

1. Copy files to Computer A:
   ```bash
   # Copy these files:
   protocol.py
   sender.py
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements-sender.txt
   ```

3. Copy some text to your clipboard (Ctrl+C / Cmd+C)

4. Make sure your VNC window is open and showing Computer B's terminal

5. Run the sender:
   ```bash
   python sender.py
   ```

6. Within 5 seconds, click into the VNC window to focus it

7. Watch the transfer happen!

## Verification

On Computer B, you should see:

```
[INFO] Session started. Expecting 123 bytes
[INFO] Received 10 frames, 48 bytes
[INFO] Received 20 frames, 96 bytes
...
[INFO] Session END marker received.
[INFO] Received 123 bytes in 30 frames
[OK] Transfer verified successfully!
[INFO] Data written to: received.txt
```

Check the received file:
```bash
cat received.txt
```

## First Test - Simple Text

Try this simple test first:

1. On Computer A, copy this text to clipboard:
   ```
   Hello from CommSync!
   ```

2. On Computer B:
   ```bash
   python receiver.py -e utf-8
   ```

3. On Computer A:
   ```bash
   python sender.py
   ```

4. Focus VNC window and wait

5. Verify you see "Hello from CommSync!" on Computer B

## Common Issues

### "Clipboard is empty"
- Make sure you copied text to clipboard before running sender.py

### Characters appearing wrong
- Increase delay: `python sender.py --char-delay 0.02`

### CRC mismatch errors
- VNC connection may be slow
- Try: `python sender.py --char-delay 0.02 --chunk-size 32`

### Transfer too slow
- Speed up: `python sender.py --char-delay 0.005 --chunk-size 64`

## Next Steps

- Read the full [README.md](README.md) for advanced usage
- Run tests: `python test_protocol.py && python test_e2e.py`
- Try the demo: `bash examples/demo.sh`

## Getting Help

If you run into issues:

1. Check both terminals for error messages
2. Verify Python version: `python --version` (need 3.7+)
3. Test VNC connection is stable
4. Try the demo script first to verify setup

## What's Happening

```
Computer A                    Computer B
┌─────────┐                   ┌─────────┐
│Clipboard│                   │ Terminal│
└────┬────┘                   └────▲────┘
     │                             │
     ▼                             │
┌─────────┐   VNC Keystrokes  ┌────┴────┐
│ sender  ├──────────────────►│receiver │
│  .py    │                   │  .py    │
└─────────┘                   └────┬────┘
                                   │
                                   ▼
                              ┌─────────┐
                              │  File   │
                              └─────────┘
```

Each keystroke is verified with checksums to ensure lossless transfer!
