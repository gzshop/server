
import random

a="0123456789abcdefghijklmnopqrstuvwxyz"

s=""
for item in range(12):
    s+=random.choice(a)

print(len(s))