---
name: ci-cd
description: Set up CI/CD for Odoo 17 modules — GitHub Actions / GitLab CI with matrix testing, pre-commit, pylint-odoo, coverage, OCA-style runbots, automated deployment to Odoo.sh / self-hosted. Use when configuring CI for an Odoo repo, automating test runs, or setting up auto-deploy from main.
---

# CI/CD for Odoo (Odoo 17)

## When to use this skill

You're setting up CI/CD on a repo of Odoo modules — either OCA-style with many addons, or a single-product repo. Or you're auto-deploying to Odoo.sh / a self-hosted server.

## What "good CI" looks like for Odoo

1. **Linting**: pre-commit (black, isort, flake8, pylint-odoo) on every PR
2. **Tests**: install module(s) on a fresh DB, run `--test-enable --stop-after-init`, all pass
3. **Coverage**: track which lines tests cover; flag drops
4. **Multi-version**: if your repo supports multiple Odoo versions, matrix-test them
5. **Auto-deploy** (optional): on merge to a branch, push to Odoo.sh / SSH to server / build container

## GitHub Actions: minimal Odoo 17 test workflow

```yaml
# .github/workflows/test.yml
name: Tests

on:
  pull_request:
  push:
    branches: ["17.0"]

jobs:
  test:
    runs-on: ubuntu-22.04

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: odoo
          POSTGRES_PASSWORD: odoo
          POSTGRES_DB: postgres
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with: { path: addons }

      - name: Set up Python
        uses: actions/setup-python@v5
        with: { python-version: "3.10" }

      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}

      - name: Install system deps
        run: |
          sudo apt-get update
          sudo apt-get install -y --no-install-recommends \
            python3-dev libldap2-dev libsasl2-dev libxml2-dev libxslt1-dev \
            libjpeg-dev zlib1g-dev libffi-dev wkhtmltopdf

      - name: Clone Odoo
        run: git clone --depth=1 -b 17.0 https://github.com/odoo/odoo.git /tmp/odoo

      - name: Install Odoo
        run: |
          pip install --upgrade pip
          pip install -r /tmp/odoo/requirements.txt
          pip install /tmp/odoo

      - name: Install our addon deps
        run: |
          if [ -f addons/requirements.txt ]; then pip install -r addons/requirements.txt; fi

      - name: Install + test our modules
        env:
          PGHOST: localhost
          PGPORT: 5432
          PGUSER: odoo
          PGPASSWORD: odoo
        run: |
          # Detect installable modules
          MODULES=$(find addons -maxdepth 2 -name "__manifest__.py" \
                    | xargs -I{} dirname {} | xargs -I{} basename {} \
                    | tr '\n' ',' | sed 's/,$//')
          echo "Testing: $MODULES"
          createdb -h localhost -U odoo test_db
          /tmp/odoo/odoo-bin \
            --addons-path=/tmp/odoo/addons,addons \
            -d test_db \
            -i "$MODULES" \
            --test-enable \
            --test-tags="$MODULES" \
            --stop-after-init \
            --log-level=info
```

## Pre-commit on CI

```yaml
# .github/workflows/pre-commit.yml
name: pre-commit
on:
  pull_request:
  push:
    branches: ["17.0"]

jobs:
  pre-commit:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.10" }
      - uses: pre-commit/action@v3.0.0
```

The `.pre-commit-config.yaml` in the repo root drives this. See `oca-compliance` skill for the full config.

## Multi-version matrix

```yaml
strategy:
  fail-fast: false
  matrix:
    odoo-version: ["17.0", "16.0"]

steps:
  - name: Checkout
    uses: actions/checkout@v4
    with:
      ref: ${{ matrix.odoo-version }}      # if branches per version
  - run: git clone --depth=1 -b ${{ matrix.odoo-version }} https://github.com/odoo/odoo.git /tmp/odoo
```

If your repo has a branch per version (like this pack), `ref:` ensures CI runs on the right branch. If you have one branch supporting multiple Odoo versions (less common), use the matrix to install Odoo for each.

## Coverage with codecov

```yaml
- name: Run with coverage
  run: |
    pip install coverage
    coverage run --source=addons /tmp/odoo/odoo-bin \
      --addons-path=/tmp/odoo/addons,addons \
      -d test_db -i my_module --test-enable --stop-after-init
    coverage xml -o coverage.xml

- uses: codecov/codecov-action@v4
  with:
    files: ./coverage.xml
```

## OCA-style runbot replication

The OCA `oca-ci` action does most of this for you:

```yaml
jobs:
  test:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4
      - uses: OCA/odoo-pre-commit-hooks@v0.0.33
      # ... or use OCA's docker images directly
      - run: docker run --rm \
               -v $(pwd):/mnt/extra-addons \
               ghcr.io/oca/oci-odoo:17.0 \
               odoo --test-enable --stop-after-init -i my_module -d test
```

