# Contributing

Thanks for helping improve `ticket-escalation-agent`.

## Ground rules

* Be kind. The [Code of Conduct](CODE_OF_CONDUCT.md) applies to issues, pull requests, and discussions.
* Open an issue before a large change so we can agree on the approach.
* Keep pull requests focused. One behavior change per pull request is easier to review.

## Development setup

Python 3.11 or newer. The agent itself uses only the standard library.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

## Tests

```bash
python -m pytest
```

If you change `CONFIDENCE_THRESHOLD` or the citation shape, update the README and the tests in the same pull request. GitHub Actions runs pytest on every pull request against Python 3.11, 3.12, and 3.13.

## Pull requests

Use the pull request template. Answers must stay traceable to a chunk in [`corpus/`](corpus/). Do not add a model client.

## Reporting security issues

See [SECURITY.md](SECURITY.md). Do not file a public issue for a vulnerability.
