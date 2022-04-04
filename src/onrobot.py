#!/usr/bin/env python3

from pymodbus.client.sync import ModbusTcpClient as ModbusClient


class RG():

    def __init__(self, gripper, ip, port):
        self.client = ModbusClient(
            ip,
            port=port,
            stopbits=1,
            bytesize=8,
            parity='E',
            baudrate=115200,
            timeout=1)
        if gripper not in ['rg2', 'rg6']:
            print("Please specify either rg2 or rg6.")
            return
        self.gripper = gripper  # RG2/6
        if self.gripper == 'rg2':
            self.max_width = 1100
            self.max_force = 400
        elif self.gripper == 'rg6':
            self.max_width = 1600
            self.max_force = 1200
        self.open_connection()

    def open_connection(self):
        """Opens the connection with a gripper."""
        self.client.connect()

    def close_connection(self):
        """Closes the connection with the gripper."""
        self.client.close()

    def get_fingertip_offset(self):
        """Reads the current fingertip offset in 1/10 millimeters.
        Please note that the value is a signed two's complement number.
        """
        result = self.client.read_holding_registers(
            address=258, count=1, unit=65)
        offset_mm = result.registers[0] / 10.0
        return offset_mm

    def get_width(self):
        """Reads current width between gripper fingers in 1/10 millimeters.
        Please note that the width is provided without any fingertip offset,
        as it is measured between the insides of the aluminum fingers.
        """
        result = self.client.read_holding_registers(
            address=267, count=1, unit=65)
        width_mm = result.registers[0] / 10.0
        return width_mm

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
        # address   : register number
        # count     : number of registers to be read
        # unit      : slave device address
        result = self.client.read_holding_registers(
            address=268, count=1, unit=65)
        status = format(result.registers[0], '016b')
        status_list = [0] * 7
        if int(status[-1]):
            print("A motion is ongoing so new commands are not accepted.")
            status_list[0] = 1
        if int(status[-2]):
            print("An internal- or external grip is detected.")
            status_list[1] = 1
        if int(status[-3]):
            print("Safety switch 1 is pushed.")
            status_list[2] = 1
        if int(status[-4]):
            print("Safety circuit 1 is activated so it will not move.")
            status_list[3] = 1
        if int(status[-5]):
            print("Safety switch 2 is pushed.")
            status_list[4] = 1
        if int(status[-6]):
            print("Safety circuit 2 is activated so it will not move.")
            status_list[5] = 1
        if int(status[-7]):
            print("Any of the safety switch is pushed.")
            status_list[6] = 1

        return status_list

    def get_width_with_offset(self):
        """Reads current width between gripper fingers in 1/10 millimeters.
        The set fingertip offset is considered.
        """
        result = self.client.read_holding_registers(
            address=275, count=1, unit=65)
        width_mm = result.registers[0] / 10.0
        return width_mm

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
        result = self.client.write_register(
            address=2, value=command, unit=65)

    def set_target_force(self, force_val):
        """Writes the target force to be reached
        when gripping and holding a workpiece.
        It must be provided in 1/10th Newtons.
        The valid range is 0 to 400 for the RG2 and 0 to 1200 for the RG6.
        """
        result = self.client.write_register(
            address=0, value=force_val, unit=65)

    def set_target_width(self, width_val):
        """Writes the target width between
        the finger to be moved to and maintained.
        It must be provided in 1/10th millimeters.
        The valid range is 0 to 1100 for the RG2 and 0 to 1600 for the RG6.
        Please note that the target width should be provided
        corrected for any fingertip offset,
        as it is measured between the insides of the aluminum fingers.
        """
        result = self.client.write_register(
            address=1, value=width_val, unit=65)

    def close_gripper(self, force_val=400):
        """Closes gripper."""
        params = [force_val, 0, 16]
        print("Start closing gripper.")
        result = self.client.write_registers(
            address=0, values=params, unit=65)

    def open_gripper(self, force_val=400):
        """Opens gripper."""
        params = [force_val, self.max_width, 16]
        print("Start opening gripper.")
        result = self.client.write_registers(
            address=0, values=params, unit=65)

    def move_gripper(self, width_val, force_val=400):
        """Moves gripper to the specified width."""
        params = [force_val, width_val, 16]
        print("Start moving gripper.")
        result = self.client.write_registers(
            address=0, values=params, unit=65)

