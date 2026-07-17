# Model Hub Provider Plugin Package

This directory now contains a daemon-oriented Dify model plugin project layout.

Key files:

- `manifest.yaml`
- `main.py`
- `provider/model_hub.yaml`
- `provider/model_hub.py`
- `models/**`
- `_assets/**`

The plugin still keeps the earlier developer scaffold files for local testing,
but the `.difypkg` build now targets the plugin daemon's expected project
structure.

## Local package build

Build a local unsigned package archive:

```powershell
python api/dev/model_hub_provider_plugin_package/build_package.py
```

Default output:

`api/dev/model_hub_provider_plugin_package/dist/model-hub-provider-0.1.5.difypkg`

## Local live install helper

Once the Dify API and plugin daemon are reachable, you can feed the local
package into the backend directly:

```powershell
python api/dev/model_hub_provider_plugin_package/install_live.py --email admin@bblizhuo.local
```

## Local verification

Run the local package verification chain:

```powershell
python api/dev/model_hub_provider_plugin_package/verify_local.py
```

## Target plugin identity

- author: `your-company`
- name: `model-hub-provider`
- provider yaml id: `model_hub`
- display provider id in Dify UI/runtime: `your-company/model-hub-provider/model_hub`

## Required proxy endpoints

- `GET /provider/ping`
- `GET /provider/models`

See `docs/proxy-api-contract.md`.
