# CommSync Web UI Guide

Complete guide for using the web-based receiver interface.

## Overview

The CommSync Web UI provides a real-time browser-based interface for receiving data transfers. It offers:

- **Real-time progress visualization**
- **Activity logging** with timestamps
- **Automatic data verification**
- **Download capability** for received data
- **User-friendly interface** with status indicators

## Installation

### On Computer B (Receiver)

1. Install web dependencies:
   ```bash
   pip install -r requirements-web.txt
   ```

   This installs:
   - Flask (web framework)
   - Flask-SocketIO (real-time communication)
   - python-socketio (WebSocket support)
   - eventlet (async server)

2. Copy required files to Computer B:
   ```
   protocol.py
   web_receiver.py
   templates/index.html
   static/css/style.css
   static/js/app.js
   ```

## Starting the Web Receiver

### Basic Usage

```bash
python web_receiver.py
```

This starts the server on `http://0.0.0.0:5000` (accessible from any network interface).

### Custom Configuration

```bash
# Custom port
python web_receiver.py --port 8080

# Specific host (localhost only)
python web_receiver.py --host 127.0.0.1

# Debug mode (for development)
python web_receiver.py --debug

# Combined
python web_receiver.py --host 0.0.0.0 --port 8000
```

### Command-Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | 0.0.0.0 | Host to bind to (0.0.0.0 = all interfaces) |
| `--port` | 5000 | Port number |
| `--debug` | False | Enable debug mode (more verbose logging) |

## Using the Web Interface

### Step 1: Access the Interface

1. Start the web receiver on Computer B:
   ```bash
   python web_receiver.py
   ```

2. Open a web browser and navigate to:
   ```
   http://localhost:5000
   ```

   Or from another computer on the same network:
   ```
   http://<computer-b-ip>:5000
   ```

### Step 2: Start Receiving

Click the **"Start Receiving"** button. The interface will:
- Enable receiving mode
- Focus the input area
- Wait for transfer data

### Step 3: Transfer Data

You have two options:

#### Option A: Paste Method (Quick Testing)

1. On Computer A, run the sender to generate transfer data
2. Copy the output (all lines including `#SESSION`, frames, and `#END`)
3. Paste into the web UI input area
4. Data is processed automatically

#### Option B: VNC Typing Method (Production Use)

1. Ensure the web browser on Computer B is visible via VNC
2. Focus the input area in the web UI
3. On Computer A, run:
   ```bash
   python sender.py
   ```
4. Focus the VNC window pointing at the web UI input area
5. Watch real-time updates as data is typed

### Step 4: Monitor Progress

The web UI displays:

- **Status Panel**: Current session state, frame count, bytes received
- **Progress Bar**: Visual progress with percentage
- **Activity Log**: Real-time event log with timestamps
- **Transfer Speed**: Calculated throughput

### Step 5: Complete & Download

When transfer completes:

1. **Verification happens automatically**:
   - Size check
   - SHA256 hash verification

2. **Results displayed**:
   - Total bytes received
   - Number of frames
   - Transfer duration
   - Average speed
   - Data preview (first 500 chars)

3. **Download the data**:
   - Click **"Download Received Data"**
   - Saves as `received.txt` (text) or `received.bin` (binary)

## Interface Components

### Status Panel

Shows real-time transfer statistics:

```
┌─────────────────────────────────────┐
│ Session Status: Receiving           │
│ Frames Received: 42                 │
│ Bytes Received: 2.1 KB              │
│ Expected Size: 5.2 KB               │
└─────────────────────────────────────┘
```

Status values:
- **Idle**: Waiting to start
- **Receiving**: Transfer in progress
- **Complete**: Successfully finished
- **Error**: Transfer failed

### Progress Bar

Visual indicator of transfer completion:
```
[████████████░░░░░░░░] 65%
```

Updates in real-time as frames are received.

### Activity Log

Chronological event log:
```
[14:23:45] System ready. Click "Start Receiving" to begin.
[14:24:01] Receiving mode activated. Waiting for transfer data...
[14:24:05] Session started. Expecting 5234 bytes
[14:24:06] Received frame 10
[14:24:07] Received frame 20
...
[14:24:15] Transfer verified successfully!
```

