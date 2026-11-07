.PHONY: help install test
help:
	@echo 'make install: source install; make test: offline legacy/model checks'
install:
	bash scripts/install.sh
test:
	python3 -B -m unittest discover -s tests -p 'test_*.py'
