#!/bin/bash
# Demo script for CommSync
# This simulates a transfer using stdio instead of actual VNC typing

set -e

echo "CommSync Demo - Simulated Transfer"
echo "==================================="
echo ""

# Create test data
TEST_DATA="Hello from CommSync! This is a test of lossless communication via keystrokes. 世界 🌍"
echo "Test data: $TEST_DATA"
echo ""

# Simulate sender creating the stream
echo "Step 1: Sender encoding data..."
python3 -c "
from protocol import Frame, encode_frame, compute_sha256
import sys

data = sys.argv[1].encode('utf-8')
total_size = len(data)
sha256_hex = compute_sha256(data)

print(f'#SESSION:size={total_size}:sha256={sha256_hex}')

chunk_size = 16
seq = 0
for i in range(0, total_size, chunk_size):
    chunk = data[i:i + chunk_size]
    frame = Frame(seq=seq, payload=chunk)
    print(encode_frame(frame))
    seq = (seq + 1) & 0xFFFF

print('#END')
" "$TEST_DATA" > /tmp/commsync_demo_stream.txt

echo "  Encoded stream saved to /tmp/commsync_demo_stream.txt"
echo ""

# Show the stream
echo "Step 2: Transfer stream (what gets typed):"
echo "---"
cat /tmp/commsync_demo_stream.txt
echo "---"
echo ""

# Simulate receiver
echo "Step 3: Receiver decoding data..."
python3 receiver.py -e utf-8 < /tmp/commsync_demo_stream.txt 2>/tmp/commsync_demo_stderr.txt

echo ""
echo "Step 4: Receiver status:"
cat /tmp/commsync_demo_stderr.txt

echo ""
echo "Demo complete!"

# Cleanup
rm -f /tmp/commsync_demo_stream.txt /tmp/commsync_demo_stderr.txt
