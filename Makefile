
# install dependencies using pip, uv or pipx

install:
	pip install -r requirements.txt

run:
	python config.py

debug:
	python -m pdb main.py

clean:
	rm -rf  __pycache__
	rm -rf .mypy_cache

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores \
	--ignore-missing-imports --disallow-untyped-defs \
	--check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict