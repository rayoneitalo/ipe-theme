# GAROA/87 look for the Claude Desktop terminal: gray palette, banner with live
# weather and 24h city time, gray prompt. ~/.zshrc sources this only when
# TERM_PROGRAM=claude-desktop, so other terminals keep their own look.

zmodload zsh/datetime
zmodload -F zsh/stat b:zstat
autoload -Uz add-zsh-hook
setopt prompt_subst

GAROA_CACHE=${XDG_CACHE_HOME:-$HOME/.cache}/garoa
GAROA_WEATHER_TTL=600
GAROA_PLACE_TTL=3600
typeset -gA GAROA
typeset -g GAROA_MTIME= GAROA_RPROMPT=

_garoa_sky() {
  case $1 in
    0) print -r clear ;;
    1) print -r 'mostly clear' ;;
    2) print -r 'partly cloudy' ;;
    3) print -r overcast ;;
    45|48) print -r fog ;;
    51) print -r 'light drizzle' ;;
    53) print -r drizzle ;;
    55) print -r 'heavy drizzle' ;;
    56|57) print -r 'freezing drizzle' ;;
    61) print -r 'light rain' ;;
    63) print -r rain ;;
    65) print -r 'heavy rain' ;;
    66|67) print -r 'freezing rain' ;;
    71) print -r 'light snow' ;;
    73) print -r snow ;;
    75) print -r 'heavy snow' ;;
    77) print -r 'snow grains' ;;
    80|81) print -r showers ;;
    82) print -r 'violent showers' ;;
    85|86) print -r 'snow showers' ;;
    95) print -r thunderstorm ;;
    96|99) print -r 'thunderstorm, hail' ;;
    *) print -r 'unknown sky' ;;
  esac
}

_garoa_age() {
  local -a m
  zstat -A m +mtime -- $1 2>/dev/null || { REPLY=999999; return }
  REPLY=$(( EPOCHSECONDS - m[1] ))
}

# Location comes from the public IP (city level); coordinates sent to
# Open-Meteo are rounded to two decimals.
_garoa_fetch() {
  emulate -L zsh
  local ua='garoa-theme/0.2' place=$GAROA_CACHE/place json city lat lon url
  mkdir -p $GAROA_CACHE
  _garoa_age $place
  if [[ ! -s $place ]] || (( REPLY > GAROA_PLACE_TTL )); then
    for url in https://ipapi.co/json/ https://ipwho.is/; do
      json=$(curl -fsS -m 4 -A $ua $url 2>/dev/null) || continue
      print -r -- $json |
        jq -er '[.city, (.latitude * 100 | round / 100), (.longitude * 100 | round / 100)]
                | select(.[0] != null and .[1] != null and .[2] != null) | @tsv' \
          > $place.tmp 2>/dev/null && { mv -f $place.tmp $place; break }
    done
    rm -f $place.tmp
  fi
  [[ -s $place ]] || return 1
  IFS=$'\t' read -r city lat lon < $place
  json=$(curl -fsS -m 5 -A $ua "https://api.open-meteo.com/v1/forecast?latitude=$lat&longitude=$lon&current=temperature_2m,relative_humidity_2m,weather_code&timezone=auto" 2>/dev/null) || return 1
  print -r -- $json |
    jq -er --arg city $city '"city=\($city)
temp=\(.current.temperature_2m | round)
humidity=\(.current.relative_humidity_2m | round)
code=\(.current.weather_code)
offset=\(.utc_offset_seconds)"' > $GAROA_CACHE/weather.tmp 2>/dev/null &&
    mv -f $GAROA_CACHE/weather.tmp $GAROA_CACHE/weather
  rm -f $GAROA_CACHE/weather.tmp
}

_garoa_load() {
  local k v f=$GAROA_CACHE/weather
  GAROA=()
  [[ -r $f ]] || return
  while IFS='=' read -r k v; do GAROA[$k]=$v; done < $f
}

_garoa_refresh_if_stale() {
  local lock=$GAROA_CACHE/.fetching
  _garoa_age $GAROA_CACHE/weather
  (( REPLY > GAROA_WEATHER_TTL )) || return
  _garoa_age $lock
  (( REPLY < 30 )) && return
  mkdir -p $GAROA_CACHE && : > $lock
  { _garoa_fetch; rm -f $lock } &>/dev/null &!
}

