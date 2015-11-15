#!/usr/bin/env python
import curses, json, pycurl, subprocess, textwrap
from io import BytesIO

proxy = ""
query_limit = "75"

print("twitch-cli: Initializing")
stdscr = curses.initscr()
curses.noecho()
curses.cbreak()
stdscr.keypad(1)
curses.curs_set(0)

def init_display(stdscr): 
	global maxlen
	global win_l
	global win_r
	global maxitems
	stdscr.clear()
	size = stdscr.getmaxyx()
	stdscr.addstr(size[0]//2-1, size[1]//2-5, "Loading...")
	stdscr.refresh()
	maxlen = size[1] // 2 - 4
	maxitems = size[0] // 2 - 1
	win_l = curses.newwin(size[0], size[1] // 2, 0, 0)
	win_r = curses.newwin(size[0], size[1] // 2, 0, size[1] // 2)
	return size

def query_twitch(query, search):
	if search:
		query = query.replace(" ", "+")
		url = "https://api.twitch.tv/kraken/search/streams?limit="+query_limit+"&q="+query
	elif query == "topgames":
		url = "https://api.twitch.tv/kraken/games/top?limit="+query_limit
	else:
		query = query.replace(" ", "+")
		url = "https://api.twitch.tv/kraken/streams?limit="+query_limit+"&game="+query
	buf = BytesIO()
	c = pycurl.Curl()
	c.setopt(c.URL, url)
	c.setopt(c.WRITEDATA, buf)
	if proxy != "":
		c.setopt(c.PROXY, 'socks5h://'+proxy)
	c.perform()
	c.close()
	body = buf.getvalue()
	buf.close()
	return json.loads(body.decode('utf-8'))

windowsize = init_display(stdscr)
data = query_twitch("topgames", 0)

highlight = 0
page = 0
state = "top"
q = ["source", "high", "medium", "low", "mobile", "audio"]
quality = 0
key = 0
try:
	while key != ord('q'):
		if windowsize[0] > 8 and windowsize[1] > 30:
			win_l.clear()
			win_l.border(0)
			win_r.clear()
			win_r.border(0)
			win_l.addstr(windowsize[0]-1, windowsize[1]//2-9, "page:"+str(page+1))
			win_r.addstr(windowsize[0]-4, windowsize[1]//2-11, "search: s")
			win_r.addstr(windowsize[0]-3, windowsize[1]//2-12, "refresh: r")
			win_r.addstr(windowsize[0]-2, windowsize[1]//2-9, "quit: q")
			index = 0
			if state == "top":
				totalitems = len(data['top'])
				currentpage = data['top'][maxitems*page:maxitems*(page+1)]
				for i in currentpage:
					if index < maxitems:
						if index == highlight:
							win_l.addnstr(index*2+2, 2, str(i['game']['name']), maxlen, curses.A_REVERSE)
							win_r.addnstr(2, 3, "Viewers: "+str(i['viewers']), maxlen)
							win_r.addnstr(3, 3, "Channels: "+str(i['channels']), maxlen)
						else:
							win_l.addnstr(index*2+2, 2, str(i['game']['name']), maxlen)
					index += 1
			if state == "search":
				totalitems = len(data['streams'])
				currentpage = data['streams'][maxitems*page:maxitems*(page+1)]
				for i in currentpage:
					if index < maxitems:
						if index == highlight:
							win_l.addnstr(index*2+2, 2, str(i['channel']['display_name']), maxlen, curses.A_REVERSE)
							win_r.addnstr(windowsize[0]-3, 2, "quality: +-", maxlen)
							win_r.addnstr(windowsize[0]-2, 3, q[quality], maxlen)
							win_r.addnstr(2, 3, str(i['game']), maxlen)
							win_r.addnstr(4, 3, "Viewers: "+str(i['viewers']), maxlen)
							win_r.addstr(5, 3, "Status:")
							status = textwrap.wrap(str(i['channel']['status']), windowsize[1]//2-6)
							l_num = 7
							for line in status:
								if l_num >= windowsize[0] - 4:
									break
								win_r.addstr(l_num, 4, line)
								l_num += 1
						else:
							win_l.addnstr(index*2+2, 2, str(i['channel']['display_name']), maxlen)
					index += 1
			win_l.refresh()
			win_r.refresh()
		else:
			stdscr.clear()
			stdscr.addstr(0,0,"Terminal")
			stdscr.addstr(1,0,"too small")
		key = stdscr.getch()
		if key == curses.KEY_DOWN:
			if highlight + page * maxitems + 1 < totalitems:
				if highlight + 1 == maxitems:
					page += 1
					highlight = 0
				else:
					highlight += 1
		elif key == curses.KEY_UP:
			if highlight == 0 and page > 0:
				page -= 1
				highlight = maxitems - 1
			elif highlight > 0:
				highlight -= 1
		elif key == curses.KEY_NPAGE and totalitems > (page+1) * maxitems:
			highlight = 0
			page += 1
		elif key == curses.KEY_PPAGE and page > 0:
			highlight = 0
			page -= 1
		elif key == curses.KEY_RIGHT or key == 10:
			if state == "search":
				curses.nocbreak(); stdscr.keypad(0); curses.echo()
				curses.endwin()
				print("twitch-cli: Launching livestreamer")
				subprocess.call(["livestreamer", currentpage[highlight]['channel']['url'], q[quality]+",best"])
				stdscr = curses.initscr()
				curses.noecho()
				curses.cbreak()
				stdscr.keypad(1)
			elif state == "top":
				init_display(stdscr)
				query = [currentpage[highlight]['game']['name'], 0]
				data = query_twitch(query[0], query[1])
				state = "search"
				highlight = 0
				page = 0
		elif key == curses.KEY_LEFT:
			if state != "top":
				init_display(stdscr)
				data = query_twitch("topgames", 0)
				state = "top"
				highlight = 0
				page = 0
		elif key == ord('+') and quality > 0:
			quality -= 1
		elif key == ord('-') and quality < 5:
			quality += 1
		elif key == ord('s'):
			searchbox = curses.newwin(3, windowsize[1]-4, windowsize[0]//2-1, 2)
			searchbox.border(0)
			searchbox.addnstr(0, 3, "Search for streams", windowsize[0]-4)
			searchbox.refresh()
			curses.echo()
			s = searchbox.getstr(1,1, windowsize[1]-6)
			init_display(stdscr)
			query = [s.decode("utf-8"), 1]
			data = query_twitch(query[0], query[1])
			state = "search"
			highlight = 0
			page = 0
		elif key == ord('r'):
			if state == "search":
				init_display(stdscr)
				data = query_twitch(query[0], query[1])
			elif state == "top":
				init_display(stdscr)
				data = query_twitch("topgames", 0)
			highlight = 0
			page = 0
		elif key == curses.KEY_RESIZE:
			windowsize = init_display(stdscr)
			highlight = 0
			page = 0
finally:
	curses.nocbreak(); stdscr.keypad(0); curses.echo()
	curses.endwin()
	print("twitch-cli: Exiting")