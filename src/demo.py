#!/usr/bin/env python3

import time
import argparse
from pymodbus.client.sync import ModbusTcpClient as ModbusClient


def get_fingertip_offset(client):
    """Reads the current fingertip offset in 1/10 millimeters.
       Please note that the value is a signed two's complement number.
    """
    result = client.read_holding_registers(address=258, count=1, unit=65)
    offset_mm = result.registers[0] / 10.0
    return offset_mm


def get_width(client):
    """Reads the current width between the gripper fingers in 1/10 millimeters.
       Please note that the width is provided without any fingertip offset,
       as it is measured between the insides of the aluminum fingers.
    """
    result = client.read_holding_registers(address=267, count=1, unit=65)
    width_mm = result.registers[0] / 10.0
    return width_mm


def get_status(client):
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
                                can only be reset by power cycling the gripper.
       4:       S2 pushed       High (1) when safety switch 2 is pushed.
       5:       S2 trigged      High (1) when safety circuit 2 is activated.
                                The gripper will not move
                                while this flag is high;
                                can only be reset by power cycling the gripper.
       6:       safety error    High (1) when on power on any of
                                the safety switch is pushed.
       10-16:   reserved        Not used.
    """
    # address   : register number
    # count     : number of registers to be read
    # unit      : slave device address
    result = client.read_holding_registers(address=268, count=1, unit=65)
    status = format(result.registers[0], '016b')
    status_list = [0] * 7
    if int(status[-1]):
        print("Any motion is not ongoing so new commands are accepted.")
        status_list[0] = 1
    elif int(status[-2]):
        print("An internal- or external grip is detected.")
        status_list[1] = 1
    elif int(status[-3]):
        print("Safety switch 1 is pushed.")
        status_list[2] = 1
    elif int(status[-4]):
        print("Safety circuit 1 is activated so the gripper will not move.")
        status_list[3] = 1
    elif int(status[-5]):
        print("Safety switch 2 is pushed.")
        status_list[4] = 1
    elif int(status[-6]):
        print("Safety circuit 2 is activated so the gripper will not move.")
        status_list[5] = 1
    elif int(status[-7]):
        print("Any of the safety switch is pushed.")
        status_list[6] = 1

    return status_list


def get_width_with_offset(client):
    """Reads the current width between the gripper fingers in 1/10 millimeters.
       The set fingertip offset is considered.
    """
    result = client.read_holding_registers(address=275, count=1, unit=65)
    width_mm = result.registers[0] / 10.0
    return width_mm


def easy_control(client, command):
    """The control field is used to start and stop gripper motion.
       Only one option should be set at a time.
       Please note that the gripper will not start a new motion
       before the one currently being executed is done
       (see busy flag in the Status field).
       The valid flags are:

       1 (0x0001):  grip
                    Start the motion, with the preset target force and width.
                    Width is calculated without the fingertip offset.
                    Please note that the gripper will ignore this command
                    if the busy flag is set in the status field.
       8 (0x0008):  stop
                    Stop the current motion.
       16 (0x0010): grip_w_offset
                    Same as grip, but width is calculated
                    with the set fingertip offset.
    """
    result = client.write_register(address=2, value=command, unit=65)


def set_target_force(client, force_val):
    """Writes the target force to be reached
       when gripping and holding a workpiece.
       It must be provided in 1/10th Newtons.
       The valid range is 0 to 400 for the RG2 and 0 to 1200 for the RG6.
    """
    result = client.write_register(address=0, value=force_val, unit=65)
    easy_control(client, 16)


def set_target_width(client, width_val):
    """Writes the target width between
       the finger to be moved to and maintained.
       It must be provided in 1/10th millimeters.
       The valid range is 0 to 1100 for the RG2 and 0 to 1600 for the RG6.
       Please note that the target width should be provided
       corrected for any fingertip offset,
       as it is measured between the insides of the aluminum fingers.
    """
    result = client.write_register(address=1, value=width_val, unit=65)
    easy_control(client, 16)


def run_demo():
    """Runs gripper open-close demonstration once."""
    client = ModbusClient(
        toolchanger_ip,
        port=toolchanger_port,
        stopbits=1,
        bytesize=8,
        parity='E',
        baudrate=115200,
        timeout=1)
    client.connect()

    if get_status(client)[0] == 0:
        print("Current hand opening width: " +
              str(get_width_with_offset(client)) +
              " mm")

        set_target_width(client, 1600)  # fully opened
        time.sleep(1.0)
        set_target_width(client, 0)  # fully closed

    client.close()


def get_options():
    """Returns user-specific options."""
    parser = argparse.ArgumentParser(description='Set options.')
    parser.add_argument(
        '--ip', dest='ip', type=str, default="192.168.1.1",
        help='set ip address')
    parser.add_argument(
        '--port', dest='port', type=str, default="502",
        help='set port number')
    return parser.parse_args()


if __name__ == '__main__':
    args = get_options()
    toolchanger_ip = args.ip
    toolchanger_port = args.port
    run_demo()
