.PHONY: test check demo

test:
	PYTHONPATH=src python3 -m unittest discover -s tests -v

check:
	python3 scripts/check_style.py

demo:
	./run.sh examples/acyclic.toml
