# Quick Start Guide

Get up and running with CommSync in 5 minutes.

Choose your preferred method:
- **Option 1**: Command-Line Receiver (fastest setup, no dependencies on Computer B)
- **Option 2**: Web UI Receiver (user-friendly, visual progress tracking)

## Prerequisites

- Python 3.7 or higher on both computers
- VNC connection from Computer A to Computer B
- On Computer A: `pip install pynput pyperclip`

## Setup - Option 1: Command-Line Receiver

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

---

## Setup - Option 2: Web UI Receiver (Recommended)

### Computer B (Receiver - VNC Target)

1. Copy files to Computer B:
   ```bash
   # Copy these files:
   protocol.py
   web_receiver.py
   templates/
   static/
   ```

2. Install web dependencies:
   ```bash
   pip install -r requirements-web.txt
   ```

3. Start the web receiver:
   ```bash
   python web_receiver.py
   ```

   You should see:
   ```
   Starting server on http://0.0.0.0:5000
   ```

4. Open a web browser and navigate to:
   ```
   http://localhost:5000
   ```

5. Click **"Start Receiving"** button in the web interface

6. The input area will be focused and ready

### Computer A (Sender - VNC Controller)

Same setup as Option 1:

1. Copy files: `protocol.py` and `sender.py`
2. Install dependencies: `pip install -r requirements-sender.txt`
3. Copy text to clipboard
4. Run `python sender.py`
5. Focus the VNC window showing the **web browser** with the input area
6. Watch real-time progress!

### Verification (Web UI)

The web interface will show:

```
✓ Status: Complete
  Frames Received: 30
  Bytes Received: 123 bytes
  Progress: [████████████████████] 100%

Activity Log:
[14:23:45] Session started. Expecting 123 bytes
[14:23:46] Received frame 10
[14:23:47] Received frame 20
[14:23:48] Transfer verified successfully!

Transfer Complete ✓
[Download Received Data]
```

Click the download button to save your file!

---

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

### Sticky keys (random capitalization like "HeLLo")
- **Most common issue!** Modifier keys (Shift/Ctrl/Alt) stick between characters
- Fix: `python sender.py --modifier-delay 0.01`
- For severe cases: `python sender.py --char-delay 0.02 --modifier-delay 0.015`

### Characters appearing wrong
- Increase delay: `python sender.py --char-delay 0.02`

### CRC mismatch errors
- VNC connection may be slow or modifiers are sticking
- Try: `python sender.py --char-delay 0.02 --modifier-delay 0.01 --chunk-size 32`

### Transfer too slow
- Speed up: `python sender.py --char-delay 0.005 --chunk-size 64`
- Note: Very fast transfers may cause sticky modifier keys

## Next Steps

- Read the full [README.md](README.md) for advanced usage and protocol details
- Check out [WEB_UI_GUIDE.md](WEB_UI_GUIDE.md) for comprehensive web UI documentation
- Run tests: `python test_protocol.py && python test_e2e.py`
- Try the CLI demo: `bash examples/demo.sh`
- Test the web UI: `python examples/test_web_ui.py` and paste into web interface

## Getting Help

If you run into issues:

1. Check both terminals for error messages
2. Verify Python version: `python --version` (need 3.7+)
3. Test VNC connection is stable
4. Try the demo script first to verify setup

## What's Happening

**Command-Line Mode:**
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

**Web UI Mode:**
```
Computer A                    Computer B
┌─────────┐                   ┌─────────┐
│Clipboard│                   │ Browser │
└────┬────┘                   │ Web UI  │
     │                        └────▲────┘
     ▼                             │
┌─────────┐   VNC Keystrokes  ┌────┴────┐
│ sender  ├──────────────────►│  Flask  │
│  .py    │   (to browser)    │ Server  │
└─────────┘                   └────┬────┘
                                   │
                              ┌────▼────┐
                              │Download │
                              └─────────┘
```

Each keystroke is verified with checksums to ensure lossless transfer!
Real-time progress updates keep you informed every step of the way.
