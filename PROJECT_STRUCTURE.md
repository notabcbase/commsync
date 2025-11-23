# Project Structure

Complete file layout and description of all components in the CommSync repository.

## Directory Structure

```
commsync/
├── protocol.py              # Core protocol implementation (shared)
├── sender.py               # Sender application (Computer A)
├── receiver.py             # Command-line receiver (Computer B)
├── web_receiver.py         # Web UI receiver (Computer B)
│
├── templates/              # Web UI HTML templates
│   └── index.html          #   Main web interface
│
├── static/                 # Web UI static assets
│   ├── css/
│   │   └── style.css       #   Web UI styling
│   └── js/
│       └── app.js          #   Client-side JavaScript
│
├── examples/               # Example files and demos
│   ├── demo.sh             #   CLI demo script
│   ├── test_web_ui.py      #   Web UI test data generator
│   └── example_text.txt    #   Sample text file
│
├── test_protocol.py        # Protocol unit tests
├── test_e2e.py            # End-to-end simulation tests
│
├── requirements.txt        # All dependencies (combined)
├── requirements-sender.txt # Sender-only dependencies
├── requirements-web.txt    # Web UI dependencies
│
├── README.md              # Main documentation
├── QUICKSTART.md          # Quick start guide
├── WEB_UI_GUIDE.md        # Web UI detailed guide
├── PROJECT_STRUCTURE.md   # This file
├── LICENSE                # MIT License
└── .gitignore            # Git ignore rules
```

## Core Components

### protocol.py
**Location**: Root
**Used by**: All components
**Dependencies**: Python standard library only
**Description**:
- Core protocol encoding/decoding
- CRC-16 checksum calculation
- SHA256 hash computation
- Frame serialization/deserialization
- Shared by both sender and receiver

**Key Functions**:
- `encode_frame(frame)` - Encode frame to ASCII string
- `decode_frame(line)` - Decode ASCII string to frame
- `crc16_ccitt(data)` - Calculate CRC-16 checksum
- `compute_sha256(data)` - Calculate SHA256 hash

### sender.py
**Location**: Root
**Used on**: Computer A (controller)
**Dependencies**: pynput, pyperclip, protocol.py
**Description**:
- Reads text from system clipboard
- Encodes data using protocol.py
- Types data via keyboard emulation
- Supports VNC/remote desktop typing

**Command-line options**:
- `--chunk-size` - Payload bytes per frame (default: 48)
- `--char-delay` - Delay between keystrokes (default: 0.01s)
- `--focus-delay` - Time to focus window (default: 5.0s)
- `--encoding` - Text encoding (default: utf-8)

### receiver.py
**Location**: Root
**Used on**: Computer B (target)
**Dependencies**: Python standard library, protocol.py
**Description**:
- Reads encoded frames from stdin
- Decodes using protocol.py
- Verifies CRC and SHA256
- Outputs received data to file/stdout

**Command-line options**:
- `-o, --output` - Output file path
- `-e, --encoding` - Text encoding for output

### web_receiver.py
**Location**: Root
**Used on**: Computer B (target)
**Dependencies**: Flask, Flask-SocketIO, python-socketio, eventlet, protocol.py
**Description**:
- Flask web server with WebSocket support
- Real-time browser interface
- Progress tracking and visualization
- Automatic verification and download

**Command-line options**:
- `--host` - Host to bind to (default: 0.0.0.0)
- `--port` - Port number (default: 5000)
- `--debug` - Enable debug mode

## Web UI Components

### templates/index.html
**Description**: Main web interface HTML
- Status panel with real-time updates
- Progress bar visualization
- Input area for receiving data
- Activity log with timestamps
- Results/error panels
- Download button

### static/css/style.css
**Description**: Web UI styling
- Responsive design (mobile-friendly)
- Color-coded status indicators
- Animated progress bars
- Professional gradient theme
- Smooth transitions

### static/js/app.js
**Description**: Client-side JavaScript
- Socket.IO WebSocket client
- Real-time event handling
- DOM manipulation for updates
- Auto-processing of input
- Keyboard shortcuts support

## Testing Components

### test_protocol.py
**Description**: Unit tests for protocol module
- CRC-16 calculation tests
- SHA256 hash tests
- Frame encoding/decoding tests
- Error detection tests
- Edge case handling

**Test coverage**:
- 18 test cases
- 6 test classes
- All protocol functions tested

### test_e2e.py
**Description**: End-to-end simulation tests
- Complete transfer simulations
- Corruption detection tests
- Large file transfers
- Unicode and binary data
- Sequence wraparound

**Test coverage**:
- 9 comprehensive tests
- Various chunk sizes
- Error scenarios
- Success scenarios

## Example Files

### examples/demo.sh
**Description**: CLI demonstration script
- Simulates transfer without VNC
- Uses stdio for testing
- Generates sample data
- Runs receiver locally

### examples/test_web_ui.py
**Description**: Web UI test data generator
- Creates sample transfer data
- Multiple text samples available
- Custom text support
- Saves to temporary file

