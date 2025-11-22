
import sys, time
print("Process B started, waiting for input...")
sys.stdout.flush()
for line in sys.stdin:
    print(f"Process B received: {line.strip()}")
    sys.stdout.flush()
