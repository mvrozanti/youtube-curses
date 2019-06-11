#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function)

from subprocess import Popen, PIPE
from queue import Queue
import threading
import logging
import termios
import struct
import errno
import fcntl
import code
import sys
import os

W3MIMGDISPLAY_ENV = "W3MIMGDISPLAY_PATH"
W3MIMGDISPLAY_OPTIONS = []
W3MIMGDISPLAY_PATHS = [
    '/usr/lib/w3m/w3mimgdisplay',
    '/usr/libexec/w3m/w3mimgdisplay',
    '/usr/lib64/w3m/w3mimgdisplay',
    '/usr/libexec64/w3m/w3mimgdisplay',
    '/usr/local/libexec/w3m/w3mimgdisplay',
]

log = logging.getLogger()
log.setLevel(logging.FATAL)
log.propagate = True

class ImageDisplayError(Exception):
    pass


class ImgDisplayUnsupportedException(Exception):
    pass


class ImageDisplayer(object):
    """Image display provider functions for drawing images in the terminal"""

    def draw(self, path, start_x, start_y, width, height):
        """Draw an image at the given coordinates."""
        pass

    def clear(self, start_x, start_y, width, height):
        """Clear a part of terminal display."""
        pass

    def quit(self):
        """Cleanup and close"""
        pass


class W3MImageDisplayer(ImageDisplayer, threading.Thread):
    """Implementation of ImageDisplayer using w3mimgdisplay, an utilitary
    program from w3m (a text-based web browser). w3mimgdisplay can display
    images either in virtual tty (using linux framebuffer) or in a Xorg session.
    Does not work over ssh.

    w3m need to be installed for this to work.
    """
    is_initialized = False

    def __init__(self):
        self.binary_path = None
        self.process = None
        self.x = 1
        self.y = 1
        self.w = 1
        self.h = 1
        self.stop_event = threading.Event()
        self.path_queue = Queue()
        threading.Thread.__init__(self,daemon=True)

    def initialize(self):
        """start w3mimgdisplay"""
        self.binary_path = None
        self.binary_path = self._find_w3mimgdisplay_executable()  # may crash
        self.process = Popen([self.binary_path] + W3MIMGDISPLAY_OPTIONS, stdin=PIPE, stdout=PIPE, universal_newlines=True)
        self.is_initialized = False

    def set_params(self,path,x,y,w,h):
        self.path_queue.put(path)
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def pause(self):
        self.stop_event.set()

    def run(self):
        from time import sleep
        sleep(0.18)
        if not self.is_initialized or self.process.poll() is not None: self.initialize()
        if self.path_queue.qsize() == 2: self.path_queue.get()
        path = self.path_queue.get()
        self.draw(path, self.x, self.y, self.w, self.h)


    @staticmethod
    def _find_w3mimgdisplay_executable():
        paths = [os.environ.get(W3MIMGDISPLAY_ENV, None)] + W3MIMGDISPLAY_PATHS
        for path in paths:
            if path is not None and os.path.exists(path):
                return path
        log.error(ImageDisplayError("No w3mimgdisplay executable found.  Please set "
                                "the path manually by setting the %s environment variable.  (see "
                                "man page)" % W3MIMGDISPLAY_ENV))

    def _get_font_dimensions(self):
        # Get the height and width of a character displayed in the terminal in
        # pixels.
        if self.binary_path is None:
            self.binary_path = self._find_w3mimgdisplay_executable()
        farg = struct.pack("HHHH", 0, 0, 0, 0)
        fd_stdout = sys.stdout.fileno()
        fretint = fcntl.ioctl(fd_stdout, termios.TIOCGWINSZ, farg)
        rows, cols, xpixels, ypixels = struct.unpack("HHHH", fretint)
        if xpixels == 0 and ypixels == 0:
            process = Popen([self.binary_path, "-test"], stdout=PIPE, universal_newlines=True)
            output, _ = process.communicate()
            output = output.split()
            xpixels, ypixels = int(output[0]), int(output[1])
            # adjust for misplacement
            xpixels += 2
            ypixels += 2
        return (xpixels // cols), (ypixels // rows)

    def draw(self, path, start_x, start_y, width, height):
        if self.is_initialized: return 
        self.is_initialized = True
        if self.process.poll() is not None: self.initialize()
        try:
            input_gen = self._generate_w3m_input(path, start_x, start_y, width, height)
            if input_gen:
                self.process.stdin.write(input_gen)
                self.process.stdin.flush()
                self.process.stdout.readline()
        except ImageDisplayError as e: log.exception(e)
        finally:
            self.quit()
            self.is_initialized = False

    def clear(self, start_x, start_y, width, height):
        if not self.is_initialized or self.process.poll() is not None:
            self.initialize()

        fontw, fonth = self._get_font_dimensions()

        cmd = "6;{x};{y};{w};{h}\n4;\n3;\n".format(
            x=int((start_x - 0.2) * fontw),
            y=start_y * fonth,
            # y = int((start_y + 1) * fonth), # (for tmux top status bar)
            w=int((width + 0.4) * fontw),
            h=height * fonth + 1,
            # h = (height - 1) * fonth + 1, # (for tmux top status bar)
        )

        try:
            self.process.stdin.write(cmd)
        except IOError as ex:
            if ex.errno == errno.EPIPE: return
            raise
        self.process.stdin.flush()
        self.process.stdout.readline()

    def _generate_w3m_input(self, path, start_x, start_y, max_width, max_height):
        """Prepare the input string for w3mimgpreview

        start_x, start_y, max_height and max_width specify the drawing area.
        They are expressed in number of characters.
        """
        fontw, fonth = self._get_font_dimensions()
        if fontw == 0 or fonth == 0:
            raise ImgDisplayUnsupportedException

        max_width_pixels = max_width * fontw
        max_height_pixels = max_height * fonth - 2
        # (for tmux top status bar)
        # max_height_pixels = (max_height - 1) * fonth - 2

        # get image size
        cmd = "5;{}\n".format(path)

        try:
            self.process.stdin.write(cmd)
            self.process.stdin.flush()
        except Exception:
            log.error(ImageDisplayError('Failed to execute w3mimgdisplay on', cmd))
            return 
        output = self.process.stdout.readline().split()

        if len(output) != 2:
            log.error(ImageDisplayError('Failed to execute w3mimgdisplay', output, 'for', path, cmd))
            return ""

        width = int(output[0])
        height = int(output[1])

        # get the maximum image size preserving ratio
        if width > max_width_pixels:
            height = (height * max_width_pixels) // width
            width = max_width_pixels
        if height > max_height_pixels:
            width = (width * max_height_pixels) // height
            height = max_height_pixels

        return "0;1;{x};{y};{w};{h};;;;;{filename}\n4;\n3;\n".format(
            x=int((start_x - 0.2) * fontw),
            y=start_y * fonth,
            # y = (start_y + 1) * fonth, # (for tmux top status bar)
            w=width,
            h=height,
            filename=path,
        )

    def quit(self):
        if self.is_initialized and self.process and self.process.poll() is None:
            self.process.kill()
