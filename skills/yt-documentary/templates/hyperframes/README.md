# Reusable documentary graphics

These are editable HyperFrames composition blocks adapted from the project's
documentary graphics. Copy only the block needed into a HyperFrames project's
`compositions/` directory, then mount it on an appropriate graphics track.
They use no project-specific walrus copy, footage, font files, external
scripts or GSAP dependency.

| Template | Use |
| --- | --- |
| `statistic-card.html` | One sourced number, unit and short explanation; optional proportional bar |
| `keyword-callout.html` | A short emphasis phrase or red stamp, positioned over relevant footage |
| `source-credit.html` | Plain-text media/source credit at the bottom of frame |

Example host for the statistic card:

```html
<div
  id="stat-weight"
  data-composition-id="doc-statistic-card"
  data-composition-src="compositions/statistic-card.html"
  data-start="12"
  data-duration="8"
  data-track-index="2"
  data-track-kind="graphics"
  data-width="1920"
  data-height="1080"
  data-variable-values='{"value":"120","unit":"kg","label":"Measured quantity","caption":"Short context","source":"Source, page 4","direction":"ltr"}'
></div>
```

Give each host a unique HTML `id`. Change its start and duration to match the
spoken beat; if changing a block's own duration, keep the root and inner
`class="clip"` durations in its file aligned. `data-variable-values` overrides
the defaults declared by the block. The `scalePercent` bar is optional and
should be enabled only when its denominator and comparison are supported by a
source.

The blocks default to the documentary's cobalt/navy grid style and 16:9,
1920x1080 dimensions. They can be used in other projects by changing their
CSS custom properties, text direction, dimensions and positioning to match
that project's brand and canvas. The default typeface uses Arial/system
fallbacks; for consistent Arabic typography across local and cloud renders,
add a licensed local font with `@font-face` in the block. Keep key content
inside the project's safe area. The statistic card is a panel, so use it only when a quantity or
comparison benefits from one; do not cover important evidence. Keep source
credits as plain text and separate media attribution from scientific support.

These are starting templates, not evidence: replace sample values and credits,
verify factual claims, and inspect every mounted block in the target project.
Run `npx hyperframes check --json` and snapshot the relevant scenes after
adding or adapting them.
