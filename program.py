import json, codecontainer, vexbrain, vexunits, prettyemu, vexfunctions, veximplementations, time, random, string, competitionsupport
from vexdevices.vexv5 import virtualaccel2g, virtualaccel6g, virtualbumper, virtualcontroller, virtualdigitalin, virtualdigitalout
from vexdevices.vexv5 import virtualdistance, virtualdrivetrain, virtualencoder, virtualgps, virtualgyro, virtualpotentiometer, virtualpotentiometerv2, virtualrangefinder
from vexdevices.vexv5 import virtualinertial, virtualled, virtuallight, virtuallimitswitch, virtuallinetracker, virtualoptical
from vexdevices.vexv5 import virtualrotation, virtualvision, virtualmotor393, virtualservo, virtualmagnet, virtualmotor, virtualmotorgroup

def getRandomString(length=8) -> str: return ''.join(random.choice(string.ascii_letters) for _ in range(length))

class ProgramFile(object):
    def __init__(self, filename: str):
        self.fileName = filename

        self.programType = filename.split('.')[1].replace('python','')
        print('Type:',self.programType)

        if self.programType == 'v5':
            self.name = self.fileName.split('.v5python')[0]
            if '/' in self.name: self.name = self.name.split('/')[-1]

            self.container = None

            with open(self.fileName, 'r') as f: self.fileData = json.load(f)

            self.deviceMappings = {
                'Controller': virtualcontroller.Controller,
                'Motor': virtualmotor.Motor,
                'Drivetrain': virtualdrivetrain.Drivetrain,
                'Gyro': virtualgyro.Gyro,
                'Distance': virtualdistance.Distance,
                'Magnet': virtualmagnet.Magnet,
                'Rotation': virtualrotation.Rotation,
                'Optical': virtualoptical.Optical,
                'Inertial': virtualinertial.Inertial,
                'Vision': virtualvision.Vision,
                'GPS': virtualgps.Gps,

                'Bumper': virtualbumper.Bumper,
                'LimitSwitch': virtuallimitswitch.LimitSwitch,
                'Encoder': virtualencoder.Encoder,
                'RangeFinder': virtualrangefinder.RangeFinder,
                'LineTracker': virtuallinetracker.LineTracker,
                'Light': virtuallight.Light,
                'Potentiometer': virtualpotentiometer.Potentiometer,
                'PotentiometerV2': virtualpotentiometerv2.PotentiometerV2,
                'Motor393': virtualmotor393.Motor393,
                'Servo': virtualservo.Servo,
                'LED': virtualled.Led,
                'Accel2G': virtualaccel2g.Accel2G,
                'Accel6G': virtualaccel6g.Accel6G,
                'DigitalIn': virtualdigitalin.DigitalIn,
                'DigitalOut': virtualdigitalout.DigitalOut,
            }
    
        elif self.programType == 'iq':
            print('[ProgramFile] Warning IQ programs are not fully supported!')
            self.name = self.fileName.split('.iqpython')[0]
            if '/' in self.name: self.name = self.name.split('/')[-1]

            self.container = None

            with open(self.fileName, 'r') as f: self.fileData = json.load(f)

            self.deviceMappings = {
                'Vision': virtualvision.Vision,
                'Distance': virtualdistance.Distance,
                'Motor': virtualmotor.Motor,
                'Drivetrain': virtualdrivetrain.Drivetrain,
                'Optical': virtualoptical.Optical,
            }

    def reloadContainerCode(self):
        with open(self.fileName, 'r') as f: self.fileData = json.load(f)
        if self.container is not None:
            self.container.code = self.patchTextCode()

    def getTextCode(self) -> str:
        """
        Returns the text code of the program.
        """
        return self.fileData['textContent']
    
    def getUserCode(self) -> str:
        """
        Returns the user code of the program. (anything below #endregion VEXcode)
        """
        if "#endregion VEXcode" not in self.getTextCode():
            return self.getTextCode()#This most likely means that the code was generated before VEX made the auto generated code save to the .v5python file
        return '\n'.join(self.getTextCode().split('\n')[self.getTextCode().strip().split('\n').index('#endregion VEXcode Generated Robot Configuration')+1:]).replace('\nfrom vex import *','')
    
    def patchTextCode(self) -> str:
        """
        Gets the text code ready to run on the emulator.5
        """
        baseCode = self.getUserCode()
        baseCode = baseCode.replace('\n\n','\n')
        with open('linker.py', 'r') as f:
            linker = f.read()

        return linker + baseCode
    
    def loadContainer(self, brainCore: vexbrain.Brain) -> codecontainer.Container:
        # sourcery skip: extract-duplicate-method
        """
        Loads the program into a container.
        """
        NewContainer = codecontainer.Container(self.patchTextCode())

        fileName = self.fileName.split('.v5python')[0]
        if '/' in fileName: fileName = fileName.split('/')[-1]
        brainCore.BrainScreen.programName  = fileName

        brainCore.virtualDevices = []

        NewContainer.set_global('brain', vexbrain.BrainLinker(brainCore.BrainScreen, vexbrain.Battery(), vexbrain.Timer()))
        NewContainer.set_global('print', prettyemu.prettyPrint)
        NewContainer.merge_globals(vexunits.new_globals)
        NewContainer.merge_globals(veximplementations.new_globals)
        NewContainer.merge_globals(vexfunctions.new_globals)

        CompetitionClass = competitionsupport.CompetitionAttributeStore(brainCore)
        NewContainer.set_global('Competition', CompetitionClass.CompetitionUserFunc)
        CompetitionClass._id = getRandomString(16); CompetitionClass._type = 'callback'; CompetitionClass._name = 'Competition_Controller'
        brainCore.virtualDevices.append(CompetitionClass)

        for device in self.fileData['rconfig']:
            if device['deviceType'] in self.deviceMappings:
                print(f'[VexEmulator(Loader)] Found {device["deviceType"]} {device["name"]}')
                deviceRef = self.deviceMappings[device['deviceType']]()
                deviceRef._id   = getRandomString(16)
                deviceRef._type = device['deviceType']
                deviceRef._name = device['name']
                NewContainer.set_global(device['name'], deviceRef)
                brainCore.virtualDevices.append(deviceRef)
            elif device['deviceType'] == 'MotorGroup':
                print(f'[VexEmulator(Loader)] Found {device["deviceType"]} {device["name"]}')
                Motor1, Motor2  = virtualmotor.Motor(), virtualmotor.Motor()
                MotorGroup      = virtualmotorgroup.MotorGroup(Motor1, Motor2)
                Motor1._id      = getRandomString(16); Motor1._type     = 'Motor'; Motor1._name          = f"{device['name']}_motor_a"
                Motor2._id      = getRandomString(16); Motor2._type     = 'Motor'; Motor2._name          = f"{device['name']}_motor_b"
                MotorGroup._id  = getRandomString(16); MotorGroup._type = 'MotorGroup'; MotorGroup._name = device['name']

                NewContainer.set_global(device['name'], MotorGroup); brainCore.virtualDevices.append(MotorGroup)
                NewContainer.set_global(f"{device['name']}_motor_a", Motor1); brainCore.virtualDevices.append(Motor1)
                NewContainer.set_global(f"{device['name']}_motor_b", Motor2); brainCore.virtualDevices.append(Motor2)
            else:
                print(f'[VexEmulator(Loader)] Unknown device type {device["deviceType"]} {device["name"]}')

        brainCore.BrainScreen.startTime = time.time()

        self.container = NewContainer
        return NewContainer
