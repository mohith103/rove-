/**
 * ROVE color palette and shared UI constants.
 * Centralizing hex codes means we can retheme the whole app in one place.
 */

export const colors = {
  // Backgrounds
  bg: '#0a0e14',
  surface: '#11151c',
  surface2: '#161b22',

  // Borders
  border: '#1f2937',
  borderFocus: '#2d3641',

  // Text
  text: '#e6edf3',
  textDim: '#7d8590',
  textMuted: '#4d5566',

  // Accents
  accent: '#4db8ff',     // cyan — headings, highlights
  accent2: '#1f6feb',    // blue — buttons, badges

  // Status
  success: '#3fb950',
  warning: '#d29922',
  danger: '#f85149',
} as const;

/** Gradient for resource bars based on value (0-100). */
export function resourceColor(value: number): string {
  if (value >= 60) return colors.success;
  if (value >= 30) return colors.warning;
  return colors.danger;
}

/** Common utility class strings. */
export const ui = {
  panel: 'bg-[#11151c] border border-[#1f2937] rounded-lg',
  panelTitle:
    'text-xs font-semibold text-[#4db8ff] uppercase tracking-wider mb-3',
  mono: 'font-mono',
} as const;