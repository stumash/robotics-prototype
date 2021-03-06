class Microcontroller:
    """Microcontroller or SoaC class acting as a `serial` wrapper.

    This will act as the mother class to represent the Arduino (Microcontroller)
    that will contain other class component objects thanks to the wonders of
    OO composition design patterns.

    """

    def __init__(self, name, serial_port, motors):
        self.name = name
        self.serial_port = serial_port
        self.motors = self.Collection(motors)
        for motor in motors:
            motor.serial_port = serial_port

    class Collection:
        def __init__(self, motors):
            self.elements = motors

        def __iter__(self):
            return iter(self.elements)

        @property
        def elements(self):
            return self.__elements

        @elements.setter
        def elements(self, elements):
            self.__elements = elements

        def get(self, name=None):
            return next((motor for motor in self.elements
                         if motor.name == name))

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name):
        self.__name = name

    @property
    def serial_port(self):
        return self.__serial_port

    @serial_port.setter
    def serial_port(self, serial_port):
        self.__serial_port = serial_port

    @property
    def motors(self):
        return self.__motors

    @motors.setter
    def motors(self, motors):
        self.__motors = motors

    def write(self, name, data):
        for motor in self.motors:
            if motor.name in name:
                print(data)
                motor.write(self.serial_port, data)

    def read(self, name):
        for motor in self.motors:
            if motor.name in name:
                return motor.read(self.serial_port)
