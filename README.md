# IPÊ/87

A black-and-gray cyberpunk theme for Claude Desktop, named after the ipê, the
tree that turns Brasília yellow, pink and white every dry season. Brasília,
2087: the capital grew into a gray megacity under a drizzle that never stops,
and the ipês still bloom at street level.

## What it does

- **Backdrop.** An animated scene drawn full window behind the conversation:
  layered towers, the National Congress and the Cathedral, ipê trees in bloom
  with petals falling through the rain, fog, an elevated rail line with a passing train, a
  helicopter searchlight, an old propeller plane, flickering shop signs, a
  clock tower stopped at 23:58, a cinema marquee, and Vigia, the line's cyborg
  watchman, stencilled on a pillar at the right edge.
- **Palette.** Repaints the app in dark grays with a cold white accent
  (Claude Code 2.1.325 or newer).
- **Weather sign.** A lit sign above the message box with your city, the
  city's time in 24h format, temperature, sky and humidity. The billboard in
  the scene scrolls the same weather.
- **Chat opacity slider.** Eight segments beside the sign set how solid the
  chat panels are over the backdrop, from 20% to 90%. The choice is kept
  across sessions.
- **`/ipe` command.** `/ipe on`, `/ipe still` (no animation, lighter on
  CPU) or `/ipe off`.

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

## Changing the scene

The backdrop is generated. Edit `scripts/gen_scene.py`, then:

```bash
python3 scripts/gen_scene.py > hooks/scene.js
```

`hooks/make-colors.js` is Claude Code's palette generator, copied unchanged.
