# Design

Vite is the correct tool here because the generated outputs are browser-native HTML plus TypeScript entry files. Vite can serve those directly without introducing a framework or a documentation system.

This change does not convert the repository into a frontend application. It only adds:

- a pinned Vite dev dependency
- a small Python CLI that resolves generated roots and site roots
- a stable operator workflow for local inspection

VitePress is intentionally not used because this is not a docs-site authoring problem.
