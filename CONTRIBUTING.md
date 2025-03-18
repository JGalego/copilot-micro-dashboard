# Contributing Guidelines

## Before contributing

**Welcome!** 👋 Before submitting your pull requests, please ensure that you __read the whole guidelines__.

If you have any doubts about the contributing guide, please feel free to state it clearly in an issue or reach out to one of the contributors.

## Contributing

### `pre-commit` plugin

Use [pre-commit](https://pre-commit.com/#installation) to automatically format your code to match our coding style:

```bash
pip install -r requirements-dev.txt
pre-commit install
```

**That's it!** The plugin will run every time you commit any changes.

If there are any errors found during the run, fix them and commit those changes.

You can even run the plugin manually on all files:

```bash
pre-commit run --all-files --show-diff-on-failure
```

### Other Requirements

- Strictly use `snake_case` (underscore_separated) in your file_name, as it will be easy to parse in the future using scripts.
- Please avoid creating new directories if at all possible. Try to fit your work into the existing directory structure.
- If possible, follow the standard *within* the folder you are submitting to.
- If you have modified/added code work, make sure the code compiles before submitting.
- If you have modified/added documentation work, ensure your language is concise and contains no grammar errors.

- Most importantly,
  - __Be consistent__ in the use of these guidelines when submitting.
  - __Reach out__ to other contributors if you have any questions.
  - Once again, thank you for your contribution!