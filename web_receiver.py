#!/usr/bin/env python3
"""
Web-based receiver for CommSync.

Provides a real-time web interface for receiving data transfers.
Uses Flask and Flask-SocketIO for live updates.

Usage:
    python web_receiver.py [--port 5000] [--host 0.0.0.0]

Then open http://localhost:5000 in your browser and start the receiver.
"""

import sys
import argparse
import threading
import queue
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from protocol import decode_frame, compute_sha256


app = Flask(__name__)
app.config['SECRET_KEY'] = 'commsync-receiver-secret'
socketio = SocketIO(app, cors_allowed_origins="*")


class WebReceiverSession:
    """Manages a single web-based transfer session."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset session to initial state."""
        self.expected_size = None
        self.expected_sha256 = None
        self.collected = bytearray()
        self.in_session = False
        self.frame_count = 0
        self.start_time = None
        self.end_time = None
        self.status = "idle"  # idle, receiving, complete, error
        self.error_message = None

    def get_stats(self):
        """Get current session statistics."""
        stats = {
            'status': self.status,
            'frame_count': self.frame_count,
            'bytes_received': len(self.collected),
            'expected_size': self.expected_size,
            'expected_sha256': self.expected_sha256,
            'error_message': self.error_message,
        }

        if self.expected_size and self.expected_size > 0:
            stats['progress_percent'] = (len(self.collected) / self.expected_size) * 100
        else:
            stats['progress_percent'] = 0

        if self.start_time:
            stats['start_time'] = self.start_time.isoformat()

        if self.end_time:
            stats['end_time'] = self.end_time.isoformat()
            duration = (self.end_time - self.start_time).total_seconds()
            stats['duration_seconds'] = duration
            if duration > 0:
                stats['bytes_per_second'] = len(self.collected) / duration

        return stats

    def process_line(self, line):
        """
        Process a single line of input.

        Returns:
            dict: Update information to send to frontend
        """
        line = line.strip()

        # Session header
        if line.startswith("#SESSION:"):
            return self._handle_session_header(line)

        # Session end
        if line == "#END":
            return self._handle_session_end()

        # Frame data
        if self.in_session:
            return self._handle_frame(line)

        return {
            'type': 'info',
            'message': 'Waiting for session to start...'
        }

    def _handle_session_header(self, line):
        """Handle session header."""
        try:
            parts = line.split(":")
            size_part = next(p for p in parts if p.startswith("size="))
            hash_part = next(p for p in parts if p.startswith("sha256="))

            self.expected_size = int(size_part.split("=", 1)[1])
            self.expected_sha256 = hash_part.split("=", 1)[1]
            self.in_session = True
            self.status = "receiving"
            self.start_time = datetime.now()

            return {
                'type': 'session_start',
                'expected_size': self.expected_size,
                'expected_sha256': self.expected_sha256,
                'message': f'Session started. Expecting {self.expected_size} bytes'
            }
        except Exception as e:
            self.status = "error"
            self.error_message = f"Invalid session header: {e}"
            return {
                'type': 'error',
                'message': self.error_message
            }

    def _handle_frame(self, line):
        """Handle a data frame."""
        try:
            frame = decode_frame(line)
        except ValueError as e:
            self.status = "error"
            self.error_message = f"CRC mismatch: {e}"
            return {
                'type': 'error',
                'message': self.error_message
            }

        if frame is None:
            self.status = "error"
            self.error_message = f"Invalid frame: {line[:50]}..."
            return {
                'type': 'error',
                'message': self.error_message
            }

        self.collected.extend(frame.payload)
        self.frame_count += 1

        progress = 0
        if self.expected_size and self.expected_size > 0:
            progress = (len(self.collected) / self.expected_size) * 100

        return {
            'type': 'frame',
            'frame_count': self.frame_count,
            'bytes_received': len(self.collected),
            'progress_percent': progress,
            'message': f'Received frame {self.frame_count}'
        }

    def _handle_session_end(self):
        """Handle session end and verify data."""
        self.end_time = datetime.now()

        if not self.in_session:
            self.status = "error"
            self.error_message = "END marker without session"
            return {
                'type': 'error',
                'message': self.error_message
            }

        # Verify size
        actual_size = len(self.collected)
        if actual_size != self.expected_size:
            self.status = "error"
            self.error_message = f"Size mismatch: expected {self.expected_size}, got {actual_size}"
            return {
                'type': 'error',
                'message': self.error_message
            }

        # Verify hash
        actual_hash = compute_sha256(self.collected)
        if actual_hash != self.expected_sha256:
            self.status = "error"
            self.error_message = "SHA256 mismatch"
            return {
                'type': 'error',
                'message': self.error_message,
                'expected_hash': self.expected_sha256,
                'actual_hash': actual_hash
            }

        # Success!
        self.status = "complete"
        duration = (self.end_time - self.start_time).total_seconds()

        return {
            'type': 'complete',
            'message': 'Transfer verified successfully!',
            'bytes_received': actual_size,
            'frame_count': self.frame_count,
            'duration_seconds': duration,
            'bytes_per_second': actual_size / duration if duration > 0 else 0,
            'data_preview': self._get_data_preview()
        }

    def _get_data_preview(self, max_chars=500):
        """Get a preview of the received data."""
        data = bytes(self.collected)

        # Try to decode as UTF-8
        try:
            text = data.decode('utf-8')
            if len(text) > max_chars:
                return text[:max_chars] + f"... ({len(text) - max_chars} more chars)"
            return text
        except UnicodeDecodeError:
            # Binary data
            return f"<Binary data, {len(data)} bytes>"

    def get_data(self):
        """Get the complete received data."""
        return bytes(self.collected)


