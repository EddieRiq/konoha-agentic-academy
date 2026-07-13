# v3.3.0 Installable Terminal Distribution Review Scroll

## Installer

```bash
bash -n scripts/install.sh
grep -n "INSTALL_KONOHA_CLI\|confirm-install\|v3.3.0" scripts/install.sh
```

Reject:

```text
unversioned clone
force checkout
hard reset
root/system-wide writes
hidden approval
background service
```

## Distribution tests

```bash
python -S -m unittest discover \
  -s tests/distribution \
  -p "test_*.py"
```

## Release wrapper tests

```bash
python -S -m unittest discover \
  -s tests/release_delivery \
  -p "test_*.py"
```

## Clean-install smoke

```bash
python -S tools/distribution/run_clean_install_smoke.py \
  --repo-root . \
  --expected-version 3.3.0 \
  --output ./sandbox/reports/v3-3-0-clean-install-smoke.json \
  --force
```

## Registry

```bash
python -S tools/konoha_cli.py --validate-registry
python -S tools/konoha_cli.py --registry-json
```

Confirm these active commands:

```text
install-status
upgrade
uninstall
release deliver
```

Confirm that the registry does not inject:

```text
approval tokens
--allow-network
force arguments
```

## Package-to-release dogfood

Run the v3.3.0 delivery plan with the exact token block. Final expected state:

```text
PACKAGE_RELEASE_CLOSED
RELEASE_CLOSED
managed clean-install smoke passed
working tree clean
origin/main 0/0
```

## Public/private stop conditions

Stop if the public scope contains:

```text
.env
sandbox
alliance/kirigakure
private-library
alliance/*/memory
memory/local
vault
credentials
company/client data
```
