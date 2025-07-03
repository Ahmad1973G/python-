import time

start_time = time.time()
i = 0
while i < 1000000:
    i += 1

end_time = time.time()
print(f"Execution time: {end_time - start_time} seconds")

a = 0.11202597618103027
b = 0.0017256

print(a / b)