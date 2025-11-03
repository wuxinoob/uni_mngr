import time
import random
import os
import sys
for i in range(10):
    time.sleep(1)
    print(f"output {i}/  ",end="@@")
    #sys.stdout.write(f"output {i}/  ")
    sys.stdout.flush()