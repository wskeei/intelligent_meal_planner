# Meal Plan Chat-First Redesign Design

## 1. Background

`/meal-plan` is already the product's core workflow, but the current page still behaves like several different pages stacked together:

- A large hero section explains the feature before the user acts.
- The chat area competes with a persistent right rail.
- The status card and the "系统过程" card both occupy primary page real estate.
- The result overlay repeats context that is already present elsewhere.

This weakens the intended interaction model. The product should feel like a calm meal-planning conversation, not a dashboard with a chat embedded inside it.

The user feedback for this redesign is explicit:

- the page should be centered on chat
- the copy should be shorter and cleaner
- the "系统过程" area should stop creating awkward empty space when expanded
- the redesign must not break the core meal-chat flow

## 2. Goals and Non-Goals

### 2.1 Goals

- Make chat the dominant surface on `/meal-plan`.
- Reduce cognitive load by removing redundant copy and lowering visual competition.
- Keep session status visible, but allow the user to collapse or expand it on demand.
- Demote "系统过程" from a main-page content block to a secondary, optional surface.
- Preserve the current core behavior:
  - create or restore meal-chat session
  - send user messages
  - show current progress and missing information
  - trigger formal meal-plan generation
  - view final result
  - add generated meals to shopping list

### 2.2 Non-Goals

- No backend workflow change.
- No change to the meal-chat API contract unless a presentation field is needed for UI state persistence.
- No redesign of unrelated pages.
- No new analytics, recommendations, or extra feature surfaces.

## 3. Design Constraints

- The page must continue to work as a guided conversation-first flow for Chinese-speaking users.
- The layout must remain mobile-safe and avoid horizontal crowding.
- The interface should stay consistent with the established brand direction in `.impeccable.md`:
  - practical
  - calm
  - trustworthy
  - utility-first
- Any new UI state for collapsing status or opening process details must not interfere with the meal-chat session state.

## 4. Primary UX Direction

The approved direction is:

- desktop: chat-first layout with a narrow, optional status rail
- mobile: single-column chat-first layout
- status: user-controlled collapse/expand behavior
- system trace: removed from main-page prominence and treated as optional detail

This direction keeps the core workflow legible without stripping away necessary context.

## 5. Information Architecture

### 5.1 Main Page

The main page should be reduced to four layers:

1. Compact header
   - page title
   - one short status line
   - lightweight "new session" action

2. Main chat surface
   - message list
   - inline error handling
   - composer

3. Optional context rail or drawer
   - current phase
   - known key facts
   - missing items
   - primary next action
   - user can collapse it

4. Result entry point
   - visible only when generation is ready or a result exists
   - should feel like the next step, not a separate dashboard card

### 5.2 System Trace

"系统过程" should no longer be rendered as a full secondary card in the main page column layout.

Instead:

- main page: only a small secondary entry point such as "查看过程"
- result overlay: keep the detailed trace as a folded optional section
- if the user needs to inspect trace before result, use a compact drawer/panel that does not alter the main chat layout width

This directly removes the current expanded whitespace problem, which is caused by giving low-priority trace content a dedicated structural block in the page layout.

## 6. Layout Strategy

### 6.1 Desktop

Use a two-column shell only when there is enough width:

- primary column: chat card / chat panel
- secondary column: narrow status rail

The primary column should visually dominate. The secondary rail should be narrow enough to support the flow, not compete with it.

The hero section should be removed and replaced by a compact top bar so the conversation starts higher on the screen.

### 6.2 Mobile

Use a single-column layout:

- compact header
- collapsible status summary
- chat thread
- composer

Status details should expand inline or open as a bottom sheet style panel. The design must avoid side-by-side blocks on small screens.

## 7. Content Strategy

All page copy should be shortened.

### 7.1 Remove

- repeated explanations of the same workflow
- decorative subtitles that restate the heading
- long section intros
- duplicate action language between the rail and overlay

### 7.2 Keep

- the current next step
- what is missing
- whether the user can generate the final plan
- the result action when available

The rule is simple: every visible sentence must help the user decide what to do next.

## 8. Component Direction

### 8.1 `MealPlanView.vue`

This view should become the orchestration shell for:

- compact page header
- chat thread
- composer
- collapsible status container
- optional process entry
- generation and result overlay triggers

It should stop rendering the current large hero and separate persistent trace card.

### 8.2 `MealChatStatusPanel.vue`

This component should be simplified into a more compact context module.

It should support:

- collapsed summary mode
- expanded detail mode
- clear emphasis on the next action

The detailed lists can stay, but the component should be visually lighter and more concise.

### 8.3 `MealChatResultOverlay.vue`

The result overlay should remain the main result surface, but it should be simplified:

- shorter top copy
- clearer grouping of meals and actions
- trace stays folded and secondary

This preserves existing flow while making the main page lighter.

## 9. State Model

The redesign needs lightweight local presentation state, separate from backend meal-chat state:

- status panel visibility: expanded or collapsed
- process panel visibility if a drawer is used
- result overlay visibility

This state can remain frontend-local unless product requirements demand persistence across reloads. Persisting result overlay behavior through the existing presentation API can remain unchanged.

## 10. Functional Preservation Requirements

The redesign must preserve all of the following without regression:

- session bootstrap and restore
- optimistic message send behavior
- auth failure handling
- generation loading overlay
- result overlay open/close flow
- shopping list import
- restart session behavior
- locale-aware copy rendering

## 11. Acceptance Criteria

- A user can understand the page purpose within a few seconds: this is a meal-planning chat.
- The chat surface is visually dominant over all other elements.
- The status area can be collapsed by the user without losing access to the next action.
- "系统过程" no longer occupies a large dedicated content area on the main page.
- Expanding optional process details does not create a large blank zone in the surrounding layout.
- The page copy is materially shorter than the current version.
- Core generation and result behavior remain unchanged.

## 12. Risks and Mitigations

### Risk 1: removing too much context makes the workflow unclear

Mitigation:

- keep one compact summary line always visible
- keep expanded status accessible behind one obvious toggle

### Risk 2: simplifying the layout hides important actions

Mitigation:

- preserve one dominant CTA based on current state
- keep result and generation actions near the context summary

### Risk 3: refactor introduces state regressions

Mitigation:

- limit scope to presentation structure and related copy
- verify restored sessions, send flow, generate flow, and overlay flow manually after build
