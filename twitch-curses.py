#!/usr/bin/env python
import curses, json, pycurl, subprocess, textwrap, urllib.parse
from io import BytesIO

print("[twitch-curses] Initializing")
stdscr = curses.initscr()
curses.noecho()
curses.cbreak()
stdscr.keypad(1)
curses.curs_set(0)

query_limit = "75"
highlight = 0
page = 0
hl_cache = 0
p_cache = 0
state = "top"
q = ["source", "high", "medium", "low", "mobile", "audio"]
quality = 0
key = 0
donothing = False

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

def query_twitch(query, search):
	if search:
		query = urllib.parse.quote(query)
		url = "https://api.twitch.tv/kraken/search/streams?limit="+query_limit+"&q="+query
	elif query == "topgames":
		url = "https://api.twitch.tv/kraken/games/top?limit="+query_limit
	else:
		query = urllib.parse.quote(query)
		url = "https://api.twitch.tv/kraken/streams?limit="+query_limit+"&game="+query
	buf = BytesIO()
	c = pycurl.Curl()
	c.setopt(c.URL, url)
	c.setopt(c.HTTPHEADER, ['Client-ID: caozjg12y6hjop39wx996mxn585yqyk'])
	c.setopt(c.WRITEDATA, buf)
	c.perform()
	c.close()
	body = buf.getvalue()
	buf.close()
	return json.loads(body.decode('utf-8'))

try:
	windowsize = init_display(stdscr)
	data = query_twitch("topgames", 0)
	cache = data
	while key != ord('q') and key != ord('Q'):
		if windowsize[0] < 10 or windowsize[1] < 32:
			stdscr.clear()
			stdscr.addstr(0,0,"Terminal")
			stdscr.addstr(1,0,"too small")
		elif donothing == True:
			donothing = False
		else:
			win_l.erase()
			win_l.border(0)
			win_r.erase()
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
							win_r.addstr(windowsize[0]-5, windowsize[1]//2-9, "back: b")
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
		key = stdscr.getch()
		if key == curses.KEY_DOWN or key == ord('j'):
			if highlight + page * maxitems + 1 < totalitems:
				if highlight + 1 == maxitems:
					page += 1
					highlight = 0
				else:
					highlight += 1
		elif key == curses.KEY_UP or key == ord('k'):
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
		elif key == curses.KEY_RIGHT or key == 10 or key == ord('l'):
			if state == "search":
				curses.nocbreak(); stdscr.keypad(0); curses.echo()
				curses.endwin()
				chat_url = "http://www.twitch.tv/"+currentpage[highlight]['channel']['display_name']+"/chat"
				print("[twitch-curses]", currentpage[highlight]['channel']['display_name'], "-", currentpage[highlight]['channel']['status'], "(", currentpage[highlight]['viewers'], "viewers )")
				print("[twitch-curses] Chat url:", chat_url)
				print("[twitch-curses] Launching livestreamer")
				ls_exit_code = subprocess.call(["livestreamer", "--http-header", "Client-ID=caozjg12y6hjop39wx996mxn585yqyk", currentpage[highlight]['channel']['url'], q[quality]])
				while ls_exit_code != 0:
					print("\n[twitch-curses] Livestreamer returned an error. This usually means that the selected stream quality is not available. If that is the case, then you can now choose one of the available streams printed above (defaults to 'best' if left empty). Or you can type 'A' to abort.")
					selected_stream = input("Stream to open [best]: ")
					if selected_stream == "A" or selected_stream == "a":
						break
					if selected_stream == "":
						selected_stream = "best"
					ls_exit_code = subprocess.call(["livestreamer", "--http-header", "Client-ID=caozjg12y6hjop39wx996mxn585yqyk", currentpage[highlight]['channel']['url'], selected_stream])
				stdscr = curses.initscr()
				curses.noecho()
				curses.cbreak()
				stdscr.keypad(1)
				windowsize = init_display(stdscr)
			elif state == "top":
				windowsize = init_display(stdscr)
				query = [currentpage[highlight]['game']['name'], 0]
				data = query_twitch(query[0], query[1])
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
		elif key == ord('+') and quality > 0:
			quality -= 1
		elif key == ord('-') and quality < 5:
			quality += 1
		elif key == ord('s') or key == ord('S') or key == ord('/'):
			searchbox = curses.newwin(3, windowsize[1]-4, windowsize[0]//2-1, 2)
			searchbox.border(0)
			searchbox.addnstr(0, 3, "Search for streams", windowsize[0]-4)
			searchbox.refresh()
			curses.echo()
			s = searchbox.getstr(1,1, windowsize[1]-6)
			windowsize = init_display(stdscr)
			query = [s.decode("utf-8"), 1]
			data = query_twitch(query[0], query[1])
			state = "search"
			highlight = 0
			page = 0
		elif key == ord('r') or key == ord('R'):
			if state == "search":
				windowsize = init_display(stdscr)
				data = query_twitch(query[0], query[1])
			elif state == "top":
				windowsize = init_display(stdscr)
				data = query_twitch("topgames", 0)
				cache = data
			highlight = 0
			page = 0
		elif key == curses.KEY_RESIZE:
			windowsize = init_display(stdscr)
			hl_cache = 0
			p_cache = 0
			highlight = 0
			page = 0
		else:
			donothing = True
finally:
	curses.nocbreak(); stdscr.keypad(0); curses.echo()
	curses.endwin()
	print("[twitch-curses] Exiting")
