# ticket-escalation-agent

[![CI](https://github.com/minaelzek/ticket-escalation-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/minaelzek/ticket-escalation-agent/actions/workflows/ci.yml)

Offline customer-support agent. It reads the local markdown help center in [`corpus/`](corpus/), answers a ticket only with claims quoted from the matching chunks, or escalates to a human. There is no network call, no API key, and no LLM.

> [!NOTE]
> The help center is a small fictional corpus checked into this repository. The agent does not invent policy that is not in those files.

**Maintainer:** [Mina Elzek](https://github.com/minaelzek) · **Built:** November 2026

## About

| | |
| --- | --- |
| Package | `ticket_agent` |
| API | `answer_ticket(ticket) -> AgentResult` |
| CLI | `python -m ticket_agent` reads one JSON ticket from stdin |
| Threshold | `CONFIDENCE_THRESHOLD = 0.18` in [`ticket_agent/agent.py`](ticket_agent/agent.py) |
| Python | 3.11+ |
| Dependencies | standard library only |

## Decision rule

`answer_ticket` looks at `subject`, `body`, and `requester_email`.

1. If `requester_email` is not a single address of the form `local@domain.tld` (no spaces), return `action="escalate"`, `answer=null`, `citations=[]`, `confidence=0`, and `escalation.reason="invalid_requester"`. The queue is `human_support`. The corpus is not used to invent an answer.
2. Chunk every `corpus/*.md` file. Split on markdown headings, then on blank lines, so each chunk is one paragraph. Keep the source path (for example `corpus/refunds.md`) and the heading.
3. Tokenize the ticket (`subject` plus `body`) and each chunk (heading plus paragraph). A token is a lowercase run of letters or digits of length at least 3, minus the stopword list in [`ticket_agent/tokenize.py`](ticket_agent/tokenize.py).
4. The chunk score is normalized token overlap: `|query ∩ chunk| / |query|`, rounded to 4 decimal places. The score is 0 when the query is empty or no token overlaps.
5. If the best score is at least `0.18` and at least one chunk meets it, return `action="answer"`. The answer quotes the top 1–3 chunks at or above the threshold and does not add policy from anywhere else. `citations` are `{source, heading, score}`. `confidence` is the best score. `escalation` is null.
6. Otherwise return `action="escalate"`, `answer=null`, and `escalation.queue="human_support"`.
   * `reason="empty_corpus_match"` when no chunk shares a token. Citations are empty.
   * `reason="low_confidence"` when some tokens overlap but the best score is below the threshold. Citations are those weak top chunks (up to 3).

## Getting started

No third-party packages are required to run the agent. Pytest is the only development dependency.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

### Answer a sample ticket

```bash
python -m ticket_agent < fixtures/tickets/refund.json
```

On Windows PowerShell:

```powershell
Get-Content -Raw -Encoding utf8 fixtures/tickets/refund.json | python -m ticket_agent
```

[`fixtures/tickets/wifi.json`](fixtures/tickets/wifi.json) is an out-of-domain escalation. [`fixtures/tickets/invalid-email.json`](fixtures/tickets/invalid-email.json) escalates with `invalid_requester`. [`fixtures/tickets/weak-overlap.json`](fixtures/tickets/weak-overlap.json) escalates with `low_confidence`.

## Tests

```bash
python -m pytest
```

The tests check a refund answer and its citation, an out-of-domain escalation, an invalid email, and that an answer does not pick up a fact that lives only in a different article.

## Project layout

```text
ticket_agent/     decision rule, retrieval, CLI
corpus/           help-center articles
fixtures/tickets/ sample tickets
tests/
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The [Code of Conduct](CODE_OF_CONDUCT.md) applies to this repository.

## Security

See [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE) © 2026 Mina Elzek
