# FFREP public site

This repository is a public introduction, not the experiment implementation.

- Edit Korean prose in `content/ko.json`; keep sentences short, friendly and precise.
- Do not import private source files, training settings, tuning recipes, logs, checkpoints, access tokens, personal details, or internal document excerpts.
- Keep the distinctions between a connectivity-constrained software model, a living animal, and a complete biological reconstruction. Do not claim consciousness, suffering, biological equivalence, or unverified performance.
- Do not imply there is no engineering help; distinguish learning support from a finished external walking controller.
- Public diagrams are original conceptual illustrations, not data visualizations, live telemetry, real avatar meshes, or evidence of learned movement.
- Korean is the default. English is disabled until a reviewed complete translation exists. Do not expose a nonfunctional toggle as a finished translation.
- Keep all design corners square, thin structural lines, accessible contrast, responsive layouts, native FAQ details, keyboard support and reduced-motion support.
- No analytics, external fonts, third-party runtime dependencies, autoplay media, fake counters or hidden contact forms.
- Run `python scripts/build.py` and `python -m unittest discover -s tests -v`. Generated root `index.html` and `_site/` are ignored. Pages rebuilds from the canonical content on every push.
- Production bundle is `_site/`, built from an explicit public allowlist. Never deploy the repository wholesale if it later gains private work files.
