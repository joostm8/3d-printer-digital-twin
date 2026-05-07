# Cookbook selector for digital twin scaffolding

## How to use this router

When a user asks to scaffold a digital twin or monitoring backend, follow these steps:

### Step 1 — Identify the domain

Read `cookbooks/registry.yaml` to see available domains.

Ask the user in plain language what they want to build. Match their answer to a domain:
- 3D printer, print farm, FDM printer, filament printer → domain: 3d-printer
- Brewery, fermentation, homebrewing → domain: beer-brewing
- If unclear, list the available domains from registry.yaml and ask.

### Step 2 — Load the domain skill

Once domain is known, read the `instructions` file listed in registry.yaml for that domain.
Follow all steps in that file to determine use case, flavor, and broker.

### Step 3 — Handle cross-domain or combined recipes

If the user wants to combine multiple domains or extend a recipe with a simulation sidecar,
refer them to `cookbooks/combined/`. Each combined recipe is a compose file that uses
Docker Compose `include:` to pull in ingredients from multiple domain folders.

### General rules
- Always keep generated run commands explicit and copy-paste ready.
- Prefer beginner-friendly language. Avoid raw flavor IDs unless the user is clearly technical.
- Recommend a default whenever the user is unsure.
- If a domain or use case is not yet scaffolded, say so clearly and point to registry.yaml
  as the place to register new domains.