Log entry types:
- **Info** (blue): General information
- **Success** (green): Positive events
- **Error** (red): Failures or issues
- **Frame** (gray): Frame reception events

### Results Panel

Displayed after successful transfer:

```
┌─────────────────────────────────────┐
│ Transfer Complete ✓                 │
│                                     │
│ Total Bytes: 5.2 KB                 │
│ Frames: 110                         │
│ Duration: 8.5 seconds               │
│ Speed: 627 bytes/s                  │
│                                     │
│ Data Preview:                       │
│ Hello, World!                       │
│ This is a test...                   │
│                                     │
│ [Download Received Data]            │
└─────────────────────────────────────┘
```

### Error Panel

Displayed if verification fails:

```
┌─────────────────────────────────────┐
│ ⚠ Error                             │
│                                     │
│ CRC mismatch: got A1B2, expected... │
│                                     │
│ [Reset and Try Again]               │
└─────────────────────────────────────┘
```

## Workflow Comparison

### Command-Line Receiver vs Web UI

| Feature | CLI Receiver | Web UI |
|---------|--------------|--------|
| Real-time progress | Stderr messages | Visual progress bar |
| Status display | Text output | Color-coded panels |
| Data preview | Manual file read | Automatic preview |
| Download | File redirect | One-click download |
| Multiple sessions | Restart script | Reset button |
| User-friendliness | Technical | Beginner-friendly |
| Remote monitoring | SSH required | Any web browser |

## Advanced Features

### Multiple Concurrent Users

The web UI supports multiple browser connections viewing the same transfer:

1. Open the URL in multiple browsers
2. All see real-time updates
3. Only one person needs to input data
4. Everyone can download the result

### Keyboard Shortcuts

- **Ctrl/Cmd + S**: Start receiving
- **Ctrl/Cmd + R**: Reset session (when not receiving)

### Auto-Processing

Input is processed automatically when:
- A complete line is entered (ends with newline)
- Data is pasted into the input area
- VNC types data into the input area

### API Endpoints

For integration with other tools:

```bash
# Get current status (JSON)
curl http://localhost:5000/api/status

# Reset session
curl -X POST http://localhost:5000/api/reset

# Download received data
curl http://localhost:5000/api/download > received.bin
```

## Troubleshooting

### Server Won't Start

**Error**: `Address already in use`

**Solution**: Port 5000 is occupied. Use a different port:
```bash
python web_receiver.py --port 8080
```

### Can't Access from Other Computers

**Problem**: Browser on Computer A can't reach web UI on Computer B

**Solutions**:
1. Check firewall allows port 5000
2. Verify using `--host 0.0.0.0` (not `127.0.0.1`)
3. Use Computer B's IP address: `http://192.168.1.100:5000`

### Real-time Updates Not Working

**Problem**: Progress doesn't update in real-time

**Solutions**:
1. Check browser supports WebSockets (modern browsers do)
2. Refresh the page
3. Check browser console for errors (F12)
4. Verify Flask-SocketIO is installed

### Transfer Stuck at 0%

**Problem**: Status shows "Receiving" but no progress

**Solutions**:
1. Verify sender is actually typing into the input area
2. Check if VNC window is focused correctly
3. Try pasting sample data manually to test
4. Check activity log for error messages

### Download Returns Empty File

**Problem**: Transfer shows complete but download is empty

**Solution**: This shouldn't happen if verification passed. Try:
1. Check browser downloads folder
2. Check browser console for errors
3. Reset and retry transfer

## Performance Tips

### For Large Transfers

1. **Increase chunk size** on sender:
   ```bash
   python sender.py --chunk-size 128
   ```

2. **Monitor activity log**: Every 10th frame is logged to reduce spam

3. **Use modern browser**: Chrome/Firefox perform better with WebSockets

### For Slow Networks

1. **Decrease typing speed**:
   ```bash
   python sender.py --char-delay 0.02
   ```

2. **Use smaller chunks**:
   ```bash
   python sender.py --chunk-size 32
   ```

