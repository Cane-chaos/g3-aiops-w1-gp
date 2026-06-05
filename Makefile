.PHONY: analyze pipeline verify clean

PYTHON ?= python3
JUPYTER ?= jupyter

analyze:
	MPLCONFIGDIR=/tmp/matplotlib JUPYTER_CONFIG_DIR=/tmp/jupyter-config JUPYTER_DATA_DIR=/tmp/jupyter-data JUPYTER_RUNTIME_DIR=/tmp/jupyter-runtime $(JUPYTER) nbconvert --to notebook --execute --inplace notebooks/analysis.ipynb --ExecutePreprocessor.timeout=600

pipeline:
	MPLCONFIGDIR=/tmp/matplotlib $(PYTHON) scripts/run_pipeline.py

verify:
	$(PYTHON) scripts/verify_outputs.py

clean:
	rm -rf reports/generated reports/figures docs/assets/g3 FINDINGS.md
