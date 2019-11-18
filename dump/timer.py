import time

start = time.time()
# whatever you want to time, put between these two statements
time.sleep(3)
end = time.time()
elapsed = round(end - start)
#if you want to convert to minutes, just divide
min = round(elapsed / 60,2)
print "Your stuff took", elapsed, "seconds to run, which is the same as", min, "minutes"


