
import sys, time
print("Process A started.")
sys.stdout.flush()
for i in range(10):
    time.sleep(2)
    print(f"Process A heartbeat {i+1}")
    if i == 2:
        # ·¢ËÍÃüÁî¸øB
        print("[CMD:ProcB:Hello from A!]")
    sys.stdout.flush()
print("Process A finished.")
