#!/usr/bin/env python3

import time
import argparse

from onrobot import RG6


def run_demo():
    """Runs gripper open-close demonstration once."""
    rg6 = RG6(toolchanger_ip, toolchanger_port)

    if not rg6.get_status()[0]:  # not busy
        print("Current hand opening width: " +
              str(rg6.get_width_with_offset()) +
              " mm")

        rg6.open_gripper()     # fully opened
        while True:
            time.sleep(0.5)
            if not rg6.get_status()[0]:
                break
        rg6.close_gripper()    # fully closed
        while True:
            time.sleep(0.5)
            if not rg6.get_status()[0]:
                break
        rg6.move_gripper(800)  # move to middle point
        while True:
            time.sleep(0.5)
            if not rg6.get_status()[0]:
                break

    rg6.close_connection()


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
