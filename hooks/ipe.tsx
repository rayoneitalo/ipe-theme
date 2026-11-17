import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

import type { Sky } from '../types'
import { makeColors } from './make-colors.js'
import { SCENE } from './scene.js'

const PLUGIN = 'ipe-theme'
const GLASS = { blur: 16, tint: '#0b0c0e' }
const OPACITY_STEPS = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9] as const
const DEFAULT_OPACITY = 0.6
const ALT = 'Brasília at night under drizzle: gray towers, the National Congress, ipê trees in bloom, an elevated rail line'
const MONO = "Menlo,Consolas,'DejaVu Sans Mono',monospace"
// Menlo and its fallbacks advance every glyph by 0.602em.
const ADVANCE = 0.602

// Token values come from the design system's generator; hand-written keys paint nothing.
const { theme: COLORS } = makeColors({
  label: 'IPÊ/87',
  only: 'dark',
  roles: { accent: '#c8d0d8', danger: '#e0625a', success: '#9cc2a8', warning: '#d1b072', pro: '#b3aed0' },
  dark: {
    gray: {
      anchors: {
        'surface-0': '#0b0c0e',
        'surface-1': '#121316',
        'surface-2': '#17181b',
        'surface-3': '#1c1d21',
        'text-primary': '#e9ecef',
        'text-secondary': '#b4b8be',
        'text-muted': '#959aa1',
      },
    },
  },
})

const skyAtom = atom({ plugin: 'ipe-theme', key: 'sky' } as const, null)
const timeAtom = atom({ plugin: 'ipe-theme', key: 'time' } as const, '')
const offAtom = atom({ plugin: 'ipe-theme', key: 'isOff' } as const, false)
const locatingAtom = atom({ plugin: 'ipe-theme', key: 'locating' } as const, 'pending')
const opacityAtom = atom({ plugin: 'ipe-theme', key: 'opacity' } as const, DEFAULT_OPACITY)
const modeAtom = atom({ plugin: 'ipe-theme', key: 'mode' } as const, 'on')

const SCENES = { on: 'ipe', still: 'ipe-still' } as const
type Mode = keyof typeof SCENES
type Result = { isDrawn: boolean; reason?: string }

const UA = { accept: 'application/json', 'user-agent': 'ipe-theme/0.3' }
const LOCATORS = ['https://ipapi.co/json/', 'https://ipwho.is/']
const CLOCK_MS = 15_000
const WEATHER_MS = 10 * 60_000
const LOCATE_MS = 60 * 60_000

const SKY: Record<number, string> = {
  0: 'clear', 1: 'mostly clear', 2: 'partly cloudy', 3: 'overcast',
  45: 'fog', 48: 'rime fog',
  51: 'light drizzle', 53: 'drizzle', 55: 'heavy drizzle', 56: 'freezing drizzle', 57: 'freezing drizzle',
  61: 'light rain', 63: 'rain', 65: 'heavy rain', 66: 'freezing rain', 67: 'freezing rain',
  71: 'light snow', 73: 'snow', 75: 'heavy snow', 77: 'snow grains',
  80: 'showers', 81: 'showers', 82: 'violent showers', 85: 'snow showers', 86: 'snow showers',
  95: 'thunderstorm', 96: 'thunderstorm, hail', 99: 'thunderstorm, hail',
}
const describe = (code: number) => SKY[code] ?? 'unknown sky'

const escapeXml = (text: string) =>
  text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
const width = (text: string, size: number, spacing = 0) => [...text].length * (size * ADVANCE + spacing)
const stripAnimation = (svg: string) =>
  svg.replace(/<animate(?:Transform)?\b[^>]*\/>/g, '').replace('/*A*/', '*{animation:none!important}')

const BILLBOARD_IDLE = 'CHUVA ÁCIDA · pH 4.1 · USE CAPA · '
const BILLBOARD_FONT = 26

