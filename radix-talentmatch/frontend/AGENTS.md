<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.
<!-- LOVABLE:END -->

- RADIX TalentMatch screens live in `src/radix/` (ported from a React Router app); `src/radix/router.tsx` maps the old `Link/useNavigate/useLocation` API onto TanStack Router — import from it inside `src/radix`, never add react-router-dom.
- `src/radix/services/api.ts` calls the FastAPI backend only when `VITE_API_BASE_URL` is set; otherwise `demo.ts` mirrors the backend heuristics in-browser so the preview works without Python.
- The visual system is CRED "Plinth" (tokens in `src/styles.css`, component layer in `src/radix/radix.css`); NeoPOP components need literal colours from `src/radix/lib/neo-theme.ts`. Elevation is reserved for primary actions and the hero.
