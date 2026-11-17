// Engines before 2.1.325 have no ThemeColors type, so the theme is typed loosely here.
export function makeColors(definition: {
  label: string
  id?: string
  only?: 'light' | 'dark'
  roles?: Record<string, string>
  light?: { gray?: { anchors?: Record<string, string> } }
  dark?: { gray?: { anchors?: Record<string, string> } }
}): { theme: { v: 1; label: string; inputs: Record<string, Record<string, string>> }; problems: string[] }

export function checkColors(colors: unknown): string[]