### examples/example_text.txt
**Description**: Sample text file
- Multi-line text example
- Unicode characters
- Special symbols
- For manual testing

## Documentation Files

### README.md
**Purpose**: Main project documentation
**Contents**:
- Overview and features
- Protocol specification
- Installation instructions
- Usage examples (CLI and Web UI)
- Advanced configuration
- Troubleshooting guide
- Architecture diagrams
- Performance benchmarks
- Security considerations
- FAQ section

**Audience**: All users

### QUICKSTART.md
**Purpose**: Quick setup guide
**Contents**:
- 5-minute setup instructions
- Both CLI and Web UI options
- Prerequisites
- First test walkthrough
- Common issues
- Visual diagrams

**Audience**: New users

### WEB_UI_GUIDE.md
**Purpose**: Comprehensive web UI guide
**Contents**:
- Detailed installation steps
- Web UI feature tour
- Interface components explained
- API endpoint documentation
- Troubleshooting web-specific issues
- Performance tuning
- Security considerations
- Development guide

**Audience**: Web UI users

### PROJECT_STRUCTURE.md
**Purpose**: Repository organization reference
**Contents**: This file
**Audience**: Developers and contributors

## Configuration Files

### requirements.txt
**Description**: Combined dependencies for all components
```
pynput>=1.7.6
pyperclip>=1.8.2
Flask>=2.3.0
Flask-SocketIO>=5.3.0
python-socketio>=5.9.0
eventlet>=0.33.0
```

### requirements-sender.txt
**Description**: Sender-only dependencies (Computer A)
```
pynput>=1.7.6
pyperclip>=1.8.2
```

### requirements-web.txt
**Description**: Web UI dependencies (Computer B)
```
Flask>=2.3.0
Flask-SocketIO>=5.3.0
python-socketio>=5.9.0
eventlet>=0.33.0
```

### .gitignore
**Description**: Git ignore patterns
- Python bytecode
- Virtual environments
- IDE files
- Test outputs
- OS-specific files

## Deployment Scenarios

### Minimal Setup (CLI only)

**Computer A**:
- protocol.py
- sender.py
- requirements-sender.txt

**Computer B**:
- protocol.py
- receiver.py
- No dependencies needed!

### Full Setup (with Web UI)

**Computer A**:
- protocol.py
- sender.py
- requirements-sender.txt

**Computer B**:
- protocol.py
- web_receiver.py
- templates/
- static/
- requirements-web.txt

### Development Setup

**All files including**:
- All source files
- All tests
- All examples
- All documentation
- All requirements files

## File Dependencies

```
sender.py
  ├── protocol.py
  ├── pynput (external)
  └── pyperclip (external)

receiver.py
  └── protocol.py

web_receiver.py
  ├── protocol.py
  ├── templates/index.html
  ├── static/css/style.css
  ├── static/js/app.js
  ├── Flask (external)
  ├── Flask-SocketIO (external)
  ├── python-socketio (external)
  └── eventlet (external)

test_protocol.py
  └── protocol.py

test_e2e.py
  └── protocol.py

examples/test_web_ui.py
  └── protocol.py
```

## Data Flow

### Sender Flow
```
User Clipboard
    ↓
sender.py
    ↓
protocol.py (encode)
    ↓
Keyboard Emulation
    ↓
VNC/Remote Desktop
```

### Receiver Flow (CLI)
```
VNC/Terminal Input
    ↓
receiver.py (stdin)
    ↓
protocol.py (decode)
    ↓
File/stdout
```

### Receiver Flow (Web UI)
```
VNC/Browser Input
    ↓
web_receiver.py (Flask)
    ↓
WebSocket (Socket.IO)
    ↓
Browser (JavaScript)
    ↓
protocol.py (decode)
    ↓
Download
```

## Version History

All components are version 1.0, included in initial release.

## File Sizes

Approximate file sizes (actual may vary):

| File | Lines | Size |
|------|-------|------|
| protocol.py | ~150 | ~5 KB |
| sender.py | ~200 | ~8 KB |
| receiver.py | ~200 | ~8 KB |
| web_receiver.py | ~350 | ~14 KB |
| templates/index.html | ~120 | ~5 KB |
| static/css/style.css | ~380 | ~12 KB |
| static/js/app.js | ~300 | ~10 KB |
| test_protocol.py | ~350 | ~12 KB |
| test_e2e.py | ~250 | ~9 KB |
| README.md | ~530 | ~18 KB |
| WEB_UI_GUIDE.md | ~525 | ~18 KB |
| QUICKSTART.md | ~255 | ~9 KB |

**Total**: ~2,800 lines of code and documentation

## Contributing

When contributing, please maintain this structure:
- Core protocol code stays in protocol.py
- UI-specific code in separate files
- Tests in root directory with test_ prefix
- Examples in examples/ directory
- Documentation in root as .md files
- Web assets in static/ and templates/

## License

All files in this repository are licensed under MIT License.
See LICENSE file for details.
