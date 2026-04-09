# METARMap 2.5 — Release & Installation Guide

## Directory Structure

This repo uses the standard Home Assistant custom integration layout:

```
custom_components/
└── metarmap25/
    ├── __init__.py
    ├── manifest.json
    ├── config_flow.py
    ├── const.py
    ├── sensor.py
    ├── binary_sensor.py
    └── metarmap25-card.js
```

HACS expects the `custom_components/<domain>/` folder at the repo root. This structure is correct and ready for HACS distribution.

---

## Creating a Release

### 1. Bump the version in `manifest.json`

Edit `custom_components/metarmap25/manifest.json` and increment the `version` field following [semantic versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`):

```json
"version": "1.0.1"
```

### 2. Commit the version bump

```bash
git add custom_components/metarmap25/manifest.json
git commit -m "Bump version to 1.0.1"
git push origin main
```

### 3. Create a Git tag

The tag must match the version in `manifest.json` exactly:

```bash
git tag 1.0.1
git push origin 1.0.1
```

### 4. Create a GitHub Release

1. Go to the repo on GitHub
2. Click **Releases** → **Draft a new release**
3. **Choose a tag** → select `1.0.1`
4. Set the **Release title** to `v1.0.1` (or a short description)
5. Write release notes describing what changed
6. Click **Publish release**

HACS will detect the new release and notify users who have the integration installed.

---

## Installing via HACS (Custom Repository)

Since this integration is not yet in the HACS default store, users install it as a custom repository:

### Prerequisites
- [HACS](https://hacs.xyz/docs/use/download/download/) installed in Home Assistant

### Steps

1. In Home Assistant, go to **HACS** → **Integrations**
2. Click the **⋮** menu (top right) → **Custom repositories**
3. Enter the repository URL:
   ```
   https://github.com/Birdheezy/METARMap2.5-ha
   ```
4. Set **Category** to `Integration`
5. Click **Add**
6. Search for **METARMap 2.5** in HACS → click **Download**
7. Restart Home Assistant
8. Go to **Settings** → **Devices & Services** → **Add Integration** → search **METARMap 2.5**
9. Enter your METARMap's local IP address when prompted

---

## Updating an Existing Installation

When a new release is published:

1. In Home Assistant, go to **HACS** → **Integrations**
2. Find **METARMap 2.5** — it will show a pending update badge
3. Click **Update**
4. Restart Home Assistant

---

## Release Checklist

- [ ] Version bumped in `manifest.json`
- [ ] Changes committed and pushed to `main`
- [ ] Git tag created and pushed (matching version string exactly)
- [ ] GitHub Release published with release notes
