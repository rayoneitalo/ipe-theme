export type Sky = {
  city: string
  temp: number
  humidity: number
  code: number
  offsetSec: number
}

export type Locating = 'pending' | 'failed' | 'done'

declare module 'claude-code' {
  interface PluginState {
    'garoa-theme': {
      sky: Sky | null
      time: string
      isOff: boolean
      locating: Locating
      opacity: number
      mode: 'on' | 'still'
    }
  }
}
