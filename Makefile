PYTHON ?= python

venv:
	$(PYTHON) -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt

run-mock:
	$(PYTHON) -m src.main --scenario scenarios --adapter mock --out artifacts

run-command:
	$(PYTHON) -m src.main --scenario scenarios --adapter command --out artifacts

test:
	pytest -q

docker-mock:
	docker compose run --rm harness
