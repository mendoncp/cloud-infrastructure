# Cloud infrastructure learning path

A single-file, self-paced site tracking a 7-stage hands-on curriculum for developers learning cloud infrastructure. Progress is saved in your browser (`localStorage`) — no backend needed.

## Deploy on GitHub Pages

1. Create a new GitHub repository (public, or private if you have GitHub Pro/Team/Enterprise).
2. Add `index.html` to the root of the repo (drag-and-drop on github.com works, or `git add`/`commit`/`push` from your machine).
3. In the repo, go to **Settings → Pages**.
4. Under **Build and deployment → Source**, choose **Deploy from a branch**.
5. Under **Branch**, pick `main` and folder `/ (root)`, then **Save**.
6. Wait a minute or two, then your site will be live at:
   `https://<your-username>.github.io/<repo-name>/`

## Editing the content

All the curriculum content lives in the `STAGES` array near the bottom of `index.html` — each stage is a plain object with `title`, `diff`, `time`, `obj`, `task`, and a resource `link`. Add, remove, or reorder entries there; the pipeline diagram and progress bar update automatically to match however many stages are in the array.

## Notes

- Progress is stored per-browser, not synced anywhere — if you switch browsers or devices, progress won't carry over.
- If you preview this file directly inside Claude's chat interface, saved progress may not persist between sessions there; once deployed to GitHub Pages (or opened as a local file), it will.
