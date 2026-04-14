The commands shown in this section are supposed to run in the terminal of the environment we want to investigate (e.g. workspace).

**Command to remove all of the installed libraries:**

```
pip uninstall -y -r <(pip freeze)
```

**Command to remove cached dependencies:**

```
pip cache remove *
```

This command is useful when we want to install a library without a pinned version (e.g. `pip install dash`). If we had previously installed a specific version (e.g. `pip install dash==3.0.0`), pip will reuse that one since it has the wheel in its cache directory. Alternatively, we can do:
```
pip install dash --no-cache-dir
```

**pipdeptree: show dependencies of libraries and why a library was installed**

While pip freeze shows a flat list, pipdeptree reveals which packages are top-level and what they depend on, including conflicting or circular dependencies. More information: [pipdeptree usage](https://pipdeptree.readthedocs.io/en/latest/how-to/usage.html)

Get why a library has been installed (e.g. flask):
```
pipdeptree --reverse --packages flask
```

Get a simplified version of requirements.txt:
```
pipdeptree -o freeze --warn silence | grep -E '^[a-zA-Z0-9\-]+' > simplified_requirements.txt
```