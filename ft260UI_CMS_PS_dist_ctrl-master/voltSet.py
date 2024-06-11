import serial
import sys
import lib1785b
import time

ser = serial.Serial("/dev/ttyUSB0") # "/dev/ttyUSB0", "com2" etc...
#should define the serial as the port connected to ALDO supply
lib1785b.remoteMode(True, ser)

def volt(voltage, t=5):
    print("Setting voltage to " + str(voltage) + "V")
    dt = 0.25 #length of time for each step in seconds
    data = lib1785b.readAll(ser)
    v0 = float(data['vset'])
    if t == 0:
        t = dt
    v1 = float(voltage)
    nt = t / dt #number of steps
    dv = (v1-v0)/nt #voltage step
    newV = v0
    
    print("v0 = " + str(v0) + "\nSteps: " + str(nt) + " over " + str(t) + " seconds")
    lib1785b.outputOn(True, ser) #Turns on the output
    for i in range(int(nt)):
        newV = newV + dv
        lib1785b.volt(newV, ser)
        time.sleep(dt)
    lib1785b.volt(v1, ser)