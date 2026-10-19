# Security Policy

## Reporting a vulnerability

Please do not open a public issue for security vulnerabilities.

Report privately via GitHub Security Advisories:
<https://github.com/0xzerolight/anki_miner_note/security/advisories/new>

Anki Miner Note is maintained by a single person on a best-effort basis. You can expect an acknowledgement within a reasonable time.

## Scope

In scope:

- The card templates' scripts in `src/front.html` and `src/back.html`, Lapis's and the `amn-` additions alike: any way they turn field text into markup or script that the field itself did not contain.
- The release `.apkg`: what `build/genapkg.py` and the release workflow put into it.

Out of scope:

- Vulnerabilities in Anki, AnkiDroid, AnkiMobile or AnkiWeb, and in upstream [Lapis](https://github.com/donkuri/lapis).
- HTML or script placed in a field by whoever writes the note. Anki renders field HTML by design.

## Supported versions

The latest release on GitHub is supported. Older versions may receive critical patches at maintainer discretion.
