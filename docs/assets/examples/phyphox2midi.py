#MIDI configuration
M_OUTPUT = "Midi Through:Midi Through Port-0 14:0"
M_CHANNEL = 0
#M_CONTROLS = [1, 2, 3] #You can send on different CC channels
M_CONTROLS = [70]

#phyphox configuration
PP_ADDRESS = "http://192.168.2.100:8080"
#PP_CHANNELS = ["accX", "accY", "accZ"] #If using different CC channels, define multiple phyphox buffers
PP_CHANNELS = ["accY"]

import mido
import requests
import time

#Function used to map raw acceleration values to MIDI values 0..127
def map(v):
    try:
        cv = round((v+5.)*10)
    except:
        return 0
    if cv > 127:
        cv = 127
    if cv < 0:
        cv = 0
    return cv

#Different mapping for pitch wheel
def mapPitch(v):
    try:
        cv = round(v*1000)
    except:
        return 0
    if cv > 8191:
        cv = 8191
    if cv < -8192:
        cv = -8192
    return cv

try:
    output = mido.open_output(M_OUTPUT)
except:
    print("Could not open output. Available outputs:")
    print(mido.get_output_names())

while True:
    url = PP_ADDRESS + "/get?" + ("&".join(PP_CHANNELS))
    data = requests.get(url=url).json()
    for i, control in enumerate(M_CONTROLS):

        #Uncomment to send CC messages
        value = map(data["buffer"][PP_CHANNELS[i]]["buffer"][0])
        print("Sending CC channel " + str(M_CHANNEL) + ", control " + str(control) + ", value " + str(value))
        output.send(mido.Message("control_change", channel=M_CHANNEL, control=control, value=value))

        #Uncomment to send pitch bend
        #value = mapPitch(data["buffer"][PP_CHANNELS[i]]["buffer"][0])
        #print("Sending pitchwheel channel " + str(M_CHANNEL) + ", value " + str(value))
        #output.send(mido.Message("pitchwheel", channel=M_CHANNEL, pitch=value))

        #Uncomment to send notes
        #value = map(data["buffer"][PP_CHANNELS[i]]["buffer"][0])
        #print("Sending note on channel " + str(M_CHANNEL) + ", note " + str(value))
        #output.send(mido.Message("note_on", channel=M_CHANNEL, note=value))
        #time.sleep(0.2)
        #output.send(mido.Message("note_off", channel=M_CHANNEL, note=value))
