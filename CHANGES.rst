Changes
=======

2.0.1 (unreleased)
------------------

- Sort the imports with ruff (one per line, ``from`` imports first, no
  sections) and format the code with ``ruff format`` (90 characters per line,
  single quotes).
  [rnix]

- Add import sorting (``I`` rules) and the formatter settings to the ruff
  configuration in ``pyproject.toml``.
  [rnix]


2.0.0 (2026-10-24)
------------------

- Render ``TokenSettingsForm`` in a card with the title of the settings node
  as card header, like the settings forms of ``cone.ugm``.
  [rnix]

- ``TokenForm.timerange_extractor`` skips an empty ``valid_to`` by value.
  It checked for ``UNSET``, but ``yafowil.widget.datetime`` extracts an empty
  value as ``None``, so the guard never applied.
  [rnix]

- Modernise the code ruff flags as outdated: ``class X(object)``. Remove
  unused import. Behaviour unchanged. ``super(Class, self)`` is kept, see
  ``cone.app``.
  [rnix]

- Pin the ruff rule selection in ``pyproject.toml``. Remove ``qa.isort``
  domain from Makefile, ``make check`` runs ``ruff check`` only, like in the
  other ``cone.*`` packages.
  [rnix]

- Pin ``setuptools<82.0.0`` in ``mx.ini``. ``pyramid`` 2.0.2 still imports
  ``pkg_resources``, which ``setuptools`` 82 removed.
  [rnix]

- Boostrap 5 styles.


1.1.0 (2026-02-03)
------------------

- Refactor package layout to use ``pyproject.toml`` and implicit namespace packages.
  [rnix]


0.5 (2024-05-23)
----------------

- Update Makefile.
  [rnix]

- ``properties`` and ``metadata`` of ``cone.tokens.model.Tokens`` are instance
  properties now.
  [rnix]

- Use ``ts.http_request`` instead of ``ts.ajax.request``.
  [rnix]


0.4 (2024-02-12)
----------------

- Adopt Settings UI changes from ``cone.app``.
  [rnix]


0.3 (2023-09-28)
----------------

- Tokens can be bulk deleted.
  [lenadax]

- Tokens can be created from scanned value.
  [rnix]


0.2 (2023-09-27)
----------------

- Actually upload package to pypi.
  [rnix]


0.1 (2023-09-27)
----------------

- Initial work.
  [rnix, toalba, lenadax]
