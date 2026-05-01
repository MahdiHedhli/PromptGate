.PHONY: release-check test

release-check:
	./scripts/release-check.sh

test:
	.venv/bin/python -m pytest -q
