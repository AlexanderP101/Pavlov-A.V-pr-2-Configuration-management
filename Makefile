.PHONY: test check demo

test:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -v

check:
	python3 -B scripts/check_style.py

demo:
	./run.sh examples/acyclic.toml
