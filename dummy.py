import sys
import time


def flush_then_wait():
    sys.stdout.flush()
    sys.stderr.flush()
    time.sleep(0.5)


print("Script stdout 1\n")
print("Script stdout 2\n")
print("Script stdout 3\n")
sys.stderr.write("Total time: 00:05:00\n")
sys.stderr.write("Total complete: 10%\n")
flush_then_wait()

print("name=Martin\n")
print("Script stdout 4\n")
print("Script stdout 5\n")
sys.stderr.write("Total complete: 30%\n")
flush_then_wait()

sys.stderr.write("Elapsed time: 00:00:10\n")
sys.stderr.write("Elapsed time: 00:00:50\n")
sys.stderr.write("Total complete: 50%\n")
print("country=Nederland\n")
flush_then_wait()

sys.stderr.write("Elapsed time: 00:01:10\n")
sys.stderr.write("Total complete: 100%\n")
print("Script stdout 6\n")
print("Script stdout 7\n")
print("website=www.mfitzp.com\n")
flush_then_wait()
