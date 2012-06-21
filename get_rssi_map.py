import time
import sys
import curses
import serial
from collections import defaultdict
from pickle import dump
from xbee import XBee
import pygame


XBEES = {    # series 1
    'COM3': {
        'port': '/dev/tty.usbserial-A40081kE',
        'id': '13A20040492DAD',
        },
    'COM4': {
        'port': '/dev/tty.usbserial-A40081CZ',
        'id': '13A20040656815'
        },
    'COM1': {
        'port': '/dev/tty.usbserial-A800f91z',
        'id': '13A20040492D5E',
        },
    'COM5': {  # whip anntena
        'port': '/dev/tty.usbserial-A8004xHh',
        'id': '13A200406E7495',
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

def get_frame_until_rx_io_data(xbee):
    # read frames
    while True:
        try:
            response = coordinator.wait_read_frame()
            return (calc_rssi(response['rssi']),
                    map(lambda d: d['dio-1'], response['samples']))
        except KeyboardInterrupt:
            endwin()

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

def endwin(result=None, f=None):
    if result and f:
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

    # initialize xbee and pygame.mixer
    coordinator, serial_port = get_xbee('COM1')
    xbee_id = XBEES['COM4']['id']
    pygame.mixer.init(44100, -16, 2, 4096)
    sound = pygame.mixer.Sound('bell.wav')

    # prepare result file
    filename = raw_input("Please specify result filename:")
    if not filename:
        print "empty filename!"
        sys.exit()
    result_f = open(filename + '.p', 'w')

    # initialize curses
    stdscr = curses.initscr()
    stdscr.nodelay(1)
    curses.cbreak()

    # process
    button_pushed_old = False
    rad = MIN_RAD
    while rad <= MAX_RAD:
        l = LENGTH_UNIT
        stdscr.addstr(0, 0, "{:>6.1f}[deg]".format(rad).center(20), curses.A_REVERSE)
        stdscr.refresh()
        while l <= RADIUS:
            button_pushed = False
            rssi, dio1s = get_frame_until_rx_io_data(coordinator)
            text = "{:>6.1f}[deg] - {:>6.2f}[cm]: {:>4}[dBm] (y/b/q)".format(rad, l * 100, rssi)

            if len(filter(lambda f: not f, dio1s)) > 0:
                if not button_pushed_old:
                    button_pushed = True
                    button_pushed_old = True
                    sound.play()
                    if l in range(1, 6):
                        time.sleep(0.3)
                        sound.play()
            else:
                button_pushed_old = False
            time.sleep(0.1)

            stdscr.addstr(int(l / LENGTH_UNIT) % 40, 0, text)
            stdscr.refresh()
            c = stdscr.getch()

            if c == ord('y') or button_pushed:
                # add result
                result[rad][l] = rssi
                l += LENGTH_UNIT

            elif c == ord('b'):
                # measure again
                l -= LENGTH_UNIT

            elif c == ord('q'):
                stdscr.addstr(1, 0, "quit!", curses.A_REVERSE)
                endwin(result, result_f)

        stdscr.erase()
        rad += 180 / 8.0

    # closing
    coordinator.halt()
    serial_port.close()
    endwin(result, result_f)
