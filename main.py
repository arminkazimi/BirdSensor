import clr


clr.AddReference('D:\Documents\imp\project\\birdPower\BirdSensor.dll')
from BirdSensor import Bird_5010HID

device = Bird_5010HID()
device.FindDevice('1422', '5014')
