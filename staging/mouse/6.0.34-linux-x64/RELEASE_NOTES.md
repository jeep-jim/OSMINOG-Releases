# Mouse Browser 6.0.34 — Linux x64

Visual search and the desktop fixes requested for this release are included below.

- Mouse now includes visual search. The magnifying glass immediately to the left of the smiley opens a temporary search workspace: live website tiles in a scrolling masonry grid on the left, and a search field, Mouse mascot and AI conversation on the right.
- Search supports All, Videos, Products and Articles, additional result pages, and product prices when the source supplies them. Visible sites open as real pages; choosing Open opens a result in a regular browser tab. Closing search returns to the original desktop.
- The AI summary and follow-up conversation use the returned search results. Show screen is an explicit option for one selected visible site: it supplies structured page elements and clicks for a question, without screenshots or field values, and stops when the site changes or search closes.
- The unsolicited settings icon is removed from Nora's desktop header. Opening Nora darkens the workspace behind it more strongly in both themes while retaining the existing animation.
- Downloads use a green bottom widget in their originating pane, reserve 16 px plus 6 px, and restore that pane when the transfer finishes. Independent panes keep their own progress.
- Completed unread downloads retain a green footer badge.
- Links from the right AI chat open a lower preview in the same column; the original chat and main tabs stay in place.
- Browser screenshots preserve 12 px rounded corners and the regular 6 px pane gaps.
- Expanded main/AI panes touch the footer with square bottom corners; regular layout and upper corners retain their spacing and rounding.
- The footer shares the upper toolbar background in both themes, including with Nora open.
- Browser toolbars and pane controls use fewer background-blur effects while retaining their colors and layout.

Existing Settings, Agent, live zoom, selected-file imports, native context menus, read-only documents, hidden-scrollbar input and page preservation are covered by the installed release checks.

## Search service verification and limits

The [external service check on 21 November 2026](https://github.com/jeep-jim/OSMINOG/actions/runs/44797452740/attempts/2) passed real first-page and second-page search, video results and a model reply citing a supplied search result. Earlier intermittent HTTP 502 responses did not recur in that check; their cause has not been established or proven fixed. A service failure is shown as an error and does not replace the found websites with a fabricated answer.
