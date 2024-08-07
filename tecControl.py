import serial
import serial.tools.list_ports
import sys
import time
import lib1685b

#ser = serial.Serial("/dev/ttyUSB0") #Note that this uses the same port as the ALDOs.
# This has to be fixed before trying to control both simultaneously.
#ser.timeout = 0.1

def find_TEC(vidTarget, pidTarget):
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
                ser.timeout=0.1
                vMax = lib1685b.getMaxVoltCurr(ser)[0]
                if vMax >= 25:
                    return ser
                else:
                    ser.close()
    raise Exception("Could not find TEC PS")

vidTarget = 0x10c4
pidTarget = 0xea60
ser = find_TEC(vidTarget, pidTarget)
ser.timeout = 0.1
#print(lib1685b.getMaxVoltCurr(ser))

def occupiedPort():
    name = ser.name
    return name

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

def getVoltage():
    return float(lib1685b.getData(ser)[0])

def onOff(ser, on, t=5): #on == True for turning supply on, False for turning off
    v0 = float(lib1685b.getData(ser)[0])
    isOn = False if lib1685b.getData(ser)[0] == 0 else True
    if (on and isOn) or (not on and not isOn):
        #already in desired state
        time.sleep(0.01)
    elif (on and not isOn):
        print("Powering on TECs")
        lib1685b.setVoltage(ser, 0)
        lib1685b.onOff(ser, 0)
        stepVolt(ser, 0, v0, t, dt=0.25)
        waitUntilVolt(ser, v0)
    elif (not on and isOn):
        print("Powering down TECs")
        stepVolt(ser, v0, 0, t, dt=0.25)
        waitUntilVolt(ser, 1)
        lib1685b.onOff(ser, 1)
        waitUntilVolt(ser, 0)

def volt(voltage, t=5):
    args = sys.argv
    dt = 0.25
    v1 = float(voltage)
    v0 = float(lib1685b.getData(ser)[0])
    print("Setting TEC voltage to " + str(v1))
    if v1 == 0:
        stepVolt(ser, v0, 1, t, dt)
        time.sleep((v0+0.01) / 6)
        lib1685b.onOff(ser, 1)
        waitUntilVolt(ser, v1)
    elif v1 == v0:
        lib1685b.onOff(ser, 0)
    elif v1 > 32:
        print("TEC voltage cannot exceed 32V.")
    else:
        lib1685b.onOff(ser, 0)
        stepVolt(ser, v0, v1, t, dt)
        waitUntilVolt(ser, v1)
