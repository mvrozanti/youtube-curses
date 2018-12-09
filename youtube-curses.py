#!/usr/bin/env python
import curses, json, pycurl, subprocess, textwrap, urllib.parse
import os
from io import BytesIO
from query import *
import itertools
import threading
import code
import argparse
import sys
import logging
from img_display import W3MImageDisplayer

log = logging.getLogger()

def init_display(stdscr):
    global maxlen
    global win_l
    global win_r
    global maxitems
    stdscr.clear()
    size = stdscr.getmaxyx()
    stdscr.addstr(size[0]//2-1, size[1]//2-5, "Loading...")
    stdscr.move(0,0)
    stdscr.refresh()
    maxlen = size[1] // 2 - 4
    maxitems = size[0] // 2 - 1
    win_l = curses.newwin(size[0], size[1] // 2, 0, 0)
    win_r = curses.newwin(size[0], size[1] // 2, 0, size[1] // 2)
    return size

def main(args):
    # todo: parse args
    w3mid = W3MImageDisplayer()
    w3mid.start()
    highlight = 0
    page = 0
    hl_cache = 0
    p_cache = 0
    state = "top"
    q = ["best", "720p", "480p", "360p", "worst", "audio_only"]
    quality = 0
    key = 0
    donothing = False

    # init curses stuff
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(1)
    curses.curs_set(0)

    try:
        windowsize = init_display(stdscr)
        data = get_front_page(args.channel_count, args.video_count)
        cache = data
        while key != ord('q') and key != ord('Q'):
            if windowsize[0] < 10 or windowsize[1] < 32:
                stdscr.clear()
                stdscr.addstr(0,0,"Terminal")
                stdscr.addstr(1,0,"too small")
            elif donothing == True: donothing = False
            else:
                win_l.erase()
                win_l.border(0)
                win_r.erase()
                win_r.border(0)
#                 win_r.addstr(windowsize[0]-5, windowsize[1]//2-20, "open in browser: o") # to be implemented
                win_r.addstr(windowsize[0]-4, windowsize[1]//2-11, "search: s")
                win_r.addstr(windowsize[0]-3, windowsize[1]//2-11, "refresh: r")
                win_r.addstr(windowsize[0]-1, windowsize[1]//2-9,  "quit: q")
                win_l.addstr(windowsize[0]-1, windowsize[1]//2-9,  "page: "+str(page+1))
                index = 0
                if state == "top":
                    totalitems = len(data)
                    currentpage = list(data.keys())[maxitems*page:maxitems*(page+1)]
                    try:
                        for channel_title in currentpage:
                            if index < maxitems:
                                if index == highlight:
                                    win_l.addnstr(index*2+2, 2, channel_title, maxlen, curses.A_REVERSE)
                                    vids = data[channel_title]
                                    for v_ix,v in enumerate(vids):
                                        vid_link = v['lnk']
                                        vid_title = v['ttl']
                                        win_r.addnstr(v_ix*2+2, 2, vid_title, maxlen)
                                else: win_l.addnstr(index*2+2, 2, channel_title, maxlen)
                            index += 1
                    except Exception as e: log.exception(e)
                if state == "search":
                    currentpage_vids = data[list(data)[hl_cache]]
                    totalitems = len(currentpage_vids)
                    for v_ix,vid in enumerate(currentpage_vids):
                        vid_title = vid['ttl']
                        vid_link = vid['lnk']
                        tf = vid['tf']
                        if index < maxitems:
                            if index == highlight:
                                w3mid.quit()
                                w3mid = W3MImageDisplayer()
#                                 w3mid.path_queue.put(tf)
                                w3mid.set_params(tf, windowsize[1] - 60, 1, 999, 999)
                                w3mid.start()
                                win_l.addnstr(index*2+2, 2, vid_title, maxlen, curses.A_REVERSE)
                                win_r.addnstr(20, 2, 'something will appear here!', maxlen)
                            else: win_l.addnstr(index*2+2, 2, vid_title, maxlen)
                        index += 1
                win_l.refresh()
                win_r.refresh()
            key = stdscr.getch()

            if key == curses.KEY_DOWN or key == ord('j'):
                if highlight + page * maxitems + 1 < totalitems:
                    if highlight + 1 == maxitems:
                        page += 1
                        highlight = 0
                    else: highlight += 1

            elif key == curses.KEY_UP or key == ord('k'):
                if highlight == 0 and page > 0:
                    page -= 1
                    highlight = maxitems - 1
                elif highlight > 0: highlight -= 1

            elif key == curses.KEY_NPAGE and totalitems > (page+1) * maxitems:
                highlight = 0
                page += 1

            elif key == curses.KEY_PPAGE and page > 0:
                highlight = 0
                page -= 1

            elif key == curses.KEY_RIGHT or key == 10 or key == ord('l'):
                if state == "search":
                    curses.nocbreak(); stdscr.keypad(0); curses.echo()
                    curses.endwin()
                    url = data[currentpage[hl_cache]][highlight]['lnk']
                    print("[youtube-curses] Launching streamlink")
                    ls_exit_code = subprocess.call(["streamlink", url, q[quality]])
                    while ls_exit_code != 0:
                        print("\n[youtube-curses] Streamlink returned an error. This usually means that the selected stream quality is not available. If that is the case, then you can now choose one of the available streams printed above (defaults to 'best' if left empty). Or you can type 'A' to abort.")
                        selected_stream = input("Stream to open [best]: ")
                        if selected_stream == "A" or selected_stream == "a": break
                        if selected_stream == "": selected_stream = "best"
                        ls_exit_code = subprocess.call(["streamlink", url, selected_stream])
                    stdscr = curses.initscr()
                    curses.noecho()
                    curses.cbreak()
                    stdscr.keypad(1)
                    windowsize = init_display(stdscr)
                if state == "top":
                    windowsize = init_display(stdscr)
                    state = "search"
                    hl_cache = highlight
                    p_cache = page
                    highlight = 0
                    page = 0

            elif key == curses.KEY_LEFT or key == ord('b') or key == ord('B') or key == ord('h'):
                if state != "top":
                    windowsize = init_display(stdscr)
                    data = cache
                    state = "top"
                    highlight = hl_cache
                    page = p_cache

            elif key == ord('+'):
                quality += 1
                log.debug('Quality:' + str(quality))
                log.debug('windowsize:' + str(windowsize))

            elif key == ord('-'):
                quality -= 1
                log.debug('Quality:' + str(quality))
                log.debug('windowsize:' + str(windowsize))

#         elif key == ord('s') or key == ord('S') or key == ord('/'):
#             searchbox = curses.newwin(3, windowsize[1]-4, windowsize[0]//2-1, 2)
#             searchbox.border(0)
#             searchbox.addnstr(0, 3, "Search for streams", windowsize[0]-4)
#             searchbox.refresh()
#             curses.echo()
#             s = searchbox.getstr(1,1, windowsize[1]-6)
#             while not s:
#                 searchbox.addnstr(0, 3, "Please enter a valid search query!", windowsize[0] + 6)
#                 s = searchbox.getstr(1, 1, windowsize[1] - 6)
#             windowsize = init_display(stdscr)
#             query = [s.decode("utf-8"), 1]
#             data = query_youtube(query[0], query[1])
#             state = "search"
#             highlight = 0
#             page = 0

#         elif key == ord('r') or key == ord('R'):
#             if state == "search":
#                 windowsize = init_display(stdscr)
#                 data = query_youtube(query[0], query[1])
#             elif state == "top":
#                 windowsize = init_display(stdscr)
#                 data = query_youtube("topgames", 0)
#                 cache = data
#             highlight = 0
#             page = 0

            elif key == curses.KEY_RESIZE:
                curses.endwin()
                stdscr = curses.initscr()
                curses.noecho()
                curses.cbreak()
                stdscr.keypad(1)
                windowsize = init_display(stdscr)
                hl_cache = 0
                p_cache = 0
                highlight = 0
                page = 0

            else:
                donothing = True
    except Exception as e: log.exception(e)
    finally:
        curses.nocbreak(); stdscr.keypad(0); curses.echo()
        curses.endwin()
        print("[youtube-curses] Exiting")
        os._exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-c', '--channel-count', metavar='N',        default=10,         help='max channels to be queried',             type=int)
    parser.add_argument('-C', '--video-count',   metavar='N',        default=10,         help='video count to be queried',              type=int)
    parser.add_argument('-q', '--quality',       metavar='N',        default=0,          help='initial video quality [0=best,5=worst]'     )
    parser.add_argument('-l', '--logfile',       metavar='LOCATION', default=None,          help='default=None'                             )
    args = parser.parse_args()
    if args.logfile: logging.basicConfig(filename=args.logfile, level=logging.DEBUG)
    main(args)
