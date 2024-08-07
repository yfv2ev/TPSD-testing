import serial
import serial.tools.list_ports
import sys
import time
import lib1685b

def find_bPOLs(vidTarget, pidTarget):
    sers = []
    for portRead in serial.tools.list_ports.comports():
        if portRead[2] != 'n/a':
            #print(f"{portRead[0]}: {portRead[2]}")
            vidpid = portRead[2].split(' ')[1].split('=')[1]
            vid = hex(int("0x"+vidpid.split(':')[0], 16))
            pid = hex(int("0x"+vidpid.split(':')[1], 16))
            #print(f"{vid}: {pid}")
            if vid==hex(vidTarget) and pid==hex(pidTarget):
                port=portRead[0]
                ser = serial.Serial(port)
                ser.timeout = 0.1
                vMax = lib1685b.getMaxVoltCurr(ser)[0]
                if vMax < 25:
                    sers.append(ser)
                else:
                    ser.close()
    if len(sers) > 0:
        return sers
    raise Exception("Could not find bpol PS")

vidTarget = 0x10c4
pidTarget = 0xea60
sers = find_bPOLs(vidTarget, pidTarget)
ser1 = sers[0]
if len(sers) > 1:
    ser2 = sers[1]

def occupiedPort():
    if len(sers) == 1:
        name = [ser1.name]
        return name
    if len(sers) == 2:
        name = [ser1.name, ser2.name]
        return name
    
#ser1 = serial.Serial("/dev/ttyUSB0", timeout=0.1) #Note that this uses the same port as the ALDOs.
# This has to be fixed before trying to control both simultaneously.
#ser2 = serial.Serial("/dev/ttyUSB0", timeout=0.1) #This port is for the second bPOL12V power supply. It should be changed when a new USB port is made available

def stepVolt(ser, v0, v1, t=5, dt=0.25):
    nt = t/dt
    dv = (v1-v0)/nt
    newV = v0
    for i in range(int(nt)):
        newV = newV + dv
        lib1685b.setVoltage(ser, newV)
        time.sleep(dt)
    lib1685b.setVoltage(ser, v1)
    
def waitUntilVolt(ser, volt, timeout=10):
    counter = 0
    while not abs(float(lib1685b.getData(ser)[0]) - volt) <= 0.2:
        time.sleep(0.05)
        counter += 1
        if counter >= 20*timeout: # timeout seconds
            break
    
def off(t=5):
    for ser in sers:
        v0 = float(lib1685b.getSettings(ser1)[0])
        print("Powering down bpol supplies.")
        stepVolt(ser, v0, 1, t, dt=0.25)
        time.sleep((v0+0.01)/4)
        lib1685b.onOff(ser, 1)
    
def getVoltage1():
    return float(lib1685b.getData(ser1)[0])

def getVoltage2():
    return float(lib1685b.getData(ser2)[0])

def volt(voltage, t=5):
    for ser in sers:
        dt = 0.25
        v1 = float(voltage)
        v0 = float(lib1685b.getSettings(ser)[0])

        print(f"Setting bPOL {sers.index(ser)+1} voltage to {str(v1)}")
        if v1 == 0:
            stepVolt(ser, v0, 1, t, dt)
            time.sleep((v0+0.01) / 6)
            lib1685b.onOff(ser, 1)
            waitUntilVolt(ser, 0)
        elif v1 == v0:
            lib1685b.onOff(ser, 0)
        elif v1 > 12:
            print("bPOL voltage cannot exceed 12V.")
        else:
            lib1685b.onOff(ser, 0)
            stepVolt(ser, v0, v1, t, dt)
            waitUntilVolt(ser, v1)


