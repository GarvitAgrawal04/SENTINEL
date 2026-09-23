# Publishing Sentinel to VS Code Marketplace & OpenVSX

Sentinel is designed for developers using modern AI-first IDEs. Cursor and Windsurf (and VSCodium) use the **OpenVSX** registry (`open-vsx.org`), while Visual Studio Code uses the Microsoft VS Code Marketplace.

## Prerequisites

- Node.js 18+
- VSCE CLI: `npm install -g @vscode/vsce`
- OVSX CLI: `npm install -g ovsx`
- Access tokens:
  - VS Code Marketplace: Personal Access Token (PAT) from Azure DevOps (Marketplace: Manage).
  - OpenVSX: Access Token from `https://open-vsx.org/user-settings/tokens`.

## Packaging Locally

To build the `.vsix` package:

```bash
cd vscode-extension
npx @vscode/vsce package --no-dependencies
```

This generates `sentinel-md-<version>.vsix`.

## Publishing to OpenVSX (Cursor & Windsurf)

OpenVSX is essential because Cursor, Windsurf, and open-source VS Code distributions pull extensions from `open-vsx.org`, not Microsoft Marketplace:

```bash
ovsx publish sentinel-md-<version>.vsix -p <OPENVSX_TOKEN>
```

Or via namespace claiming:
1. Register namespace `sentinel` at `https://open-vsx.org/namespaces/sentinel`.
2. Link your GitHub organization or account.
3. Publish using `ovsx`.

## Publishing to VS Code Marketplace

```bash
vsce publish -p <VSCE_PAT>
```

## Automated Publishing via GitHub Actions

See `.github/workflows/publish-extension.yml` for automated releases on tag creation.
