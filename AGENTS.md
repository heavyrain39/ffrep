# FFREP public site

- This is a public FAQ, not the experiment implementation. Never import private training sources, tuning recipes, logs, checkpoints or access tokens.
- The author's Korean text in `content/ko.json` is canonical. Keep their voice and humor. Do not add poetic slogans, repeated rebuttals, long disclaimers or extra introduction sections.
- When the author supplies replacement copy, preserve their wording, punctuation and paragraph breaks. Do not silently soften opinions, rewrite analogies, add qualifications or omit questions. If a substantive correction seems necessary, explain it to the author and obtain approval before changing the prose. Link markup and media placeholders may be implemented without rewriting the sentences.
- Minimal layout: modest three-line project name, short introduction, actual video, 15 FAQ disclosures, two contact links.
- Do not restore search, filters, question-link copy, share buttons, generated diagrams or the website GitHub link.
- Footer links only to the approved portfolio and email.
- Use approved real project screenshots/videos and credited model reference imagery. Label past recordings with dates and training/evaluation context. Do not imply an illustration or old clip is current experimental evidence.
- Author-approved media: the original public SHOKI/YUMEKA clips, the credited Arka_X model image, and the official MaleCNS video embed. Keep `assets/media/sources.json` updated. Do not redistribute 3D model geometry.
- If attribution or the distinction between modeled neural dynamics and biological equivalence needs correction, discuss it before editing the author's prose. Keep their expressly personal speculation attributed to them rather than presenting it as a measurement.
- Korean default, English disabled until complete reviewed content exists. No fabricated finished translations.
- Square corners, thin neutral separators, restrained typography. Native keyboard-accessible details and video controls. No autoplay, analytics, external fonts, runtime libraries or fake telemetry.
- Build with `python scripts/build.py`; test with `python -m unittest discover -s tests -v`. Visually inspect desktop/mobile and native video playback when layout or media changes.
- `_site/` is the deployment allowlist; generated root `index.html` and `_site/` are ignored. Never deploy the whole repository.
