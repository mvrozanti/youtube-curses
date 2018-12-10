# youtube-curses

# Usage

![Usage](https://i.imgur.com/ZDmzrQA.gif)
This is a simple youtube browser / streamlink frontend made with python and ncurses inspired by [twitch-curses](https://github.com/mvrozanti/twitch-curses).

# Requirements

- install [streamlink](https://github.com/streamlink/streamlink)
  - `sudo pacman -S streamlink` on Arch
  - optionally create `~/.streamlinkrc` file
- install requirements with `pip install --user -r requirements.txt`
- [follow this guide to get your credentials](https://developers.google.com/youtube/v3/getting-started)
  - don't forget to download your `client_secret.json`

## Features

- [ ] Download with `youtube-dl`
- [X] List subscriptions
- [ ] Search for content (prompt user)
- [ ] Get "recommended videos" (how tho?)
- [ ] Change sorting order
- [ ] Like/Dislike bar
- [ ] Show video length
- [ ] Show upload date
- [ ] Show channel's subscriber count
- [ ] Show view count
- [ ] Show description
- [ ] Show video/channel category
- [ ] Change subscription state of selected channel or video's channel
- [ ] Configurable keymap
- [X] Logfile argument
- [X] [ranger](https://github.com/ranger/ranger)-like thumbnail preview
  - [ ] needs testing
- [ ] Make `streamlink` call outside main thread (user will be able to browse while watching a video)
- [ ] Comment section abilities
  - [ ] Show comment section
  - [ ] Show comment count
  - [ ] Order comment section by either *Top comments* or *Newest first*
  - [ ] Comment on video
  - [ ] Reply to comment
- [ ] Move between different pages
  - [ ] Home / Recommended
  - [ ] Popular
  - [ ] Trending
  - [ ] Subscriptions
  - [ ] Watch later
  - [ ] Favorites
  - [ ] Playlists
  - [ ] Specific channel's videos
- [ ] Interact with video
  - [ ] Turn notifications on or off
  - [ ] Like/Dislike
  - [ ] Report
  - [ ] Save as (watch later/favorites/existing playlist/new playlist)
  - [ ] Share link (at current time or not)
- [ ] Cached elements / internal database (?) for faster bootup
  - [ ] Video information such as thumbnails, channel, link and title
- [ ] Published on PyPi

## License

[WTFPL](https://gitlab.com/corbie/twitch-curses/blob/master/LICENSE)