## Security Considerations

### Network Exposure

The web receiver binds to `0.0.0.0` by default, making it accessible from any network interface.

**For production use**:

1. **Use firewall** to restrict access:
   ```bash
   # Allow only from specific IP
   sudo ufw allow from 192.168.1.0/24 to any port 5000
   ```

2. **Bind to localhost** if only local access needed:
   ```bash
   python web_receiver.py --host 127.0.0.1
   ```

3. **Use VPN** for remote access instead of exposing port

### Data Privacy

- **No encryption**: Data is transmitted/stored in plain text
- **No authentication**: Anyone with URL access can receive data
- **Session data**: Remains in memory until reset

**Recommendations**:
- Use only on trusted networks
- Reset session after each transfer
- Don't transfer sensitive data without additional encryption

## Example: Complete Transfer Session

### Setup (Computer B)

```bash
# Install dependencies
pip install -r requirements-web.txt

# Start web receiver
python web_receiver.py

# Output:
# ============================================================
# CommSync Web Receiver
# ============================================================
# Starting server on http://0.0.0.0:5000
#
# Open the URL in your browser, then:
# 1. Click 'Start Receiving' to begin a new session
# 2. Type data into the input area (or paste the transfer)
# 3. Watch real-time progress updates
# 4. Download the received data when complete
```

### Browser (Computer B or anywhere on network)

1. Open `http://<computer-b-ip>:5000`
2. Click **"Start Receiving"**
3. Input area is now focused and ready

### Sender (Computer A)

```bash
# Copy text to clipboard
echo "Hello from CommSync Web UI!" | xclip -selection clipboard

# Run sender
python sender.py --char-delay 0.015

# Focus VNC window with web browser showing the input area
```

### Result (Web UI)

```
Activity Log:
[14:30:01] Receiving mode activated. Waiting for transfer data...
[14:30:05] Session started. Expecting 28 bytes
[14:30:06] Received frame 10
[14:30:07] Transfer verified successfully!

Results:
✓ Transfer Complete
  Total Bytes: 28
  Frames: 1
  Duration: 1.5 seconds
  Speed: 18.67 bytes/s

Data Preview:
Hello from CommSync Web UI!

[Download Received Data]
```

## Development

### Running in Debug Mode

```bash
python web_receiver.py --debug
```

Enables:
- Auto-reload on code changes
- Detailed error traces
- Flask debug toolbar

### Customizing the UI

Edit these files:
- `templates/index.html` - HTML structure
- `static/css/style.css` - Styling
- `static/js/app.js` - Client-side logic

Changes to templates/static files are loaded on refresh.

### Testing Without VNC

Use the paste method:

1. Generate test data:
   ```python
   from protocol import Frame, encode_frame, compute_sha256
   data = b"Test data"
   print(f"#SESSION:size={len(data)}:sha256={compute_sha256(data)}")
   print(encode_frame(Frame(0, data)))
   print("#END")
   ```

2. Copy output and paste into web UI

## FAQ

**Q: Can I use this over the internet?**
A: Yes, but use VPN or SSH tunnel for security. Don't expose port directly.

**Q: Does it work on mobile browsers?**
A: Yes! The UI is responsive and works on tablets/phones.

**Q: Can I receive multiple transfers without restarting?**
A: Yes, click "Reset Session" between transfers.

**Q: What happens if I close the browser during transfer?**
A: Data is lost. The server doesn't persist sessions. Start over.

**Q: Can I integrate this with my own application?**
A: Yes, use the `/api/*` endpoints or embed the receiver logic in your app.

**Q: Is there a sender web UI too?**
A: Not currently. The sender requires clipboard access and keyboard emulation, which browsers restrict.

## Next Steps

- Try the [Quick Start Guide](QUICKSTART.md) for command-line receiver
- Read the [main README](README.md) for protocol details
- Run tests: `python test_protocol.py && python test_e2e.py`
- Check examples in `examples/` directory

## Support

For issues or questions:
- Check the activity log for error messages
- Verify all dependencies are installed
- Test with the demo script first
- Review the troubleshooting section above
