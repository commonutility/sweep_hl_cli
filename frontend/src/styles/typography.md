# Typography System Documentation

## Overview
This application uses a centralized typography system based on San Francisco (SF Pro) fonts with appropriate fallbacks for non-Apple devices.

## Font Families

### Sans-serif (Default)
```css
font-family: var(--font-sans);
```
Uses SF Pro on Apple devices with fallbacks to system fonts on other platforms.

### Monospace
```css
font-family: var(--font-mono);
```
Uses SF Mono on Apple devices with fallbacks to other monospace fonts.

### Serif
```css
font-family: var(--font-serif);
```
Uses New York on Apple devices with fallbacks to other serif fonts.

## Font Sizes
All font sizes are defined as CSS variables for consistency:

- `--font-size-xs`: 0.75rem (12px)
- `--font-size-sm`: 0.875rem (14px)
- `--font-size-base`: 1rem (16px) - Default
- `--font-size-lg`: 1.125rem (18px)
- `--font-size-xl`: 1.25rem (20px)
- `--font-size-2xl`: 1.5rem (24px)
- `--font-size-3xl`: 1.875rem (30px)
- `--font-size-4xl`: 2.25rem (36px)
- `--font-size-5xl`: 3rem (48px)

## Font Weights
SF Pro supports multiple weights:

- `--font-weight-thin`: 100
- `--font-weight-light`: 300
- `--font-weight-regular`: 400 (Default)
- `--font-weight-medium`: 500
- `--font-weight-semibold`: 600
- `--font-weight-bold`: 700
- `--font-weight-heavy`: 800
- `--font-weight-black`: 900

## Line Heights
- `--line-height-tight`: 1.1
- `--line-height-snug`: 1.375
- `--line-height-normal`: 1.5 (Default)
- `--line-height-relaxed`: 1.625
- `--line-height-loose`: 2

## Letter Spacing
- `--letter-spacing-tight`: -0.05em
- `--letter-spacing-normal`: 0 (Default)
- `--letter-spacing-wide`: 0.05em
- `--letter-spacing-wider`: 0.1em

## Usage Examples

### Basic Text
```css
.my-text {
  font-family: var(--font-sans);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-regular);
  line-height: var(--line-height-normal);
}
```

### Headings
```css
.my-heading {
  font-family: var(--font-sans);
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
  line-height: var(--line-height-tight);
  letter-spacing: var(--letter-spacing-tight);
}
```

### Code Blocks
```css
.my-code {
  font-family: var(--font-mono);
  font-size: var(--font-size-sm);
}
```

### Small Text
```css
.my-small-text {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-regular);
}
```

## Utility Classes

The typography system includes utility classes for quick styling:

### Font Families
- `.font-sans`
- `.font-mono`
- `.font-serif`

### Font Weights
- `.font-thin`
- `.font-light`
- `.font-regular`
- `.font-medium`
- `.font-semibold`
- `.font-bold`
- `.font-heavy`
- `.font-black`

### Text Sizes
- `.text-xs`
- `.text-small`
- `.text-large`

### Text Alignment
- `.text-left`
- `.text-center`
- `.text-right`
- `.text-justify`

### Text Transform
- `.uppercase`
- `.lowercase`
- `.capitalize`

### Line Heights
- `.leading-tight`
- `.leading-snug`
- `.leading-normal`
- `.leading-relaxed`
- `.leading-loose`

### Letter Spacing
- `.tracking-tight`
- `.tracking-normal`
- `.tracking-wide`
- `.tracking-wider`

### Special Classes
- `.tabular-nums` - For tabular numbers in data displays
- `.truncate` - For text truncation with ellipsis
- `.whitespace-nowrap` - Prevent text wrapping

## Best Practices

1. **Always use variables** - Never hardcode font values
2. **Semantic sizes** - Use appropriate sizes for headings, body text, etc.
3. **Consistent weights** - Stick to the defined weight scale
4. **Accessibility** - Ensure sufficient contrast and readable sizes
5. **Performance** - System fonts load instantly on Apple devices

## Responsive Typography

The system includes responsive adjustments:
- Base font size reduces slightly on mobile (15px)
- Heading sizes scale down appropriately
- Line heights remain consistent for readability

## Migration Guide

To update existing CSS:
1. Replace hardcoded `font-family` with `var(--font-sans)`
2. Replace pixel sizes with appropriate size variables
3. Use weight variables instead of numeric values
4. Apply utility classes where appropriate 