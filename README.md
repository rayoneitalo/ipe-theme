# IPÊ/87

A black-and-gray cyberpunk theme for Claude Desktop, named after the ipê, the
tree that turns Brasília yellow, pink and white every dry season. Brasília,
2087: the capital grew into a gray megacity, and the ipês still bloom at
street level, their flowers falling over the whole city.

## What it does

- **Backdrop.** An animated scene drawn full window behind the conversation:
  layered towers, the National Congress and the Cathedral, ipê trees in bloom,
  fog, an elevated rail line with a passing train, a helicopter searchlight,
  an old propeller plane, flickering shop signs, a clock tower stopped at
  23:58 and a cinema marquee.
- **What falls.** Ipê flowers by default. `/ipe rain` brings back the rain,
  `/ipe flowers` the flowers, and `/ipe weather` follows the live weather:
  rain while it rains where you are (drizzle, rain, showers or
  thunderstorm), flowers otherwise. The choice is kept across sessions.
- **Palette.** Repaints the app in dark grays with a cold white accent
  (Claude Code 2.1.325 or newer).
- **Weather sign.** A lit sign above the message box with your city, the
  city's time in 24h format, temperature, sky and humidity.
- **Chat opacity slider.** Eight segments beside the sign set how solid the
  chat panels are over the backdrop, from 20% to 90%. The choice is kept
  across sessions.
- **`/ipe` command.** `/ipe on`, `/ipe still` (no animation, lighter on
  CPU) or `/ipe off`. The choice is kept across sessions.

## Install

At the prompt of a Claude Code terminal session:

```
/plugin install ipe-theme --marketplace rayoneitalo/ipe-theme
```

Answer `y` to add the marketplace, then pick the user scope.

From a shell:

```bash
claude plugin install ipe-theme --marketplace rayoneitalo/ipe-theme
```

In Claude Desktop, where `/plugin` does not run: click **+** next to the prompt
box, then **Plugins**, **Add marketplace** with `rayoneitalo/ipe-theme`, then
**Add plugin**.

Set Claude Desktop's appearance to **Dark**: the theme defines dark colors
only. The backdrop needs a Claude Desktop build that draws plugin backdrops;
`/ipe on` tells you if yours does not.

## Terminal look (optional)

`terminal/ipe.zsh` themes the shell that Claude Desktop's terminal panel
opens: a banner with the National Congress skyline and the live weather, a
gray prompt with the time, the weather on the right, and a gray 16-color
palette. It applies only where `TERM_PROGRAM=claude-desktop`, so other
terminals keep their own look. It needs `zsh`, `curl` and `jq`.

```bash
mkdir -p ~/.config/ipe && cp terminal/ipe.zsh ~/.config/ipe/ipe.zsh
```

Then add to `~/.zshrc`, after Oh My Zsh loads if you use it:

```zsh
if [[ $TERM_PROGRAM == claude-desktop && -r ~/.config/ipe/ipe.zsh ]]; then
  source ~/.config/ipe/ipe.zsh
fi
```

## Privacy

Nothing about you is stored in this repository. At run time, to show the
weather:

- your public IP address goes to [ipapi.co](https://ipapi.co), or
  [ipwho.is](https://ipwho.is) if the first fails, to find your city
  (city-level accuracy, refreshed hourly);
- the city's coordinates, rounded to two decimals, go to
  [Open-Meteo](https://open-meteo.com) for the current weather (refreshed
  every 10 minutes).

The results stay on your machine: in the plugin's session state, and for the
terminal look in `~/.cache/ipe/`. No API key is needed or used.

## Spotify (optional)

Skip this section and the theme works the same. Once set up, the weather sign
also shows the song or podcast playing on your Spotify account, and the
neon box at the top of the tower on the right scrolls it with its controls. With
`--control`, ⏮ ⏸ ⏭ buttons appear beside it (playback control needs Spotify
Premium). It needs macOS, because the token lives in the Keychain.

1. On [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard),
   create an app. Set the redirect URI to exactly
   `http://127.0.0.1:8898/callback`, tick **Web API**, and copy the
   **Client ID**. The flow does not use a client secret, so never paste one
   anywhere.
2. In this repository's folder, run:

   ```bash
   python3 scripts/spotify-login.py --client-id <your client id>
   ```

   Add `--control` for the playback buttons. Log in to Spotify in the browser
   tab it opens.
3. In Claude, run `/ipe spotify`.

`/ipe spotify off` hides it for the session. To disconnect for good:

```bash
python3 scripts/spotify-login.py --logout
```

and revoke the app at [spotify.com/account/apps](https://www.spotify.com/account/apps/).

How the connection is kept safe:

- **No client secret.** Login uses OAuth's Authorization Code flow with PKCE,
  made for apps that cannot keep a secret.
- **Local-only redirect.** The browser returns only to `127.0.0.1`, and the
  answer must carry a one-time `state` value, so another page cannot inject a
  login.
- **Token in the Keychain only.** The refresh token is stored under the service
  `ipe-theme-spotify` and written through `security` on stdin, so it never
  shows in the process list. It is never printed, logged, or saved to a file,
  this repository or the plugin's state. The short-lived access token stays in
  memory.
- **Smallest permissions.** By default only `user-read-currently-playing`.
  `--control` adds `user-read-playback-state` and `user-modify-playback-state`.
- **Spotify only.** Requests go to `accounts.spotify.com` and
  `api.spotify.com` over HTTPS. Track names are cleaned and escaped before they
  are drawn.

## Changing the scene

The backdrop is generated. Edit `scripts/gen_scene.py`, then:

```bash
python3 scripts/gen_scene.py > hooks/scene.js
```

`hooks/make-colors.js` is Claude Code's palette generator, copied unchanged.

## License

MIT, see [LICENSE](LICENSE). `hooks/make-colors.js` comes from Claude Code and is not
covered by it.