# Global session instance
current_session = WebReceiverSession()


@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')


@app.route('/api/status')
def get_status():
    """Get current session status."""
    return jsonify(current_session.get_stats())


@app.route('/api/reset', methods=['POST'])
def reset_session():
    """Reset the current session."""
    current_session.reset()
    socketio.emit('session_reset', {}, namespace='/')
    return jsonify({'status': 'ok', 'message': 'Session reset'})


@app.route('/api/download')
def download_data():
    """Download the received data."""
    if current_session.status != "complete":
        return jsonify({'error': 'No completed transfer'}), 400

    data = current_session.get_data()

    # Try to determine if it's text or binary
    try:
        text = data.decode('utf-8')
        return text, 200, {
            'Content-Type': 'text/plain; charset=utf-8',
            'Content-Disposition': 'attachment; filename="received.txt"'
        }
    except UnicodeDecodeError:
        return data, 200, {
            'Content-Type': 'application/octet-stream',
            'Content-Disposition': 'attachment; filename="received.bin"'
        }


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    emit('status', current_session.get_stats())


@socketio.on('input_line')
def handle_input_line(data):
    """Handle a line of input from the client."""
    line = data.get('line', '')

    # Process the line
    update = current_session.process_line(line)

    # Broadcast update to all connected clients
    socketio.emit('update', update, namespace='/')

    # Also send current stats
    socketio.emit('stats', current_session.get_stats(), namespace='/')


@socketio.on('paste_data')
def handle_paste_data(data):
    """Handle pasted data (multiple lines at once)."""
    text = data.get('text', '')
    lines = text.strip().split('\n')

    for line in lines:
        if line.strip():
            update = current_session.process_line(line)
            socketio.emit('update', update, namespace='/')

    # Send final stats
    socketio.emit('stats', current_session.get_stats(), namespace='/')


def main():
    """Run the web receiver."""
    parser = argparse.ArgumentParser(
        description="Web-based receiver for CommSync"
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Host to bind to (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to bind to (default: 5000)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("CommSync Web Receiver")
    print("=" * 60)
    print(f"Starting server on http://{args.host}:{args.port}")
    print()
    print("Open the URL in your browser, then:")
    print("1. Click 'Start Receiving' to begin a new session")
    print("2. Type data into the input area (or paste the transfer)")
    print("3. Watch real-time progress updates")
    print("4. Download the received data when complete")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)

    socketio.run(
        app,
        host=args.host,
        port=args.port,
        debug=args.debug,
        allow_unsafe_werkzeug=True
    )


if __name__ == '__main__':
    main()