function billboard(sky: Sky | null): string {
  const message = sky
    ? `${sky.city} · ${sky.temp}°C · ${describe(sky.code)} · humidity ${sky.humidity}% · `.toUpperCase()
    : BILLBOARD_IDLE
  const travel = width(message, BILLBOARD_FONT)
  return SCENE.replace('__BB__', escapeXml(message + message))
    .replace('__BBW__', travel.toFixed(1))
    .replace('__BBD__', Math.max(8, travel / 40).toFixed(1))
}

type Segment = { text: string; size: number; fill: string; weight?: number; spacing?: number; glow?: boolean; flicker?: boolean }

function ledSign(segments: Segment[]): string {
  const height = 52
  const pad = 18
  const gap = 26
  let x = pad + 14
  const body: string[] = [
    `<circle class="d" cx="${pad + 3}" cy="${height / 2}" r="3" fill="#cfa93f" filter="url(#g)"/>`,
  ]
  segments.forEach((s, i) => {
    if (i > 0) {
      body.push(`<rect x="${(x - gap / 2).toFixed(1)}" y="14" width="1" height="${height - 28}" fill="#3b3e44"/>`)
    }
    const attrs = [
      `x="${x.toFixed(1)}"`,
      `y="${(height / 2 + s.size * 0.36).toFixed(1)}"`,
      `font-size="${s.size}"`,
      `fill="${s.fill}"`,
      `font-weight="${s.weight ?? 400}"`,
      s.spacing ? `letter-spacing="${s.spacing}"` : '',
      s.glow ? 'filter="url(#g)"' : '',
      s.flicker ? 'class="f"' : '',
    ]
    body.push(`<text ${attrs.join(' ')}>${escapeXml(s.text)}</text>`)
    x += width(s.text, s.size, s.spacing ?? 0) + gap
  })
  const total = Math.ceil(x - gap + pad)
  return (
    `<svg xmlns="http://www.w3.org/2000/svg" width="${total}" height="${height}" viewBox="0 0 ${total} ${height}">` +
    '<style>.f{animation:f 11s steps(1) infinite}@keyframes f{0%,100%{opacity:1}1%{opacity:.25}2%{opacity:1}3%{opacity:.4}4%{opacity:1}}' +
    '.d{animation:d 1.6s steps(1) infinite}@keyframes d{50%{opacity:.15}}</style>' +
    '<defs><filter id="g" x="-30%" y="-60%" width="160%" height="220%"><feGaussianBlur stdDeviation="2.4" result="b"/>' +
    '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>' +
    '<pattern id="s" width="4" height="3" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" opacity=".35"/></pattern></defs>' +
    `<rect x=".5" y=".5" width="${total - 1}" height="${height - 1}" fill="#050506" stroke="#23252a"/>` +
    `<g font-family="${MONO}">${body.join('')}</g>` +
    `<rect width="${total}" height="${height}" fill="url(#s)"/></svg>`
  )
}

async function getJson($: any, url: string): Promise<any> {
  const res = await $.http.fetch(url, { headers: UA })
  if (!res.ok) throw new Error(`${url} answered ${res.status}`)
  return JSON.parse(res.text)
}

type Place = { city: string; lat: number; lon: number }
let place: Place | undefined
let timers: { cancel: () => void }[] = []

async function locate($: any): Promise<Place | undefined> {
  for (const url of LOCATORS) {
    try {
      const j = await getJson($, url)
      const lat = Number(j.latitude)
      const lon = Number(j.longitude)
      if (typeof j.city === 'string' && Number.isFinite(lat) && Number.isFinite(lon)) {
        return { city: j.city, lat, lon }
      }
    } catch {}
  }
  return undefined
}

async function forecast($: any, at: Place): Promise<Sky | undefined> {
  try {
    const j = await getJson(
      $,
      'https://api.open-meteo.com/v1/forecast' +
        `?latitude=${at.lat.toFixed(2)}&longitude=${at.lon.toFixed(2)}` +
        '&current=temperature_2m,relative_humidity_2m,weather_code&timezone=auto',
    )
    return {
      city: at.city,
      temp: Math.round(Number(j.current.temperature_2m)),
      humidity: Math.round(Number(j.current.relative_humidity_2m)),
      code: Number(j.current.weather_code),
      offsetSec: Number(j.utc_offset_seconds),
    }
  } catch {
    return undefined
  }
}

