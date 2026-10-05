---
name: Eligibility Judge
description: A public rulebook ledger for inspecting qualification evidence.
colors:
  paper: "#f7f8f4"
  white: "#fff"
  ink: "#182b25"
  muted: "#5d6d65"
  line: "#dce2d9"
  green: "#285f43"
  green-light: "#e5efdf"
  green-hover: "#1c4933"
  red: "#973b35"
  red-light: "#f9eae5"
  amber: "#775219"
  amber-light: "#f4efdc"
  neutral: "#edf0e9"
  ledger-header: "#f0f3ec"
  source-strip: "#eef3e9"
  expanded-row: "#fafbf7"
  evidence-surface: "#fbfcf9"
typography:
  display:
    fontFamily: "Space Grotesk, sans-serif"
    fontSize: "clamp(48px, 5.4vw, 76px)"
    fontWeight: 500
    lineHeight: 1.04
    letterSpacing: "-0.04em"
  headline:
    fontFamily: "Space Grotesk, sans-serif"
    fontSize: "21px"
    fontWeight: 500
    letterSpacing: "-0.5px"
  title:
    fontFamily: "Space Grotesk, sans-serif"
    fontSize: "20px"
    fontWeight: 500
    letterSpacing: "-0.5px"
  body:
    fontFamily: "DM Sans, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "DM Sans, sans-serif"
    fontSize: "12px"
    fontWeight: 600
    lineHeight: 1.5
  code:
    fontFamily: "monospace"
    fontSize: "12px"
    lineHeight: 1.5
rounded:
  stamp: "4px"
  status: "5px"
  control: "6px"
  wallet: "7px"
  panel: "8px"
  ledger: "10px"
  challenge: "12px"
spacing:
  compact: "4px"
  control-gap: "8px"
  small: "12px"
  inset: "16px"
  panel: "20px"
  ledger: "24px"
  evidence: "30px"
  section: "40px"
  desktop-gutter: "64px"
components:
  button-primary:
    backgroundColor: "{colors.green}"
    textColor: "{colors.white}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "11px 15px"
  button-primary-hover:
    backgroundColor: "{colors.green-hover}"
  button-secondary:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "11px 15px"
  button-secondary-hover:
    backgroundColor: "{colors.green-light}"
  button-text:
    textColor: "{colors.green}"
    typography: "{typography.label}"
    padding: "0"
  input:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "12px 13px"
    width: "100%"
  navigation:
    textColor: "{colors.muted}"
    padding: "15px 0"
  status-good:
    backgroundColor: "{colors.green-light}"
    textColor: "{colors.green}"
    rounded: "{rounded.status}"
    padding: "5px 9px"
  status-bad:
    backgroundColor: "{colors.red-light}"
    textColor: "{colors.red}"
    rounded: "{rounded.status}"
    padding: "5px 9px"
  status-unknown:
    backgroundColor: "{colors.amber-light}"
    textColor: "{colors.amber}"
    rounded: "{rounded.status}"
    padding: "5px 9px"
  status-neutral:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.muted}"
    rounded: "{rounded.status}"
    padding: "5px 9px"
  rule-chip:
    backgroundColor: "{colors.green-light}"
    textColor: "{colors.green}"
    rounded: "{rounded.control}"
    width: "30px"
    height: "30px"
  ledger:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.ledger}"
  evidence:
    backgroundColor: "{colors.evidence-surface}"
    textColor: "{colors.ink}"
    padding: "22px 30px 22px 70px"
  payout-equation:
    backgroundColor: "{colors.green-light}"
    textColor: "{colors.ink}"
    rounded: "{rounded.ledger}"
    padding: "30px"
---

# Design System: Eligibility Judge

## Overview

**Creative North Star: "Rulebook ledger"**

The implemented world is a community workshop acceptance ledger: quiet paper, forest ink, ordered rule cells and compact outcome stamps. Space Grotesk gives headings a precise, open character; DM Sans keeps the controls and evidence readable. The visual emphasis belongs to repository identity, rule status and the quoted passage.

The same restrained shell holds the rulebook, entry forms, transaction trail and payout arithmetic. Evidence opens within its entry rather than moving the reader to another surface. The system uses flat surfaces, fine dividers and restrained tonal changes; icons are inline vector strokes. It ships no raster imagery.

This is a scan of `app/globals.css`, `app/judge-app.tsx` and `app/layout.tsx`, with the established direction in `docs/DIRECTION.md`. CSS and markup take precedence over intended prose. It records visual implementation, not a claim that chain completion or browser signing has been verified.

**Key Characteristics:**

- Paper surfaces and forest-green actions.
- Ordered rule cells with text and symbol support for every status.
- Inline, commit-specific evidence with readable quotations.
- Flat borders and tonal layering, with one small selection shadow.
- A compact desktop ledger that rearranges on mobile.

