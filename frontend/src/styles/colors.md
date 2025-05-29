# Color System Documentation

## Overview
This application uses a centralized color system with CSS variables for consistent theming. The primary background is a dark grey (#0f0f0f) rather than pure black, providing a softer appearance while maintaining a dark theme.

## Background Colors

### Primary Backgrounds
- `--bg-primary`: #0f0f0f - Main background for all panels
- `--bg-secondary`: #1a1a1a - Secondary panels, elevated sections
- `--bg-tertiary`: #242424 - Higher elevation surfaces
- `--bg-quaternary`: #2a2a2a - Highest elevation

### Usage
```css
background-color: var(--bg-primary);
```

## Surface Colors
For interactive elements and overlays:
- `--surface-overlay`: rgba(255, 255, 255, 0.05)
- `--surface-hover`: rgba(255, 255, 255, 0.08)
- `--surface-active`: rgba(255, 255, 255, 0.12)
- `--surface-border`: rgba(255, 255, 255, 0.1)

## Text Colors
- `--text-primary`: #ffffff - Main text
- `--text-secondary`: #b3b3b3 - Secondary text
- `--text-tertiary`: #808080 - Muted text
- `--text-disabled`: #4d4d4d - Disabled state

## Brand Colors
- `--color-success`: #00ff88 - Success, buy orders, positive values
- `--color-danger`: #ff3366 - Danger, sell orders, negative values
- `--color-warning`: #ffaa00 - Warnings
- `--color-info`: #00bbff - Information

## Input & Button Colors
- `--input-bg`: #1a1a1a
- `--input-bg-hover`: #242424
- `--input-bg-focus`: #2a2a2a
- `--button-bg`: #1a1a1a
- `--button-bg-hover`: #242424

## Chart Colors
- `--chart-green`: #00ff88
- `--chart-red`: #ff3366
- `--chart-grid`: #333333
- `--chart-text`: #888888

## Shadow System
For elevation and depth:
- `--shadow-sm`: 0 1px 2px rgba(0, 0, 0, 0.5)
- `--shadow-md`: 0 4px 6px rgba(0, 0, 0, 0.5)
- `--shadow-lg`: 0 10px 15px rgba(0, 0, 0, 0.5)
- `--shadow-xl`: 0 20px 25px rgba(0, 0, 0, 0.5)

## Migration Guide

### Old Color → New Variable
- `#000000` → `var(--bg-primary)`
- `#0a0a0a` → `var(--bg-primary)`
- `#0f0f0f` → `var(--bg-primary)`
- `#1a1a1a` → `var(--bg-secondary)`
- `#222`, `#333` → `var(--bg-tertiary)`
- `#00ff88` → `var(--color-success)`
- `#ff3366` → `var(--color-danger)`

## Best Practices
1. Always use CSS variables instead of hardcoded colors
2. Use semantic color names (e.g., `--color-success` not `--green`)
3. For new colors, add them to the color system first
4. Maintain consistency across similar UI elements
5. Use appropriate color variants for different states (hover, active, etc.)

## Utility Classes
The color system provides utility classes for quick styling:
- `.bg-primary`, `.bg-secondary`, etc.
- `.text-primary`, `.text-secondary`, etc.
- `.text-success`, `.text-danger`, etc.
- `.shadow-sm`, `.shadow-md`, etc. 