const pad2 = (v: number) => String(v).padStart(2, '0')

// The city's UTC offset from Open-Meteo makes this the city's time even when the
// machine runs in another zone; until weather arrives it is the machine's time.
function clock(nowMs: number, offsetSec?: number): string {
  if (offsetSec === undefined || !Number.isFinite(offsetSec)) {
    const d = new Date(nowMs)
    return `${pad2(d.getHours())}:${pad2(d.getMinutes())}`
  }
  const d = new Date(nowMs + offsetSec * 1000)
  return `${pad2(d.getUTCHours())}:${pad2(d.getUTCMinutes())}`
}

const sameSky = (a: Sky | null, b: Sky) =>
  a !== null && a.city === b.city && a.temp === b.temp && a.humidity === b.humidity && a.code === b.code && a.offsetSec === b.offsetSec

async function tick($: any) {
  const sky = await read($, skyAtom)
  const next = clock(await $.clock.now(), sky?.offsetSec)
  if ((await read($, timeAtom)) !== next) await update($, timeAtom, () => next)
}

async function refresh($: any, relocate: boolean) {
  if (relocate || !place) {
    place = (await locate($)) ?? place
    await update($, locatingAtom, () => (place ? 'done' : 'failed'))
  }
  if (place) {
    const fresh = await forecast($, place)
    if (fresh && !sameSky(await read($, skyAtom), fresh)) await update($, skyAtom, () => fresh)
  }
  await tick($)
}

function stopHud() {
  timers.forEach(t => t.cancel())
  timers = []
}

function startHud($: any) {
  stopHud()
  timers.push($.clock.every(CLOCK_MS, () => void tick($)))
  timers.push($.clock.every(WEATHER_MS, () => void refresh($, false)))
  timers.push($.clock.every(LOCATE_MS, () => void refresh($, true)))
  void refresh($, true)
}

// Engines up to 2.1.317 expose $.ui.backdrop only; 2.1.325+ replaced it with
// $.theme.set, which also repaints the app with a palette. Try the new one first.
async function apply($: any, mode: Mode, opacity: number): Promise<Result> {
  const glass = { ...GLASS, opacity }
  try {
    return await $.theme.set({ backdrop: { scene: SCENES[mode], glass }, colors: COLORS })
  } catch {
    try {
      return await $.ui.backdrop({ id: SCENES[mode], glass })
    } catch (err) {
      return { isDrawn: false, reason: String(err) }
    }
  }
}

async function remove($: any): Promise<void> {
  try {
    await $.theme.clear()
  } catch {
    try {
      await $.ui.backdrop(undefined)
    } catch {}
  }
}

const clampOpacity = (value: unknown) => {
  const n = Number(value)
  return Number.isFinite(n) ? Math.min(0.95, Math.max(0.1, n)) : DEFAULT_OPACITY
}

