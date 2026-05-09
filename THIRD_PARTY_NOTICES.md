# Third-Party Notices

## PyEDM

This repository does not vendor the original PyEDM source tree. It depends on
the upstream PyEDM commit `bc7b850` for empirical dynamic modeling routines.
That commit is labeled v2.1.1 in the original local clone; PyPI does not
publish a `pyEDM==2.1.1` wheel/sdist.

- Project: https://github.com/SugiharaLab/pyEDM
- Package: https://pypi.org/project/pyEDM/
- Original authors/maintainers: Sugihara Lab / Joseph Park

PyEDM carries the University of California license from the upstream project.
Review the upstream license before redistribution or commercial use.

## Python Dependencies

Runtime dependencies are declared in `pyproject.toml`: `pyEDM`, `numpy`,
`pandas`, `matplotlib`, and `seaborn`.
