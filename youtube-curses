#!/usr/bin/env python3
import os
import sys
import code
from math import ceil
import logging
from query import get_front_page, search
import argparse
import threading
from img_display import W3MImageDisplayer
import curses, subprocess

log = logging.getLogger()
log.setLevel(logging.FATAL)
log.propagate = False

q = ['best', '720p', '480p', '360p', 'worst', 'audio_only']
quality = 0

def init_display(stdscr):
    global maxlen
    global win_l
    global win_r
    global w_item_count
    stdscr.clear()
    size = stdscr.getmaxyx()
    stdscr.addstr(size[0]//2-1, size[1]//2-5, "Loading...")
    stdscr.move(0,0)
    stdscr.refresh()
    maxlen = size[1] // 2 - 4
    w_item_count = size[0] // 2 - 3
    win_l = curses.newwin(size[0], size[1] // 2, 0, 0)
    win_r = curses.newwin(size[0], size[1] // 2, 0, size[1] // 2)
    return size

def prompt(msg):
    searchbox = curses.newwin(3, windowsize[1]-4, windowsize[0]//2-1, 2)
    searchbox.border(0)
    searchbox.addnstr(0, 3, msg, windowsize[0]-4)
    searchbox.refresh()
    curses.echo()
    s = searchbox.getstr(1,1, windowsize[1]-6)
    while not s:
        searchbox.addnstr(0, 3, "Please enter a valid search query!", windowsize[0] + 6)
        s = searchbox.getstr(1, 1, windowsize[1] - 6)
    return s.decode("utf-8")

def streamlink(url):
    url += '?disable_polymer=1'
    try:
        subprocess.call(["streamlink", url, q[quality]], stdout=open(os.devnull, 'w'), stderr=subprocess.STDOUT)
    except OSError as e: 
        if e.errno == os.errno.ENOENT:
            print('streamlink utility is missing. See README.md requirements section')

def main(args):
    global windowsize
    global quality
    # todo: parse args
    w3mid = W3MImageDisplayer()
    highlight = page = hl_cache = p_cache = key = 0
    state = "top"
    donothing = False

    # init curses stuff
    data = get_front_page(args.channel_count, args.video_count)
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(1)
    curses.curs_set(0)

    try:
        windowsize = init_display(stdscr)
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
                win_r.addstr(windowsize[0]-4, windowsize[1]//2-13, "search:  s")
                win_r.addstr(windowsize[0]-3, windowsize[1]//2-13, "refresh: r")
                win_r.addstr(windowsize[0]-1, windowsize[1]//2-9,  "quit: q")
                win_l.addstr(windowsize[0]-1, windowsize[1]//2-9,  "page: "+str(page+1))
#                 win_l.addstr(windowsize[0]-1, windowsize[1]//2-23, "highlight "+str(highlight))
#                 win_l.addstr(windowsize[0]-1, windowsize[1]//2-38, "w_item_count "+str(w_item_count))
#                 try: win_l.addstr(windowsize[0]-1, windowsize[1]//2-46, "itemcount "+str(itemcount))
#                 except: pass
#                 win_l.addstr(windowsize[0]-1, windowsize[1]//2-37, "itemcount "+str(itemcount))
                index = 0
                if state == "top":
                    itemcount = len(data)
                    currentpage = list(data.keys())[w_item_count*page:w_item_count*(page+1)]
                    try:
                        for channel_title in currentpage:
                            if index < w_item_count:
                                if index == highlight:
                                    win_l.addnstr(index*2+2, 2, channel_title, maxlen, curses.A_REVERSE)
                                    vids = data[channel_title]
                                    for v_ix,v in enumerate(vids):
                                        # vid_link = v['lnk']
                                        vid_title = v['ttl']
                                        win_r.addnstr(v_ix*2+4, 2, vid_title, maxlen)
                                else: win_l.addnstr(index*2+2, 2, channel_title, maxlen)
                            index += 1
                    except Exception as e: log.exception(e)
                if state == "search":
                    currentpage_vids = data[list(data)[hl_cache]]
                    itemcount = len(currentpage_vids)
                    for v_ix,vid in enumerate(currentpage_vids[w_item_count*page:w_item_count*(page+1)]):
                        vid_title = vid['ttl']
                        # vid_link = vid['lnk']
                        vid_desc = vid['dsc']
                        vid_dat = vid['dat']
                        tf = vid['tf']
                        if index < w_item_count:
                            if index == highlight:
                                dsc_rows = int(ceil(len(vid_desc)/maxlen))
                                for i in range(1, dsc_rows+1):
                                    win_r.addnstr(20+i, 2, vid['dsc'][(i*maxlen)-maxlen:i*maxlen], maxlen)
                                win_l.addnstr(index*2+2, 2, vid_title, maxlen, curses.A_REVERSE)
                                win_r.addnstr(18, 2, vid_dat.strftime("%A, %d. %B %Y %I:%M%p"), maxlen)
                                # view_count = vid['stats']['viewCount']

                                like_bar_len = 40
                                if type(vid['stats']) is not dict:
                                    vid['stats'] = vid['stats'].execute()['items'][0]['statistics']
                                like_count = int(vid['stats']['likeCount'])
                                dislike_count = int(vid['stats']['dislikeCount'])
                                react_count = like_count + dislike_count
                                like_amount = int(like_count * like_bar_len / react_count)
                                dislike_amount = int(dislike_count * like_bar_len / react_count)
                                like_bar = like_amount*'━' + dislike_amount*'─'
                                win_r.addnstr(18, maxlen-like_bar_len, like_bar, maxlen)

                                w3mid.quit()
                                w3mid = W3MImageDisplayer()
                                w3mid.set_params(tf, windowsize[1] - windowsize[1]/3, 1, windowsize[1], windowsize[0])
                                w3mid.start()
                            else: 
                                win_l.addnstr(index*2+2, 2, vid_title, maxlen)
                        index += 1
            win_l.refresh()
            win_r.refresh()
            key = stdscr.getch()

            if key == curses.KEY_DOWN or key == ord('j'):
                if highlight + page * w_item_count + 1 < itemcount:
                    if highlight + 1 == w_item_count:
                        page += 1
                        highlight = 0
                    else: highlight += 1

            elif key == curses.KEY_UP or key == ord('k'):
                if highlight == 0 and page > 0:
                    page -= 1
                    highlight = w_item_count - 1
                elif highlight > 0: highlight -= 1

            elif key == curses.KEY_NPAGE and itemcount > (page+1) * w_item_count: page += 1

            elif key == curses.KEY_PPAGE and page > 0: page -= 1

            elif key == curses.KEY_RIGHT or key == 10 or key == ord('l'):
                if state == "search":
                    url = data[currentpage[hl_cache]][highlight]['lnk']
                    threading.Thread(target=streamlink, args=[url]).start()
                if state == "top":
                    windowsize = init_display(stdscr)
                    state = "search"
                    hl_cache = highlight
                    p_cache = page
                    highlight = 0
                    page = 0

            elif key == curses.KEY_LEFT or key == ord('g'):
                page = 0
                highlight = 0

            elif key == curses.KEY_LEFT or key == ord('G'):
                page = itemcount // w_item_count
                highlight = itemcount % w_item_count - 1

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

            elif key == ord('s') or key == ord('S') or key == ord('/'):
                windowsize = init_display(stdscr)
                keyword = prompt('Search for videos')
                data = search(keyword, 10, part='snippet')
                # state = 'search'
                state = 'top'
                highlight = 0
                page = 0

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
        print('[youtube-curses] Exiting')
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
