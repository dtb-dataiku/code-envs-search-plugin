# Code Environment Search Plugin

> **Dataiku DSS Plugin** · `v0.0.1` · Apache 2.0 License

A Dataiku DSS plugin that lets users search for Python and R packages across all code environments available on an instance — directly from a webapp inside DSS. No more opening a terminal or asking an admin which environment has `scikit-learn 1.4` installed.

---

## Why This Exists

Dataiku instances in production often accumulate many code environments — different Python versions, different package sets, project-specific environments, and shared platform environments. Finding which environment has the package (and version) you need typically means:

- Digging through the **Administration > Code Envs** panel one by one, or
- Asking a DSS admin, or
- Just creating yet another environment

This plugin solves that with a searchable webapp interface backed by the Dataiku Python API.

---

## Features

- 🔍 Search packages by name across **all Python and R code environments** on the instance
- 📦 See installed package versions per environment
- 🌐 Accessible as a **Dataiku webapp** — no terminal or admin access required for users
- 🔌 Includes a **Python connector** to expose environment/package data as a DSS dataset

---

## Plugin Structure

```
code-envs-search-plugin/
├── plugin.json                                  # Plugin metadata
├── code-env/
│   └── python/                                  # Plugin's own managed code environment
├── python-lib/
│   └── codeenvssearch/                          # Shared Python library used by components
├── python-connectors/
│   └── code-envs-search_dataset-code-envs/      # Dataset connector: lists code envs
│   └── code-envs-search_dataset-packages/       # Dataset connector: lists packages
└── webapps/
    └── webapp-search-code-envs/                 # Interactive search webapp
```

---

## Requirements

- Dataiku DSS **7.0+**
- The plugin's managed code environment (created automatically on install)
- The DSS instance user running the webapp must have access to the public API (standard for most user roles)
- Admin-level API access may be required to list **all** code environments on the instance (instance-scoped vs. project-scoped envs)

---

## Installation

### From GitHub (Development Install)

1. In DSS, go to **Administration > Plugins > Add Plugin > Fetch from Git repository**
2. Enter the repository URL:
   ```
   git@github.com:dtb-dataiku/code-envs-search-plugin.git
   ```
3. After fetching, DSS will prompt you to **create the plugin's code environment** — do this before using any components.

### Manual Install

1. Clone the repo locally:
   ```bash
   git clone https://github.com/dtb-dataiku/code-envs-search-plugin.git
   ```
2. Zip the contents (not the outer folder — zip from inside so `plugin.json` is at the root)
3. In DSS: **Administration > Plugins > Add Plugin > Upload**
4. Create the plugin code environment when prompted

---

## Usage

### Dataset Connector: Code Environments Inventory

The plugin also includes a Python connector that produces a dataset of all code environments and their installed packages — useful for auditing or building dashboards on top of.

1. In a DSS project, create a new dataset → **Plugin** → **Code Environments Search**
2. Run the dataset to populate a full inventory of environments and packages
3. Use downstream recipes to filter, join, or visualize as needed
4. The webapp is designed to use this dataset

### Webapp: Search Code Environments

1. In any DSS project, go to **Webapps** and create a new webapp using the **Code Environment Search** template from this plugin.
2. Launch the webapp.
3. Type a package name(s) (e.g., `pandas`, `torch`, `tidyverse`) into the search box.
4. Results show all environments where that package is installed, along with the installed version.

---

## Contributing

Pull requests and issues are welcome. This is a personal/internal tool published openly — contributions that improve compatibility or improve the webapp UI are especially appreciated.

---

## Author

**Darin Brown** · [darin.brown@dataiku.com](mailto:darin.brown@dataiku.com)

---

## License

[Apache Software License 2.0](https://www.apache.org/licenses/LICENSE-2.0)