The OCA Docker images (`ghcr.io/oca/oci-odoo:VERSION`) bundle Odoo + Postgres + tools, ready to install your addons under `/mnt/extra-addons`.

## Auto-deploy patterns

### Push to Odoo.sh

Odoo.sh deploys automatically when you push to its remote. CI just runs tests; the deploy happens on push.

```yaml
- name: Push to Odoo.sh
  if: github.ref == 'refs/heads/17.0'
  run: |
    git remote add odoosh git@github.com:my-org/odoosh-mirror.git
    git push odoosh 17.0
  env:
    SSH_KEY: ${{ secrets.ODOOSH_DEPLOY_KEY }}
```

### Self-hosted: SSH + restart

```yaml
- name: Deploy to staging
  if: github.ref == 'refs/heads/17.0'
  uses: appleboy/ssh-action@v1.0.0
  with:
    host: ${{ secrets.STAGING_HOST }}
    username: deploy
    key: ${{ secrets.SSH_KEY }}
    script: |
      cd /opt/odoo/custom
      git pull origin 17.0
      sudo systemctl restart odoo
      odoo -c /etc/odoo/odoo.conf -d production -u my_module --stop-after-init || true
```

Always test the deploy on staging first; production should require manual approval (`environment:` with required reviewers in GitHub Actions).

### Docker image build

```yaml
- name: Build and push Docker image
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: ghcr.io/${{ github.repository }}:17.0,ghcr.io/${{ github.repository }}:${{ github.sha }}
```

The Dockerfile starts from `odoo:17` and copies your addons:
```dockerfile
FROM odoo:17
COPY --chown=odoo:odoo . /mnt/extra-addons
USER odoo
```

## GitLab CI equivalent

```yaml
# .gitlab-ci.yml
image: python:3.10

services:
  - postgres:15

variables:
  POSTGRES_USER: odoo
  POSTGRES_PASSWORD: odoo
  POSTGRES_DB: postgres

stages:
  - lint
  - test

pre-commit:
  stage: lint
  script:
    - pip install pre-commit
    - pre-commit run --all-files

test:
  stage: test
  before_script:
    - apt-get update && apt-get install -y libldap2-dev libsasl2-dev wkhtmltopdf
    - git clone --depth=1 -b 17.0 https://github.com/odoo/odoo.git /tmp/odoo
    - pip install -r /tmp/odoo/requirements.txt && pip install /tmp/odoo
  script:
    - createdb -h postgres -U odoo test_db
    - /tmp/odoo/odoo-bin --addons-path=/tmp/odoo/addons,. -d test_db -i my_module --test-enable --stop-after-init
```

## Secrets handling

- Never commit secrets. CI vars only.
- For Odoo.sh deploy keys: GitHub Secrets / GitLab CI variables.
- For DB credentials in test: ephemeral, no production reuse.
- For external API keys used in tests: mock them; don't actually call.

## Common pitfalls

- CI installs Odoo from PyPI — but Odoo isn't on PyPI as of 17.0. Clone the repo or use OCA Docker images.
- Tests pass on developer machine, fail in CI because of missing system packages (`wkhtmltopdf`, `libldap2-dev`). Solve with explicit install steps.
- `--test-tags` not scoped → runs every test in every installed module (slow).
- Coverage broken because `--source=` points at the wrong dir. Should be the addons path, not Odoo's.
- Cache miss on every run because `requirements.txt` is in the wrong path for the cache key.
- Auto-deploy to production with no approval gate → one bad merge takes prod down.
- Forgetting `fail-fast: false` in matrix → one version's flake aborts all runs.

## Checklist for a new repo

- [ ] `.pre-commit-config.yaml` at repo root
- [ ] `.github/workflows/test.yml` (or GitLab equivalent) running tests on PRs
- [ ] `.github/workflows/pre-commit.yml` running pre-commit on PRs
- [ ] Branch protection on `17.0`: CI must pass before merge
- [ ] Codecov / coverage badge in README
- [ ] Deploy workflow gated by environment approval for production
- [ ] No secrets in code; all via CI vars
- [ ] OCA-style if applicable: use `oca-ci` for full standardization

## References

- [GitHub Actions](https://docs.github.com/en/actions)
- [OCA odoo-pre-commit-hooks](https://github.com/OCA/odoo-pre-commit-hooks)
- [OCA oci-odoo Docker images](https://github.com/OCA/oci-odoo)
- [Odoo.sh continuous integration](https://www.odoo.com/documentation/17.0/administration/odoo_sh.html)