## Colors

The palette is subdued and functional: the normative values are in the frontmatter, using the source CSS's exact color strings. Sidecar tonal ramps are synthesized preview aids, not additional source tokens.

### Primary

- **Forest green** (`green`): primary actions, links, rule identifiers and positive symbols. **Forest hover** (`green-hover`) darkens enabled primary actions.
- **Pale leaf** (`green-light`): positive status backgrounds, challenge surfaces, the frozen-rulebook seal and payout arithmetic.

### Secondary

- **Brick red** (`red`) with **pale brick** (`red-light`): failed rules, disqualified outcomes and error notices.
- **Amber ink** (`amber`) with **pale amber** (`amber-light`): insufficient evidence and warning copy. Amber is a state color, not a promotional accent.

### Neutral

- **Warm paper** (`paper`): the page canvas. **White** (`white`): the ledger, fields and secondary buttons.
- **Forest ink** (`ink`): main text and the selected-rule outline. **Muted ink** (`muted`): secondary descriptions and metadata.
- **Fine divider** (`line`): section rules, row separators and input strokes. **Neutral stamp** (`neutral`): pending outcomes, avatars and count badges.
- **Ledger header** (`ledger-header`): column headers and quotation blocks. **Source strip** (`source-strip`): proof provenance.
- **Expanded row** (`expanded-row`) and **evidence surface** (`evidence-surface`): subtle separation between an entry and its open citation.

**The Status Meaning Rule.** Keep pass, fail, insufficient and pending colors paired with the implemented symbols or text labels. Color alone does not convey the outcome.

## Typography

**Display Font:** Space Grotesk, with sans-serif fallback.

**Body Font:** DM Sans, with sans-serif fallback.

**Code Font:** browser monospace; the project imports no custom monospace face. The actual repository metadata uses DM Sans with tabular numerals; code elements hold hashes and paths.

The layout imports DM Sans in weights 400, 500 and 600 and Space Grotesk in weights 500 and 700. Headings are balanced where specified; tight tracking gives the large title its distinctive silhouette. Controls and supporting prose use smaller sans-serif text.

### Hierarchy

- **Display:** the main title uses the frontmatter's fluid size. At the tablet breakpoint it becomes fixed at 62px; mobile uses 53px.
- **Headline:** challenge titles use the headline role. The tablet and mobile sizes are 18px and 17px respectively; mobile sets line height to 1.3.
- **Title:** section headings use the title role, becoming 18px on mobile. Brand lettering uses Space Grotesk at weight 700.
- **Body:** the global body uses the body role. The introductory description uses 15px with line height 1.7; much supporting copy uses 12px. Evidence descriptions and quotations are constrained to 75ch.
- **Label:** action and form labels use the label role. Status stamps are 11px at weight 600; column labels are 10px. Mobile repository names and evidence rule headings are 13px, metadata and entry verdicts are 11px, and evidence descriptions and quotations are 14px with line height 1.6. These are the final overrides in the stylesheet.
- **Code:** tabular numerals and wrapping preserve readable fingerprints. Smaller code appears in seals, preview files and evidence details.

## Layout

The centered shell has a maximum width of 1440px, changing to 1380px at a minimum viewport width of 1600px. Desktop content, masthead and footer use 64px side gutters. Gutters become 32px at 1000px and 20px at 680px. The masthead is 86px tall, becoming 72px on mobile. The introduction is a two-sided flex composition that stacks on mobile.

The desktop ledger aligns repository identity, ordered rule cells, verdict and expand control. Columns are `minmax(250px,1fr) minmax(150px,240px) 160px 20px`, with a 22px gap and 24px horizontal inset. At 1000px this becomes `minmax(200px,1fr) 180px 125px 18px`, with a 15px gap and 16px inset.

At 680px the final mobile grid is `minmax(110px,1fr) calc(var(--rule-count,4)*27px) 15px`. The rule count is set from the real challenge; chips do not shrink. The repository avatar disappears, the verdict moves beneath the repository identity, and rows reserve bottom space for it. Tabs scroll horizontally. Evidence padding becomes 18px 12px; its header stacks. Form columns and inline fields stack; proof links and footer wrap.

Rulebook and payout content cap at 860px, forms at 740px. Shared spacing is compact within controls and more generous around sections. No general spacing scale exists in source; the frontmatter names the recurring observed increments for reuse.

**The Ledger Alignment Rule.** Preserve ordered rule columns and the repository identity on each row. On small screens, move the outcome beneath the identity and size the rule region from the actual rule count.

## Elevation & Depth

