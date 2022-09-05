import clr

from System import String
from System.Collections import *
from System import String, Char, Int32
clr.AddReference('D:\Documents\imp\project\\birdPower\BirdSensor.dll')
from BirdSensor import Bird_5010HID

device = Bird_5010HID()
device.FindDevice('1422', '5014')