# The city's UTC offset from Open-Meteo, so this is the city's time even when
# the machine runs in another zone.
_garoa_time() {
  if [[ -n ${GAROA[offset]} ]]; then
    date -u -r $(( EPOCHSECONDS + GAROA[offset] )) +%H:%M
  else
    strftime %H:%M $EPOCHSECONDS
  fi
}

_garoa_palette() {
  local -a ansi=(1c1d21 dc5a50 9cc2a8 d1b072 8d96a0 b3aed0 a6b4bf aeb2b8
                 5a5e65 e0625a b7d4c0 e0c690 c8d0d8 cdc9e0 c9d3db e9ecef)
  local i
  for i in {1..16}; do printf '\e]4;%d;#%s\e\\' $(( i - 1 )) $ansi[i]; done
  printf '\e]10;#aeb2b8\e\\\e]11;#0b0c0e\e\\\e]12;#e9ecef\e\\'
}

# Congresso Nacional: the Senate dome, the twin towers joined by their bridge,
# and the Chamber's bowl, all on the long platform.
_garoa_banner() {
  local dim=$'\e[38;2;59;62;68m' art=$'\e[38;2;90;94;101m' tower=$'\e[38;2;140;145;152m'
  local mute=$'\e[38;2;123;127;134m' mid=$'\e[38;2;174;178;184m' hi=$'\e[38;2;233;236;239m'
  local bold=$'\e[1m' off=$'\e[0m'
  local city=${GAROA[city]:-locating…} weather='weather on next prompt' i
  [[ -n ${GAROA[temp]} ]] &&
    weather="${GAROA[temp]}°C $(_garoa_sky ${GAROA[code]})  ·  humidity ${GAROA[humidity]}%"
  local -a left=('              ' '              ' '              ' '     ▗▄▄▄▖    ' '   ▗▟█████▙▖  ')
  local -a towers=('▐█▌▐█▌' '▐█▌▐█▌' '▐████▌' '▐█▌▐█▌' '▐█▌▐█▌')
  local -a right=('              ' '              ' '              ' ' ▄▄▄▄▄▄▄▄▄▄▄  ' '  ▀███████▀   ')
  local -a text=(
    ''
    "${hi}${bold}GAROA/87${off}  ${mute}·  terra da garoa${off}"
    "${hi}${bold}${(U)city}${off}  ${hi}${bold}$(_garoa_time)${off}"
    "${mid}${weather}${off}"
    "${mute}claude desktop terminal${off}"
  )
  print
  for i in {1..5}; do
    print -r -- "${art}${left[i]}${tower}${towers[i]}${art}${right[i]}${off}   ${text[i]}"
  done
  print -r -- "${art} ▄▄▄▄▄▄▄▄▄▄▄▄▄${tower}▐█▌▐█▌${art}▄▄▄▄▄▄▄▄▄▄▄▄▄ ${off}"
  print -r -- "${dim} ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀ ${off}"
  print
}

_garoa_precmd() {
  local -a m
  if zstat -A m +mtime -- $GAROA_CACHE/weather 2>/dev/null && [[ $m[1] != $GAROA_MTIME ]]; then
    GAROA_MTIME=$m[1]
    _garoa_load
  fi
  GAROA_RPROMPT=
  [[ -n ${GAROA[temp]} ]] && GAROA_RPROMPT="${GAROA[temp]}°C $(_garoa_sky ${GAROA[code]})"
  _garoa_refresh_if_stale
}

ZSH_THEME_GIT_PROMPT_PREFIX=' %F{#5a5e65}git:(%F{#aeb2b8}'
ZSH_THEME_GIT_PROMPT_SUFFIX='%f'
ZSH_THEME_GIT_PROMPT_DIRTY='%F{#5a5e65}) %F{#e9ecef}*'
ZSH_THEME_GIT_PROMPT_CLEAN='%F{#5a5e65})'
PROMPT='%F{#3b3e44}▌%f%F{#e9ecef}%B%D{%H:%M}%b%f %F{#aeb2b8}%c%f$(git_prompt_info) %(?.%F{#e9ecef}.%F{#dc5a50})❯%f '
RPROMPT='%F{#5a5e65}${GAROA_RPROMPT}%f'

add-zsh-hook precmd _garoa_precmd

_garoa_palette
mkdir -p $GAROA_CACHE
[[ -s $GAROA_CACHE/weather ]] || _garoa_fetch
_garoa_load
_garoa_age $GAROA_CACHE/weather
GAROA_MTIME=$(( EPOCHSECONDS - REPLY ))
_garoa_banner
_garoa_refresh_if_stale
