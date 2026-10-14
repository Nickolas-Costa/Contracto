# Contracto — working rules for this repository

Solve the whole problem with the least new code. The best code is the code
never written. The rules below take priority over everything else in this file.
End every reply with one or two lines: what you skipped or did not check, and
any risk the user must know.

## Before you write

Read the task and the code it touches. List every place your change must
reach: callers, tests, fixtures, config, exports. Check what your change
could break for users: data it would destroy or expose, callers that stop
working. That is scope. Extra features are not.

## The smallest complete change

Take the first option that fully works:

1. Does it need to exist? Skip features, options and flexibility nobody asked
   for, and name them in one line.
2. Already in this codebase (a helper, component, service, pattern)? Use it
   the way the surrounding code does.
3. Standard library or a platform feature? Use it, unless the project has its
   own. A house component beats a native widget.
4. An installed dependency? Use it. Never add a dependency for a few lines.
5. Can it be one line a reader gets at a glance? One line.
6. Otherwise: the minimum code that works.

- Be lazy about the solution, never about the change itself: finish every part
  the task needs, including the callers, tests and fixtures your change breaks.
- No abstraction, wrapper, type conversion, option, config, boilerplate or
  "for later" code nobody asked for. Keep values in the form the platform
  already gives you. Deletion beats addition. Keep the structure the codebase
  already has: its layers, interfaces and conventions.
- The shortest working diff wins, once you know everything it must touch.
  A one-liner that needs decoding is not short.
- Comment only the why the code cannot show, in one line.
- Bug fix: before you edit, grep every caller of the function you touch, then
  fix the root cause once in the shared code.
- Code you move or merge keeps its error handling and validation.
- Between options of equal size, take the one that is correct on edge cases.
- Lazy code without its check is unfinished: new non-trivial logic (a branch,
  a loop, a parser, money or security, or a whole new script or app) leaves one
  small test or an assert-based self-check. Trivial changes need none.
- A shortcut with a known limit gets a code comment in this form:
  `shortcut: <the limit>, <when to upgrade>`.

Never cut: validation at trust boundaries, error handling that prevents data
loss, security, accessibility, the calibration real hardware needs, anything
the user asked for.

## Repository context

Windows desktop app, Python, CustomTkinter; local API preparation and WebView
in progress. Before continuing the migration, read `docs/CONTINUIDADE_CODEX_WEB.md`,
`docs/SPEC_PRE_WEBVIEW.md`, `docs/ARCHITECTURE.md` and `docs/adr/`.

Latest state and pending items: `docs/BASE_UI_STATUS.md`. The local API, queue
and native bridge already exist; the production UI is still Tk. Do not restart
the old server-creation plan.

## Validation

-   Windows: `.venv/Scripts/python.exe -m unittest discover -s tests -v`.
-   Real smoke: `.venv/Scripts/python.exe tests/smoke_test_gui.py`.
-   Real WebView2: `.venv/Scripts/python.exe tests/smoke_webview.py`.
-   New UI journey, synthetic mass and checked PDFs: `.venv/Scripts/python.exe tests/smoke_webview_ui.py` (Windows; `--visible` keeps the window for review).
-   Real engines over HTTP (requires Word/GS): `.venv/Scripts/python.exe tests/smoke_api_engines.py`.
-   Linux with Tk/Xvfb: `xvfb-run -a .venv/bin/python -m unittest discover -s tests -v` and `xvfb-run -a .venv/bin/python tests/smoke_test_gui.py`.
-   Isolated backend: `python -m unittest discover -s tests -p test_headless_backend.py -v`.
-   Environment: `python -m pip check`. Install `requirements-dev.txt`; check the plan before using the Windows lock on Linux.

Use synthetic data and temporary directories; never change personal profiles/configuration in tests. Record skips and platform limitations. Word COM/WebView2/installer require Windows; the Linux suite does not certify them.

## Architectural limits

Keep services free of UI/Tk. The API at this stage is loopback, with an ephemeral token and authorized files, per the spec. Plain PDF is independent of Word/Ghostscript; RTF depends on Word and PDF/A on Ghostscript. No silent fallback. Every dependency change must answer the gate in `docs/DEPENDENCY_REVIEW.md`.

The ZIP prototype is ignored and not available in the remote checkout. Consult the versioned design documents and record the absence when doing visual work. Deliver focused changes with tests and explicit limitations.
