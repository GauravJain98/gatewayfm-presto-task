# Format Python files
uv run black ./load-generator && uv run isort ./load-generator && uv run flake8 ./load-generator && uv run pylint ./load-generator
# Format YAML files
prettier --write "./manifests/**/*.{yml,yaml}"