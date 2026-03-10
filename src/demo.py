#!/usr/bin/env python3

import time
import argparse

from onrobot import RG

BUSY_POLL_INTERVAL = 0.5  # seconds
BUSY_TIMEOUT = 30.0       # seconds


def wait_until_not_busy(rg):
    """Polls the busy flag until the gripper finishes its motion or times out."""
    elapsed = 0.0
    while rg.is_busy():
        time.sleep(BUSY_POLL_INTERVAL)
        elapsed += BUSY_POLL_INTERVAL
        if elapsed >= BUSY_TIMEOUT:
            print("Timeout waiting for gripper to finish.")
            break


def run_demo(gripper, ip, port):
    """Runs gripper open-close demonstration once."""
    rg = RG(gripper, ip, port)
    try:
        if rg.is_busy():
            print("Gripper is busy; skipping demo.")
            return
        print("Current hand opening width: {} mm".format(
            rg.get_width_with_offset()))

        rg.open_gripper()
        wait_until_not_busy(rg)
        rg.close_gripper()
        wait_until_not_busy(rg)
        rg.move_gripper(800)
        wait_until_not_busy(rg)
    finally:
        rg.close_connection()


def get_options():
    """Returns user-specific options."""
    parser = argparse.ArgumentParser(description='Set options.')
    parser.add_argument(
        '--gripper', dest='gripper', type=str,
        default="rg6", choices=['rg2', 'rg6'],
        help='set gripper type, rg2 or rg6')
    parser.add_argument(
        '--ip', dest='ip', type=str, default="192.168.1.1",
        help='set ip address')
    parser.add_argument(
        '--port', dest='port', type=int, default=502,
        help='set port number')
    return parser.parse_args()


if __name__ == '__main__':
    args = get_options()
    run_demo(args.gripper, args.ip, args.port)
