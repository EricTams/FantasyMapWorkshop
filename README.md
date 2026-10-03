# Atlas — Fantasy Map Workshop

A static, browser-based fantasy map generator with seeded Pangea and island maps, terrain controls, resource sprites, and a world tour.

The live app source is in [`map-workshop/`](map-workshop/). Preserved historical source and art are in `Fantasy_Terrain_Codex/`; iteration snapshots are in `map-workshop/checkpoints/`.

## Develop

```sh
cd map-workshop
npm test
npm run build
npm run preview
```

Use Node.js 22+ for tests/build and Python 3 for the local preview server. There are no npm dependencies to install. Open `http://127.0.0.1:4174/` to preview the built site. `npm start` serves the source app on port 4173.

## Publish with GitHub Pages

1. Create or select a GitHub repository and add it as this checkout's `origin` remote. This preparation does not create a repository or push anything.
2. In that repository, open **Settings → Pages → Build and deployment → Source**, and choose **GitHub Actions**.
3. Push this repository's `main` branch. The workflow in [`.github/workflows/pages.yml`](.github/workflows/pages.yml) runs tests, builds the site, and deploys it. For an initial push made before enabling Pages, rerun the workflow from **Actions → Test and deploy Atlas to Pages → Run workflow**, on `main`.
4. Use the URL shown by the deployment job, usually `https://OWNER.github.io/REPOSITORY/`.

Pull requests run validation without deploying. Subsequent pushes to `main` update the site. Pages uses the normal `github-pages` environment and built-in GitHub token; no personal token or application secrets are needed.

The deploy artifact contains only app modules, styles, HTML visual studies, and the 35 image files loaded by the renderer. It is about 9.4 MiB. Checkpoints, original archives, unused experimental art, build scripts and unit tests are excluded. Those tracked source files and their history remain part of the Git repository when pushed; artifact exclusions do not remove them from repository history.

The site works at a project subpath or a custom-domain root. The generator runs entirely in the visitor's browser; PNG and JSON exports remain local downloads.

See [GitHub's custom Pages workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages) for repository setup and [the workshop notes](map-workshop/README.md) for rendering details and iteration history.
