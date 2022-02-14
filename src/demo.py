#!/usr/bin/env python3

from bitstring import Bits
from pymodbus.client.sync import ModbusTcpClient as ModbusClient


def get_status(client):
    """Reads current device status.
       This status field indicates the status of the gripper and its motion.
       It is composed of 7 flags, described in the table below.

       0: busy
       1: grip detected
       2: S1 pushed
       3: S1 trigged
       4: S2 pushed
       5: S2 trigged
       6: safety error
    """
    # address   : register number
    # count     : number of registers to be read
    # unit      : slave device address
    result = client.read_holding_registers(address=268, count=1, unit=65)
    status = result.registers[0]
    return status


def get_fingertip_offset(client):
    """Reads the current fingertip offset in 1/10 millimeters. 
       Please note that the value is a signed two's complement number.
    """
    result = client.read_holding_registers(address=258, count=1, unit=65)
    print(result.registers[0])
    offset_mm = Bits(bin=str(result.registers[0])).int
    return offset_mm


def get_width(client):
    """Reads the current width between the gripper fingers in 1/10 millimeters.
       Please note that the width is provided without any fingertip offset,
       as it is measured between the insides of the aluminum fingers.
    """
    offset = 100
    result = client.read_holding_registers(address=267, count=1, unit=65)
    width_mm = result.registers[0] - offset
    return width_mm


def get_width_with_offset(client):
    """Reads the current width between the gripper fingers in 1/10 millimeters.
       The set fingertip offset is considered.
    """
    result = client.read_holding_registers(address=275, count=1, unit=65)
    width_mm = result.registers[0]
    return width_mm


def easy_control(client, command):
    """The control field is used to start and stop gripper motion.
       Only one option should be set at a time.
       Please note that the gripper will not start a new motion
       before the one currently being executed is done (see busy flag in the Status field).
       The valid flags are:

       1: grip, Start the motion, with the preset target force and width.
                Width is calculated without the fingertip offset.
                Please note that the gripper will ignore this command
                if the busy flag is set in the status field.
       8: stop, Stop the current motion.
       16: grip_w_offset, Same as grip, but width is calculated with the set fingertip offset.
    """
    result = client.write_register(address=2, value=command, unit=65)


def set_target_force(client, force_val):
    """Writes the target force to be reached when gripping and holding a workpiece.
       It must be provided in 1/10th Newtons.
       The valid range is 0 to 400 for the RG2 and 0 to 1200 for the RG6.
    """
    result = client.write_register(address=0, value=force_val, unit=65)
    easy_control(client, 16)


def set_target_width(client, width_val):
    """Writes the target width between the finger to be moved to and maintained.
       It must be provided in 1/10th millimeters.
       The valid range is 0 to 1100 for the RG2 and 0 to 1600 for the RG6.
       Please note that the target width should be provided corrected for any fingertip offset,
       as it is measured between the insides of the aluminum fingers.
    """
    result = client.write_register(address=1, value=width_val, unit=65)
    easy_control(client, 16)


def run_demo():
    client = ModbusClient(
        toolchanger_ip,
        port=toolchanger_port,
        stopbits=1,
        bytesize=8,
        parity='E',
        baudrate=115200,
        timeout=1)
    client.connect()
    print(get_status(client))
    #print(get_fingertip_offset(client))
    print(get_width(client))
    print(get_width_with_offset(client))
    #set_target_force(client, 1600)
    set_target_width(client, 1000)
    client.close()


if __name__ == '__main__':
    toolchanger_ip = "192.168.1.1"
    toolchanger_port = "502"
    run_demo()