async function setOpacity($: any, value: number) {
  await update($, opacityAtom, () => value)
  await $.store.set('opacity', value)
  if (!(await read($, offAtom))) await apply($, await read($, modeAtom), value)
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'ipe',
      description: 'IPÊ theme: animated, still or off',
      argumentHint: 'on | still | off',
    })
    $.ui.status(undefined)
    const opacity = clampOpacity((await $.store.get('opacity')) ?? DEFAULT_OPACITY)
    await update($, opacityAtom, () => opacity)
    if (!(await read($, offAtom))) {
      await apply($, await read($, modeAtom), opacity)
      startHud($)
    }

    return next(e)
  })

  on('command.run', { command: 'ipe' }, async ($, e) => {
    const mode = e.args.trim().toLowerCase() || 'on'

    if (mode === 'off') {
      await remove($)
      stopHud()
      await update($, offAtom, () => true)

      return { text: 'IPÊ theme off. Run /ipe to bring it back.' }
    }

    if (mode !== 'on' && mode !== 'still') {
      return { text: 'Usage: /ipe on | still | off' }
    }

    await update($, modeAtom, () => mode)
    await update($, offAtom, () => false)
    const set = await apply($, mode, await read($, opacityAtom))
    if (timers.length === 0) startHud($)

    return {
      text: set.isDrawn
        ? `IPÊ theme on (${mode === 'still' ? 'still' : 'animated'} backdrop).`
        : `IPÊ theme set but not drawn: ${set.reason}`,
    }
  })

  on('ui.render', { component: 'Backdrop' }, async ($, e, next) => {
    const props = e.props as { plugin: string; id?: string; scene?: string }
    if (props.plugin !== PLUGIN) {
      return next(e)
    }

    const { Box, Svg } = $.ui.resolve(e) as unknown as {
      Box: (props: Record<string, unknown>) => JSX.Element
      Svg: (props: Record<string, unknown>) => JSX.Element
    }
    const svg = billboard(await read($, skyAtom))
    const scene = props.scene ?? props.id

    return (
      <Box
        width="100%"
        height="100%"
        overflow="hidden"
        flexDirection="column"
        justifyContent="flex-end"
        backgroundColor="#050506"
      >
        <Box flexShrink={0} width="100%">
          <Svg source={scene === SCENES.still ? stripAnimation(svg) : svg} alt={ALT} />
        </Box>
      </Box>
    )
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.props.hasSurvey || (await read($, offAtom))) {
      return next(e)
    }

    const sky = await read($, skyAtom)
    const time = (await read($, timeAtom)) || '--:--'
    const locating = await read($, locatingAtom)
    const city = sky?.city ?? (locating === 'failed' ? 'location unavailable' : 'locating…')
    const weather = sky ? `${sky.temp}°C ${describe(sky.code)}` : ''
    const humidity = sky ? `humidity ${sky.humidity}%` : ''
    const line = ['IPÊ/87', city, time, weather, humidity].filter(Boolean).join(' · ')

    if (e.surface === 'terminal') {
      const { Text } = $.ui.resolve(e)
      return <Text dimColor>{line}</Text>
    }

    const { Box, Svg, Text, Button } = $.ui.resolve(e) as unknown as {
      Box: (props: Record<string, unknown>) => JSX.Element
      Svg: (props: Record<string, unknown>) => JSX.Element
      Text: (props: Record<string, unknown>) => JSX.Element
      Button: (props: Record<string, unknown>) => JSX.Element
    }
    const opacity = await read($, opacityAtom)
    const segments: Segment[] = [
      { text: 'IPÊ/87', size: 11, fill: '#959aa1', spacing: 2 },
      { text: city.toUpperCase(), size: 20, fill: '#e9ecef', weight: 700, glow: true },
      { text: time, size: 24, fill: '#ffffff', weight: 700, glow: true, flicker: true },
    ]
    if (sky) {
      segments.push({ text: `${sky.temp}°C`, size: 20, fill: '#e9ecef', weight: 700, glow: true })
      segments.push({ text: describe(sky.code).toUpperCase(), size: 13, fill: '#b4b8be', spacing: 1.5 })
      segments.push({ text: `HUMIDITY ${sky.humidity}%`, size: 13, fill: '#b4b8be', spacing: 1.5 })
    }

    return (
      <Box
        width="100%"
        flexDirection="row"
        flexWrap="wrap"
        justifyContent="flex-end"
        alignItems="center"
        columnGap={2}
        rowGap={1}
      >
        <Box flexDirection="row" alignItems="center" columnGap={1}>
          <Text dimColor>CHAT</Text>
          {OPACITY_STEPS.map(step => (
            <Button
              key={`opacity-${Math.round(step * 100)}`}
              plain
              label={step <= opacity + 0.001 ? '▮' : '▯'}
              onPress={() => setOpacity($, step)}
            />
          ))}
          <Text dimColor>{`${Math.round(opacity * 100)}%`}</Text>
        </Box>
        <Svg source={ledSign(segments)} alt={line} />
      </Box>
    )
  })
}
