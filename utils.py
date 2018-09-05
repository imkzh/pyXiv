import urllib3
import sys
import time
import os
import requests
import io


def get_terminal_size():
    """ getTerminalSize()
     - get width and height of console
     - works on linux,os x,windows,cygwin(windows)
     - https://stackoverflow.com/questions/566746/how-to-get-linux-console-window-width-in-python
    """
    import platform
    current_os = platform.system()
    tuple_xy = None
    if current_os == 'Windows':
        tuple_xy = _get_terminal_size_windows()
        if tuple_xy is None:
            tuple_xy = _get_terminal_size_tput()
            # needed for window's python in cygwin's xterm!
    if current_os == 'Linux' or current_os == 'Darwin' or current_os.startswith('CYGWIN'):
        tuple_xy = _get_terminal_size_linux()
    if tuple_xy is None:
        tuple_xy = (80, 25)      # default value

    return tuple_xy


def _get_terminal_size_windows():
    res = None
    try:
        from ctypes import windll, create_string_buffer

        # stdin handle is -10
        # stdout handle is -11
        # stderr handle is -12

        h = windll.kernel32.GetStdHandle(-12)
        csbi = create_string_buffer(22)
        res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
    except:
        return None
    if res:
        import struct
        (bufx, bufy, curx, cury, wattr,
         left, top, right, bottom, maxx, maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
        sizex = right - left + 1
        sizey = bottom - top + 1
        return sizex, sizey
    else:
        return None


def _get_terminal_size_tput():
    # get terminal width
    # src: http://stackoverflow.com/questions/263890/how-do-i-find-the-width-height-of-a-terminal-window
    try:
        import subprocess
        proc = subprocess.Popen(["tput", "cols"],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
        output = proc.communicate(input=None)
        cols = int(output[0])
        proc = subprocess.Popen(["tput", "lines"],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
        output = proc.communicate(input=None)
        rows = int(output[0])
        return cols, rows
    except:
        return None


def _get_terminal_size_linux():
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct, os
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ,'1234'))
        except:
            return None
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        try:
            cr = (os.environ['LINES'], os.environ['COLUMNS'])
        except KeyError:
            return None
    return int(cr[1]), int(cr[0])


def show_progress_bar(ratio, bytes_per_second=None, bar_indicator_char="#"):
    term_w, _ = get_terminal_size()

    spd = bytes_per_second

    if bar_indicator_char is None or len(bar_indicator_char) < 0:
        bar_indicator_char = "#"

    if term_w < 20:
        percent = "[% 3.2f%%]" % (ratio * 100,)
        print("\r" + "{:>?s}".replace("?", str(term_w)).format(percent), end="")
        pass
    elif term_w < 50:
        percent = "[% 3.2f%%]" % (ratio * 100,)
        ll = len(percent)
        l_prog = (term_w - ll - 2)
        l_done = int(l_prog * ratio + 0.5)
        print("\r[" + bar_indicator_char[0] * l_done + " " * (l_prog - l_done) + "]" + " " * (ll - len(percent)) + percent, end="")
        pass
    else:

        percent = "[% 3.2f%%]" % (ratio * 100,)
        ll = len(" 1,024 kb/s " + percent)
        l_prog = (term_w - ll - 2)
        l_done = int(l_prog * ratio + 0.5)
        if bytes_per_second is not None:
            units = ["B/s", "kB/s", "MB/s", "GB/s", "TB/s", ""]
            unit = 0

            fit = "{0:>5,.?f}"

            while bytes_per_second >= 10000:
                bytes_per_second /= 1024
                unit += 1

            if bytes_per_second >= 1000:
                fit_cnt = 0
            elif bytes_per_second >= 100:
                fit_cnt = 1
            else:
                fit_cnt = 2

            fit = fit.replace("?", str(fit_cnt))

            if unit > 4:
                unit = 5

            foot = "{:>12s}".format(fit.format(bytes_per_second) + " " + units[unit] + " ")
            print("\r[" + bar_indicator_char[0] * l_done + " " * (l_prog - l_done) + "]" + foot + percent, end="")
        else:
            print("\r[" + bar_indicator_char[0] * l_done + " " * (l_prog - l_done) + "]" + " " * (ll - len(percent)) + percent, end="")
        sys.stdout.flush()
        time.sleep(0.001)


def filename_filter(txt):
    txt = txt.replace("/", " ").replace("\t", " ").replace("&nbsp;", " ").replace("\n", " ").replace("\\", " ").replace("?", " ").replace("*", " ").replace(":", ".").replace(";", "_")

    while "  " in txt:
        txt = txt.replace("  ", " ")

    return txt


def download_file(url, filename, user_agent):

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    headers = {'User-Agent': user_agent}

    show_progress_bar(0, bytes_per_second=0)

    last_time = time.time()

    s = requests.Session()
    s.verify = False
    s.stream = True

    req = requests.Request('GET', url, headers=headers)
    req_prep = req.prepare()

    resp_stream = s.send(req_prep)

    if resp_stream.status_code == 200:
        len_total = int(resp_stream.headers["content-length"])
        len_loaded = 0
        f_out = io.open(filename, 'wb')
        for chunk in resp_stream.iter_content(chunk_size=1024*128):
            if chunk:
                t_now = time.time()
                t_diff = (t_now - last_time)
                last_time = t_now
                len_loaded += len(chunk)
                f_out.write(chunk)
                f_out.flush()
                show_progress_bar(len_loaded / len_total, bytes_per_second=len(chunk)/t_diff, bar_indicator_char='=')

        f_out.close()
        # h = Http()
        # resp, content = h.request(url, 'GET', headers=headers)
        print()
