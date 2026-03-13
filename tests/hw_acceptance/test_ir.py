# IR test script
import logging
import subprocess
import os
import sys
import time
from pathlib import Path

up_dir = os.path.dirname(os.path.abspath(__file__)) + '/../../'
sys.path.append(up_dir)

from logging_setup import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

from lcd import LCD
from test_report import update_json

result = False
lcd = LCD()
lcd.set_lcd_present(1)


def get_rc_device_index(keyword):
    """Get RC device index by checking /sys/class/rc/ symlinks for a keyword."""
    rc_dir = Path('/sys/class/rc')
    if rc_dir.exists():
        for rc_device in rc_dir.iterdir():
            if rc_device.is_symlink():
                link_target = str(rc_device.readlink())
                logger.debug("Found RC device: %s -> %s", rc_device.name, link_target)
                if keyword in link_target:
                    logger.info("Found %s device: %s", keyword, rc_device.name)
                    return rc_device.name
    logger.warning("Could not find RC device with keyword: %s", keyword)
    return None


def get_lirc_device(rc_name):
    """Get the /dev/lircN path for a given rc device."""
    lirc_dir = Path('/sys/class/rc') / rc_name
    for child in lirc_dir.iterdir():
        if child.name.startswith('lirc'):
            dev_path = '/dev/' + child.name
            if Path(dev_path).exists():
                logger.info("Found lirc device: %s for %s", dev_path, rc_name)
                return dev_path
    return None


def send_ir_command(r=5, transmitter_dev=None):
    dev_arg = "-d {} ".format(transmitter_dev) if transmitter_dev else ""
    for i in range(r):
        degree = 360 * ((i + 1) / r)
        lcd.progress_wheel("Testing IR ...", degree, "green")
        os.system("sudo ir-ctl {}-S sony12:0x10015".format(dev_arg))
        time.sleep(0.1)
        logger.debug("Sending IR command %d/%d", i + 1, r)


def main():
    lcd.display([(1, "Starting", 0, "white"), (2, "Infrared (IR)", 0, "white"), (3, "Test", 0, "white")], 25)

    # Detect receiver and transmitter by checking /sys/class/rc/ symlinks
    receiver_rc = get_rc_device_index('ir-receiver')
    transmitter_rc = get_rc_device_index('ir-transmitter')

    transmitter_lirc = None
    if transmitter_rc:
        transmitter_lirc = get_lirc_device(transmitter_rc)

    if not receiver_rc:
        logger.warning("Receiver not found via symlink, falling back to probing")
        for i in range(5):
            dev = "rc" + str(i)
            logger.info("Trying IR device: %s", dev)
            p1 = subprocess.Popen('sudo stdbuf -i0 -o0 -e0 ir-keytable -c -p all -t -s ' + dev + ' > test_ir_codes.txt', shell=True)
            time.sleep(1)
            returncode = p1.poll()
            logger.debug("Device %s returncode: %s", dev, returncode)
            if returncode is None:
                break
    else:
        logger.info("Using detected receiver: %s", receiver_rc)
        p1 = subprocess.Popen('sudo stdbuf -i0 -o0 -e0 ir-keytable -c -p all -t -s ' + receiver_rc + ' > test_ir_codes.txt', shell=True)
        time.sleep(1)

    send_ir_command(6, transmitter_lirc)

    logger.debug("Process spawned with PID: %s", p1.pid)
    pgid = os.getpgid(p1.pid)
    try:
        subprocess.check_output("sudo kill {}".format(p1.pid), shell=True)
        subprocess.check_output("sudo kill {}".format(p1.pid + 2), shell=True)
    except Exception:
        pass

    f = open("test_ir_codes.txt", "r")
    if '0x10015' in f.read():
        logger.info("IR test passed")
        lcd.display([(1, "IR Test", 0, "white"), (2, "Result:", 0, "white"), (3, "Passed", 0, "green"), (4, chr(56), 1, "green")], 25)
        result = True
    else:
        logger.info("IR test failed")
        lcd.display([(1, "IR Test", 0, "white"), (2, "Result:", 0, "white"), (3, "Failed", 0, "red"), (4, chr(50), 1, "red")], 25)
        result = False
    f.close()
    summary = {"infrared": {}}
    summary["infrared"]["receiver"] = "tsop75238"
    summary["infrared"]["test_result"] = result
    summary["infrared"]["test_report"] = {"sony12": True}
    update_json(summary)
    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Interrupted")
        sys.exit(0)
