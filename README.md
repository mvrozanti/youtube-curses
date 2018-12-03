# youtube-curses

# Usage

[](![Usage](https://i.imgur.com/nnIgkVr.gif))

This is a simple youtube browser / streamlink frontend made with python and ncurses inspired by [twitch-curses](https://github.com/mvrozanti/twitch-curses).

# Requirements

- install streamlink
  - `sudo pacman -S streamlink` on Arch
  - optionally create `~/.streamlinkrc` file
- install requirements with `pip install --user -r requirements.txt`
- [follow this guide to get your credentials](https://developers.google.com/youtube/v3/getting-started)
  - don't forget to download your client_secret.json

## Features

- [X] List subscriptions
- [ ] Search for content (prompt user)
- [ ] Get "recommended videos" (how tho?)
- [ ] Configurable keymap
- [ ] Logfile argument
- [ ] [ranger](https://github.com/ranger/ranger)-like thumbnail preview
- [ ] Show comment section
- [ ] Hotkey to go to channel
- [ ] Publish on PyPi

## License

[WTFPL](https://gitlab.com/corbie/twitch-curses/blob/master/LICENSE)