Depth comes from tonal surfaces and fine borders. Cards and ledger rows are flat. The active proof-source control is the only component with a box shadow: `0 1px 3px #23362312`. Evidence is distinguished through its pale surface and top divider, rather than a floating panel.

**The Flat Surface Rule.** Use the existing surface tones and dividers for structural depth. Keep the small selection shadow specific to the proof-source toggle.

## Shapes

Corners are gently curved and proportional to their role: compact stamps, controls, small panels and larger ledger or challenge surfaces use the frontmatter's radius vocabulary. The challenge header and provenance strip share a joined silhouette: the top header owns the upper corners and the strip owns the lower corners. Rule chips are square on desktop, narrower and slightly taller on mobile. Status dots are circular.

Forms and ledger containers use a single fine border. The ledger clips its header and row surfaces to its rounded boundary. Paths, hashes and quotation blocks wrap; their content is not treated as decorative texture.

## Components

### Buttons

Actions are compact and confident. Primary buttons use forest green and white; secondary buttons use white, ink and a divider border. Both use the control radius, label typography, a minimum height of 40px and the frontmatter's padding. Small variants use 7px 11px padding, 11px type and a minimum height of 32px. Enabled primary hover uses forest hover; secondary hover uses pale leaf. Text buttons have no filled background, use forest ink and underline on hover.

The wallet button is a separate compact outlined control with 10px 14px padding and wallet-radius corners; its mobile padding and type shrink. Disabled buttons retain their variant with opacity .46 and a not-allowed cursor. Buttons, links, inputs, textareas, selects and summaries share a green 2px focus-visible outline with 4px offset. General buttons have no animated hover transition.

### Chips and status stamps

Rule chips are interactive cells, not ranking scores. Their background and foreground follow the pass, fail, insufficient or pending pair; the content is a check, cross, question mark, dash or pending spinner. Desktop chips use a 30px square. Mobile chips use 24px by 27px with 4px corners. Hover shifts the chip up 2px and adds a current-color outline. An expanded chip has a 2px ink outline with 3px offset, and the markup exposes its evidence region through `aria-expanded` and `aria-controls`.

Status stamps are inline, compact and unwrapped, with a 6px icon gap. Entry verdicts have a smaller stamp geometry and move below repository identity on mobile. Informational states always keep their visible names.

### Cards / Containers

The bordered white ledger is the canonical container. A muted header introduces the ordered rules, and fine separators divide entries. Challenge, seal, preview and payout containers use tonal fills rather than shadows. Notice and error messages use the matching state color pair and wrap long text. There is no generic floating card grid.

### Inputs / Fields

Inputs and textareas are white, outlined, full-width controls with the frontmatter's input padding and control radius. Field labels are stacked with an 8px gap. Textareas resize vertically. Fields use a green caret and the shared focus-visible outline. Placeholders are muted green-gray. Input errors are expressed through the existing message treatment and native constraints; the stylesheet defines no separate invalid-field visual variant.

### Navigation

Tabs are plain text controls above a divider, with counts in small neutral badges. The selected tab uses ink, a 2px green underline and a leaf-toned count badge; hover uses green. Mobile preserves a horizontal scrolling strip rather than replacing it with a menu. The proof-source toggle has a white active segment and the small selection shadow. It remains visually distinct from the content tabs.

### Inline evidence

A rule chip opens the relevant evidence inside its repository row. The panel contains a pinned-commit heading, a rule identifier, the explanation, a wrapped quotation, a file link and optional evidence fingerprint details. Desktop reveals the panel using a .23s clip-path animation with `cubic-bezier(.16,1,.3,1)`. Chip hover uses .18s ease. Pending indicators rotate over 1.2s linearly. The reduced-motion media query disables all animations and transitions.

### Payout arithmetic

The payout surface is a pale-leaf arithmetic row: pool, division symbol, qualifiers, equals sign and each share. Values use Space Grotesk at 32px and weight 500 with tabular numerals, shrinking to 24px on mobile. Payment rows, state stamps and refund lines continue the ledger's divider rhythm.

## Do's and Don'ts

### Do:

- **Do** use the extracted paper, forest ink and semantic status pairs.
- **Do** preserve ordered rule identifiers across the ledger, evidence and editor.
- **Do** pair status colors with readable names or the existing symbols.
- **Do** keep evidence inline, wrap long paths and respect the mobile evidence type overrides.
- **Do** carry the shared focus-visible outline and reduced-motion behavior into new controls.

### Don't:

- **Don't** replace the ledger with ranked cards or decorative score charts.
- **Don't** add floating shadows to the flat container system.
- **Don't** shrink rule chips to fit a fixed four-rule mobile column.
- **Don't** present pending, insufficient or unverified states as successful outcomes.
- **Don't** promote these extracted styles into claims of completed chain proof or verified wallet signing.
