#!/usr/bin/env python3

from pymodbus.client.sync import ModbusTcpClient as ModbusClient

UNIT = 65  # Modbus slave address for OnRobot Compute Box

_GRIPPER_SPECS = {
    'rg2': {'max_width': 1100, 'max_force': 400},
    'rg6': {'max_width': 1600, 'max_force': 1200},
}


class RG():

    def __init__(self, gripper, ip, port):
        if gripper not in _GRIPPER_SPECS:
            raise ValueError(
                "gripper must be 'rg2' or 'rg6', got: {}".format(gripper))
        self.gripper = gripper
        self.max_width = _GRIPPER_SPECS[gripper]['max_width']
        self.max_force = _GRIPPER_SPECS[gripper]['max_force']
        self.client = ModbusClient(ip, port=port, timeout=1)
        self.open_connection()

    def open_connection(self):
        """Opens the connection with a gripper."""
        if not self.client.connect():
            raise ConnectionError(
                "Failed to connect to gripper at {}:{}".format(
                    self.client.host, self.client.port))

    def close_connection(self):
        """Closes the connection with the gripper."""
        self.client.close()

    def _read_register(self, address):
        """Reads a single holding register and returns its raw value."""
        result = self.client.read_holding_registers(
            address=address, count=1, unit=UNIT)
        if result.isError():
            raise IOError(
                "Failed to read register {}: {}".format(address, result))
        return result.registers[0]

    def get_fingertip_offset(self):
        """Reads the current fingertip offset in 1/10 millimeters.
        Please note that the value is a signed two's complement number.
        """
        value = self._read_register(258)
        if value >= 0x8000:  # convert unsigned 16-bit to signed
            value -= 0x10000
        return value / 10.0

    def get_width(self):
        """Reads current width between gripper fingers in 1/10 millimeters.
        Please note that the width is provided without any fingertip offset,
        as it is measured between the insides of the aluminum fingers.
        """
        return self._read_register(267) / 10.0

    def is_busy(self):
        """Returns True when a motion is ongoing, False otherwise.
        Use this method for polling loops to avoid printing status messages
        on every check.
        """
        return bool(self._read_register(268) & 1)

    def get_status(self):
        """Reads current device status.
        This status field indicates the status of the gripper and its motion.
        It is composed of 7 flags, described in the table below.

        Bit      Name            Description
        0 (LSB): busy            High (1) when a motion is ongoing,
                                  low (0) when not.
                                  The gripper will only accept new commands
                                  when this flag is low.
        1:       grip detected   High (1) when an internal- or
                                  external grip is detected.
        2:       S1 pushed       High (1) when safety switch 1 is pushed.
        3:       S1 trigged      High (1) when safety circuit 1 is activated.
                                  The gripper will not move
                                  while this flag is high;
                                  can only be reset by power cycling.
        4:       S2 pushed       High (1) when safety switch 2 is pushed.
        5:       S2 trigged      High (1) when safety circuit 2 is activated.
                                  The gripper will not move
                                  while this flag is high;
                                  can only be reset by power cycling.
        6:       safety error    High (1) when on power on any of
                                  the safety switch is pushed.
        10-16:   reserved        Not used.
        """
        value = self._read_register(268)

        _messages = [
            "A motion is ongoing so new commands are not accepted.",
            "An internal- or external grip is detected.",
            "Safety switch 1 is pushed.",
            "Safety circuit 1 is activated so it will not move.",
            "Safety switch 2 is pushed.",
            "Safety circuit 2 is activated so it will not move.",
            "Any of the safety switch is pushed.",
        ]

        status_list = [0] * 7
        for i in range(7):
            if (value >> i) & 1:
                print(_messages[i])
                status_list[i] = 1
        return status_list

    def get_width_with_offset(self):
        """Reads current width between gripper fingers in 1/10 millimeters.
        The set fingertip offset is considered.
        """
        return self._read_register(275) / 10.0

    def set_control_mode(self, command):
        """The control field is used to start and stop gripper motion.
        Only one option should be set at a time.
        Please note that the gripper will not start a new motion
        before the one currently being executed is done
        (see busy flag in the Status field).
        The valid flags are:

        1 (0x0001):  grip
                      Start the motion, with the target force and width.
                      Width is calculated without the fingertip offset.
                      Please note that the gripper will ignore this command
                      if the busy flag is set in the status field.
        8 (0x0008):  stop
                      Stop the current motion.
        16 (0x0010): grip_w_offset
                      Same as grip, but width is calculated
                      with the set fingertip offset.
        """
        self.client.write_register(address=2, value=command, unit=UNIT)

    def set_target_force(self, force_val):
        """Writes the target force to be reached
        when gripping and holding a workpiece.
        It must be provided in 1/10th Newtons.
        The valid range is 0 to 400 for the RG2 and 0 to 1200 for the RG6.
        """
        self.client.write_register(address=0, value=force_val, unit=UNIT)

    def set_target_width(self, width_val):
        """Writes the target width between
        the finger to be moved to and maintained.
        It must be provided in 1/10th millimeters.
        The valid range is 0 to 1100 for the RG2 and 0 to 1600 for the RG6.
        Please note that the target width should be provided
        corrected for any fingertip offset,
        as it is measured between the insides of the aluminum fingers.
        """
        self.client.write_register(address=1, value=width_val, unit=UNIT)

    def close_gripper(self, force_val=400):
        """Closes gripper."""
        print("Start closing gripper.")
        self.client.write_registers(
            address=0, values=[force_val, 0, 16], unit=UNIT)

    def open_gripper(self, force_val=400):
        """Opens gripper."""
        print("Start opening gripper.")
        self.client.write_registers(
            address=0, values=[force_val, self.max_width, 16], unit=UNIT)

    def move_gripper(self, width_val, force_val=400):
        """Moves gripper to the specified width."""
        print("Start moving gripper.")
        self.client.write_registers(
            address=0, values=[force_val, width_val, 16], unit=UNIT)
