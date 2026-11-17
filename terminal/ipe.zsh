# IPÊ/87 look for the Claude Desktop terminal: gray palette, banner with live
# weather and 24h city time, gray prompt. ~/.zshrc sources this only when
# TERM_PROGRAM=claude-desktop, so other terminals keep their own look.

zmodload zsh/datetime
zmodload -F zsh/stat b:zstat
autoload -Uz add-zsh-hook
setopt prompt_subst

IPE_CACHE=${XDG_CACHE_HOME:-$HOME/.cache}/ipe
IPE_WEATHER_TTL=600
IPE_PLACE_TTL=3600
typeset -gA IPE
typeset -g IPE_MTIME= IPE_RPROMPT=

_ipe_sky() {
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

_ipe_age() {
  local -a m
  zstat -A m +mtime -- $1 2>/dev/null || { REPLY=999999; return }
  REPLY=$(( EPOCHSECONDS - m[1] ))
}

# Location comes from the public IP (city level); coordinates sent to
# Open-Meteo are rounded to two decimals.
_ipe_fetch() {
  emulate -L zsh
  local ua='ipe-theme/0.3' place=$IPE_CACHE/place json city lat lon url
  mkdir -p $IPE_CACHE
  _ipe_age $place
  if [[ ! -s $place ]] || (( REPLY > IPE_PLACE_TTL )); then
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
offset=\(.utc_offset_seconds)"' > $IPE_CACHE/weather.tmp 2>/dev/null &&
    mv -f $IPE_CACHE/weather.tmp $IPE_CACHE/weather
  rm -f $IPE_CACHE/weather.tmp
}

_ipe_load() {
  local k v f=$IPE_CACHE/weather
  IPE=()
  [[ -r $f ]] || return
  while IFS='=' read -r k v; do IPE[$k]=$v; done < $f
}

_ipe_refresh_if_stale() {
  local lock=$IPE_CACHE/.fetching
  _ipe_age $IPE_CACHE/weather
  (( REPLY > IPE_WEATHER_TTL )) || return
  _ipe_age $lock
  (( REPLY < 30 )) && return
  mkdir -p $IPE_CACHE && : > $lock
  { _ipe_fetch; rm -f $lock } &>/dev/null &!
}

# The city's UTC offset from Open-Meteo, so this is the city's time even when
# the machine runs in another zone.
_ipe_time() {
  if [[ -n ${IPE[offset]} ]]; then
    date -u -r $(( EPOCHSECONDS + IPE[offset] )) +%H:%M
  else
    strftime %H:%M $EPOCHSECONDS
  fi
}

_ipe_palette() {
  local -a ansi=(1c1d21 dc5a50 9cc2a8 d1b072 8d96a0 b3aed0 a6b4bf aeb2b8
                 5a5e65 e0625a b7d4c0 e0c690 c8d0d8 cdc9e0 c9d3db e9ecef)
  local i
  for i in {1..16}; do printf '\e]4;%d;#%s\e\\' $(( i - 1 )) $ansi[i]; done
  printf '\e]10;#aeb2b8\e\\\e]11;#0b0c0e\e\\\e]12;#e9ecef\e\\'
}

# An ipê in bloom beside the Congresso Nacional: the Senate dome, the twin
# towers joined by their bridge, and the Chamber's bowl on the long platform.
_ipe_banner() {
  local dim=$'\e[38;2;59;62;68m' art=$'\e[38;2;90;94;101m' tower=$'\e[38;2;140;145;152m'
  local mute=$'\e[38;2;123;127;134m' mid=$'\e[38;2;174;178;184m' hi=$'\e[38;2;233;236;239m'
  local ipe=$'\e[38;2;207;169;63m' bold=$'\e[1m' off=$'\e[0m'
  local city=${IPE[city]:-locating…} weather='weather on next prompt' i
  [[ -n ${IPE[temp]} ]] &&
    weather="${IPE[temp]}°C $(_ipe_sky ${IPE[code]})  ·  humidity ${IPE[humidity]}%"
  local -a tree=('        ' '  ▗▄▄▖  ' ' ▟████▙ ' ' ▀████▀ ' '   ▐▌   ')
  local -a tree_color=($ipe $ipe $ipe $ipe $tower)
  local -a left=('              ' '              ' '              ' '     ▗▄▄▄▖    ' '   ▗▟█████▙▖  ')
  local -a towers=('▐█▌▐█▌' '▐█▌▐█▌' '▐████▌' '▐█▌▐█▌' '▐█▌▐█▌')
  local -a right=('              ' '              ' '              ' ' ▄▄▄▄▄▄▄▄▄▄▄  ' '  ▀███████▀   ')
  local -a text=(
    ''
    "${hi}${bold}IPÊ/87${off}  ${mute}·  flor do cerrado${off}"
    "${hi}${bold}${(U)city}${off}  ${hi}${bold}$(_ipe_time)${off}"
    "${mid}${weather}${off}"
    "${mute}claude desktop terminal${off}"
  )
  print
  for i in {1..5}; do
    print -r -- "${tree_color[i]}${tree[i]}${art}${left[i]}${tower}${towers[i]}${art}${right[i]}${off}   ${text[i]}"
  done
  print -r -- "${art}▄▄▄${tower}▐▌${art}▄▄▄ ▄▄▄▄▄▄▄▄▄▄▄▄▄${tower}▐█▌▐█▌${art}▄▄▄▄▄▄▄▄▄▄▄▄▄ ${off}"
  print -r -- "${dim}${ipe}▝▘▀${dim}▀▀▀▀▀ ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀ ${off}"
  print
}

_ipe_precmd() {
  local -a m
  if zstat -A m +mtime -- $IPE_CACHE/weather 2>/dev/null && [[ $m[1] != $IPE_MTIME ]]; then
    IPE_MTIME=$m[1]
    _ipe_load
  fi
  IPE_RPROMPT=
  [[ -n ${IPE[temp]} ]] && IPE_RPROMPT="${IPE[temp]}°C $(_ipe_sky ${IPE[code]})"
  _ipe_refresh_if_stale
}

ZSH_THEME_GIT_PROMPT_PREFIX=' %F{#5a5e65}git:(%F{#aeb2b8}'
ZSH_THEME_GIT_PROMPT_SUFFIX='%f'
ZSH_THEME_GIT_PROMPT_DIRTY='%F{#5a5e65}) %F{#e9ecef}*'
ZSH_THEME_GIT_PROMPT_CLEAN='%F{#5a5e65})'
PROMPT='%F{#3b3e44}▌%f%F{#e9ecef}%B%D{%H:%M}%b%f %F{#aeb2b8}%c%f$(git_prompt_info) %(?.%F{#e9ecef}.%F{#dc5a50})❯%f '
RPROMPT='%F{#5a5e65}${IPE_RPROMPT}%f'

add-zsh-hook precmd _ipe_precmd

_ipe_palette
mkdir -p $IPE_CACHE
[[ -s $IPE_CACHE/weather ]] || _ipe_fetch
_ipe_load
_ipe_age $IPE_CACHE/weather
IPE_MTIME=$(( EPOCHSECONDS - REPLY ))
_ipe_banner
_ipe_refresh_if_stale
