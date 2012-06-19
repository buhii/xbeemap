import time
import sys
import curses
import serial
from collections import defaultdict
from pickle import dump, load
from xbee import ZigBee as XBee


XBEES = {    # series 1
    'COM4': {
        'port': '/dev/tty.usbserial-A40081kE',
        'id': '13A20040492DAD',
        },
    'COM3': {
        'port': '/dev/tty.usbserial-A40081kE',
        'id': '13A20040656815'
        },
    'COM1': {
        'port': '/dev/tty.usbserial-A8004xHh',
        'id': '13A20040492D5E',
        },
}

def split_len(seq, length):
    # See: http://code.activestate.com/recipes/496784
    return [seq[i:i+length] for i in range(0, len(seq), length)]

def convert_id(xbee_id):
    tmp = ""
    for hex_char in split_len("00" + xbee_id, 2):
        tmp += chr(int(hex_char, 16))
    return tmp

def get_frame_until_db(xbee):
    # read frames
    while True:
        try:
            response = coordinator.wait_read_frame()
            if response['command'] == 'DB':
                rssi = calc_rssi(response['parameter'])
                return rssi
        except KeyboardInterrupt:
            break

def calc_rssi(param):
    return -ord(param)

def get_xbee(port):
    def print_data(data):
        print "%s: %s" % (port, repr(data))

    serial_port = serial.Serial(XBEES[port]['port'], 9600)
    xbee = XBee(serial_port)

    xbee.id = XBEES[port]['id']
    return (xbee, serial_port)

def local_blink(xbee):
    for i in range(10):
        LH = '\x05' if i % 2 == 0 else '\x04'
        xbee.send('at', command='D1', parameter=LH)
        time.sleep(0.100)

def remote_blink(xbee_from, xbee_to_id):
    for i in range(10):
        LH = '\x05' if i % 2 == 0 else '\x04'
        xbee_from.send('remote_at',
                       frame='A',
                       command='D1',
                       parameter=LH,
                       dest_addr_long=convert_id(xbee_to_id)
                       )
        time.sleep(0.100)

def get_rssi(xbee_from, xbee_to_id):
    # print "- Get RSSI of %s" % xbee_to_id
    remote_blink(coordinator, xbee_to_id)
    xbee_from.send('at', command='DB')
    return get_frame_until_db(xbee_from)


def endwin(result, f):
    # write to file
    write(result, f)
    # deinitialize curses
    curses.nocbreak()
    curses.echo()
    curses.endwin()
    sys.exit()


def write(d, f):
    dump(d, f)
    f.close()


if __name__ == '__main__':
    # constants
    RADIUS = 5.0
    LENGTH_UNIT = 0.125 / 2
    result = defaultdict(dict)
    MIN_RAD, MAX_RAD = 0.0, 180.0

    coordinator, serial_port = get_xbee('COM4')
    xbee_id = XBEES['COM3']['id']

    # input
    filename = raw_input("Please specify result filename:")
    if not filename:
        print "no filename!"
        sys.exit()
    result_f = open(filename + '.p', 'w')

    # initialize curses
    stdscr = curses.initscr()
    stdscr.nodelay(1)
    curses.cbreak()

    # process
    rad = MIN_RAD
    while rad <= MAX_RAD:
        l = LENGTH_UNIT
        stdscr.addstr(0, 0, "{:>6.1f}[deg]".format(rad).center(20), curses.A_REVERSE)
        stdscr.refresh()
        while l <= RADIUS:
            rssi = get_rssi(coordinator, xbee_id)
            text = "{:>6.1f}[deg] - {:>6.2f}[cm]: {:>4}[dBm] (y/q)".format(rad, l * 100, rssi)
            stdscr.addstr(int(l / LENGTH_UNIT) % 40, 0, text)
            stdscr.refresh()
            c = stdscr.getch()

            if c == ord('y'):
                # add result
                result[rad][l] = rssi
                l += LENGTH_UNIT * 40

            if c == ord('q'):
                stdscr.addstr(1, 0, "quit!", curses.A_REVERSE)
                endwin(result, result_f)

        stdscr.erase()
        rad += 180 / 8.0

    # closing
    coordinator.halt()
    serial_port.close()
    endwin(result, result_f)
