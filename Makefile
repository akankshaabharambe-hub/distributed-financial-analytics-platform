lint:
\tpython -m compileall data_pipeline

run-sample:
\tpython -m data_pipeline.ingest --input examples/sample_input.json --output examples/staged.json
\tpython -m data_pipeline.validate --input examples/staged.json
\tpython -m data_pipeline.transform --input examples/staged.json --output examples/analytics_rows.json
