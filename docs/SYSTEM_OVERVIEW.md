# System Overview

## Roles

- `Pantheon` is the operating system and intelligence layer.
- `Apollo` is the interface, voice, and delivery shell.
- `BlackBook` is the financial and operational source of truth.
- `Maridian` is the reflective and cognitive source material.

## Current Repo Mapping

- `apps/apollo`
  Contains the existing Apollo backend, UI, connectors, and the new `pantheon/` package that now routes reasoning behind Apollo.
- `apps/blackbook`
  Contains the BlackBook Reflex app and database/query logic.
- `apps/maridian`
  Contains Maridian code only. Private vault content and derived personal data are intentionally excluded from Git.

## What Is Not Here Yet

- `Olympus`
  The live source of truth is on the PC, so it will be added later from that machine rather than copied from laptop Dropbox.

## Current Direction

The immediate direction is:

1. keep Apollo as the visible product
2. continue moving intelligence responsibilities into Pantheon
3. run the local model stack on the PC
4. add Olympus from the PC once the runtime machine becomes the primary host

