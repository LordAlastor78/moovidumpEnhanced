MooviDump Enhanced

Quick start

- Copy `example.env` to `.env` and fill `MOODLE_SITE`, `MOODLE_USERNAME`, `MOODLE_PASSWORD`.
- Install dependencies:

	pip install -r requirements.txt

- Run the dump:

	python main.py

Notes

- Output files are saved under `dumps/`.
- Set `DUMP_ALL = True` in `main.py` to include JSON snapshots.
- Filenames are sanitized; enable `FULL_SANITIZER = True` to replace spaces with underscores.

