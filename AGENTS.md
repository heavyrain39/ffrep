# FFREP public site

- This is a public FAQ, not the experiment implementation. Never import private training sources, tuning recipes, logs, checkpoints or access tokens.
- The author's Korean text in `content/ko.json` is canonical. Keep their voice and humor. Do not add poetic slogans, repeated rebuttals, long disclaimers or extra introduction sections.
- Minimal layout: modest three-line project name, short introduction, actual video, 13 FAQ disclosures, two contact links.
- Do not restore search, filters, question-link copy, share buttons, generated diagrams or the website GitHub link.
- Footer links only to the approved portfolio and email.
- Use approved real project screenshots/videos and credited model reference imagery. Label past recordings with dates and training/evaluation context. Do not imply an illustration or old clip is current experimental evidence.
- Author-approved media: the original public SHOKI/YUMEKA clips, the credited Arka_X model image, and the official MaleCNS video embed. Keep `assets/media/sources.json` updated. Do not redistribute 3D model geometry.
- Correct attribution and separate modeled neural dynamics from biological equivalence. Preserve personal speculation as speculation rather than measured fact.
- Korean default, English disabled until complete reviewed content exists. No fabricated finished translations.
- Square corners, thin neutral separators, restrained typography. Native keyboard-accessible details and video controls. No autoplay, analytics, external fonts, runtime libraries or fake telemetry.
- Build with `python scripts/build.py`; test with `python -m unittest discover -s tests -v`. Visually inspect desktop/mobile and native video playback.
- `_site/` is the deployment allowlist; generated root `index.html` and `_site/` are ignored. Never deploy the whole repository.
