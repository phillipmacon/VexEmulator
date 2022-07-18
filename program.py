import json, codecontainer, vexbrain, vexunits, prettyemu, vexfunctions, veximplementations, vexcontroller, time
from vexdevices import virtualmotor, virtualdrivetrain, virtualgyro

class ProgramFile(object):
    def __init__(self, filename: str):
        self.fileName = filename

        self.name = self.fileName.split('.v5python')[0]
        if '/' in self.name: self.name = self.name.split('/')[-1]

        with open(self.fileName, 'r') as f: self.fileData = json.load(f)
    
    def getTextCode(self) -> str:
        """
        Returns the text code of the program.
        """
        return self.fileData['textContent']
    
    def getUserCode(self) -> str:
        """
        Returns the user code of the program. (anything below #endregion VEXcode)
        """
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
    
    def loadContainer(self, brainCore: vexbrain.Brain, controllerServer: vexcontroller.ControllerServer) -> codecontainer.Container:
        """
        Loads the program into a container.
        """
        NewContainer = codecontainer.Container(self.patchTextCode())

        fileName = self.fileName.split('.v5python')[0]
        if '/' in fileName: fileName = fileName.split('/')[-1]
        brainCore.BrainScreen.programName  = fileName


        NewContainer.set_global('brain', vexbrain.BrainLinker(brainCore.BrainScreen, vexbrain.Battery(), vexbrain.Timer()))
        NewContainer.set_global('print', prettyemu.prettyPrint)
        NewContainer.merge_globals(vexunits.new_globals)
        NewContainer.merge_globals(veximplementations.new_globals)
        NewContainer.merge_globals(vexfunctions.new_globals)

        for device in self.fileData['rconfig']:
            if device['deviceType'] == 'Controller':
                controllerCore = vexcontroller.Controller()
                controllerServer.set_controller(controllerCore)
                NewContainer.set_global(device['name'], controllerCore)
                print(f'[VexEmulator(Loader)] Found controller {device["name"]}')
            elif device['deviceType'] == 'Motor':
                brainCore.usedPorts.append(device['port'][0])
                motorName = device['name']
                NewContainer.set_global(motorName, virtualmotor.Motor())
                print(f'[VexEmulator(Loader)] Found motor {motorName}')
            elif device['deviceType'] == 'Drivetrain':
                brainCore.usedPorts.extend(device['port'])
                NewContainer.set_global(device['name'], virtualdrivetrain.Drivetrain())
                print(f'[VexEmulator(Loader)] Found drivetrain {device["name"]}')
            elif device['deviceType'] == 'Gyro':
                brainCore.usedPorts.append(device['port'][0])
                NewContainer.set_global(device['name'], virtualgyro.Gyro())
                print(f'[VexEmulator(Loader)] Found gyro {device["name"]}')

            else:
                print(f'[VexEmulator(Loader)] Unknown device type {device["deviceType"]}')

        brainCore.BrainScreen.startTime = time.time()

        return NewContainer