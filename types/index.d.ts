export type Sky = {
  city: string
  temp: number
  humidity: number
  code: number
  offsetSec: number
}

export type Locating = 'pending' | 'failed' | 'done'

export type Music = { title: string; artist: string; isPlaying: boolean }

declare module 'claude-code' {
  interface PluginState {
    'ipe-theme': {
      sky: Sky | null
      time: string
      isOff: boolean
      locating: Locating
      opacity: number
      mode: 'on' | 'still'
      music: Music | null
      canControl: boolean
      isRaining: boolean
    }
  }
}
