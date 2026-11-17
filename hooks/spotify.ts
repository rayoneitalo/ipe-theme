// Optional Spotify link. It stays off unless scripts/spotify-login.py stored a
// client id and a refresh token in the macOS Keychain. Tokens leave the Keychain
// only into this module's memory, and only travel to Spotify over HTTPS.

export type Music = { title: string; artist: string; isPlaying: boolean }
export type SpotifyStatus = 'ready' | 'not-set-up' | 'unavailable'
export type Control = 'previous' | 'toggle' | 'next'

const SERVICE = 'ipe-theme-spotify'
const SECURITY = '/usr/bin/security'
const TOKEN_URL = 'https://accounts.spotify.com/api/token'
const PLAYER = 'https://api.spotify.com/v1/me/player'
const TOKEN_SHAPE = /^[A-Za-z0-9._~-]+$/
const CLIENT_ID_SHAPE = /^[0-9a-f]{32}$/

let access: { token: string; expiresAt: number; canControl: boolean } | undefined
let quietUntil = 0

type Read = { value?: string; isUnavailable?: boolean }

async function keychainRead($: any, account: string): Promise<Read> {
  try {
    const r = await $.process.run([SECURITY, 'find-generic-password', '-s', SERVICE, '-a', account, '-w'], {
      timeoutMs: 5000,
    })
    const value = String(r.stdout ?? '').trim()
    return r.exitCode === 0 && TOKEN_SHAPE.test(value) ? { value } : {}
  } catch {
    return { isUnavailable: true }
  }
}

// Written through security's interactive mode on stdin, so the token never
// shows in a process argument list that other local processes can read.
async function keychainWrite($: any, account: string, value: string): Promise<void> {
  if (!TOKEN_SHAPE.test(value)) return
  try {
    await $.process.run([SECURITY, '-i'], {
      stdin: `add-generic-password -U -s ${SERVICE} -a ${account} -w ${value}\n`,
      timeoutMs: 5000,
    })
  } catch {}
}

export async function status($: any): Promise<SpotifyStatus> {
  const id = await keychainRead($, 'client_id')
  if (id.isUnavailable) return 'unavailable'
  if (!id.value || !CLIENT_ID_SHAPE.test(id.value)) return 'not-set-up'
  const refresh = await keychainRead($, 'refresh_token')
  return refresh.value ? 'ready' : 'not-set-up'
}

async function token($: any): Promise<string | undefined> {
  const now = await $.clock.now()
  if (access && access.expiresAt - 60_000 > now) return access.token
  const clientId = (await keychainRead($, 'client_id')).value
  const refresh = (await keychainRead($, 'refresh_token')).value
  if (!clientId || !CLIENT_ID_SHAPE.test(clientId) || !refresh) return undefined
  const res = await $.http.fetch(TOKEN_URL, {
    method: 'POST',
    headers: { 'content-type': 'application/x-www-form-urlencoded' },
    body: `grant_type=refresh_token&refresh_token=${encodeURIComponent(refresh)}&client_id=${clientId}`,
  })
  if (!res.ok) {
    access = undefined
    return undefined
  }
  const j = JSON.parse(res.text)
  if (typeof j.access_token !== 'string') return undefined
  // Spotify may rotate the refresh token; the old one can stop working.
  if (typeof j.refresh_token === 'string' && j.refresh_token !== refresh) {
    await keychainWrite($, 'refresh_token', j.refresh_token)
  }
  access = {
    token: j.access_token,
    expiresAt: now + Number(j.expires_in ?? 3600) * 1000,
    canControl: String(j.scope ?? '').split(' ').includes('user-modify-playback-state'),
  }
  return access.token
}

export const canControl = () => access?.canControl ?? false

export function forget() {
  access = undefined
  quietUntil = 0
}

const clean = (text: unknown) =>
  String(text ?? '')
    .replace(/[\u0000-\u001f\u007f]/g, '')
    .trim()
    .slice(0, 60)

/** `undefined` keeps what is shown (a rate limit, a passing error); `null` shows nothing. */
export async function nowPlaying($: any): Promise<Music | null | undefined> {
  const now = await $.clock.now()
  if (now < quietUntil) return undefined
  const t = await token($)
  if (!t) return null
  const res = await $.http.fetch(`${PLAYER}/currently-playing?additional_types=episode`, {
    headers: { authorization: `Bearer ${t}` },
  })
  if (res.status === 204) return null
  if (res.status === 401) {
    access = undefined
    return undefined
  }
  if (res.status === 429) {
    quietUntil = now + Math.max(5, Number(res.headers['retry-after'] ?? 30)) * 1000
    return undefined
  }
  if (!res.ok) return undefined
  const j = JSON.parse(res.text)
  const item = j?.item
  if (!item) return null
  const artist =
    item.type === 'episode'
      ? item.show?.name
      : (item.artists ?? []).map((a: { name?: string }) => a?.name).filter(Boolean).join(', ')
  return { title: clean(item.name), artist: clean(artist), isPlaying: Boolean(j.is_playing) }
}

/** Resolves a line to show the person when Spotify refuses, else `undefined`. */
export async function control($: any, action: Control, isPlaying: boolean): Promise<string | undefined> {
  const t = await token($)
  if (!t) return 'Spotify is not connected. Run /ipe spotify for the setup steps.'
  const [method, path] =
    action === 'next'
      ? ['POST', 'next']
      : action === 'previous'
        ? ['POST', 'previous']
        : isPlaying
          ? ['PUT', 'pause']
          : ['PUT', 'play']
  const res = await $.http.fetch(`${PLAYER}/${path}`, { method, headers: { authorization: `Bearer ${t}` } })
  if (res.ok) return undefined
  if (res.status === 403) return 'Spotify Premium is needed to control playback.'
  if (res.status === 404) return 'No active Spotify device. Start playing on one first.'
  return `Spotify answered ${res.status}.`
}
