.. image:: https://img.shields.io/pypi/v/cone.tokens.svg
    :target: https://pypi.python.org/pypi/cone.tokens
    :alt: Latest PyPI version

.. image:: https://img.shields.io/pypi/dm/cone.tokens.svg
    :target: https://pypi.python.org/pypi/cone.tokens
    :alt: Number of PyPI downloads

.. image:: https://github.com/conestack/cone.tokens/actions/workflows/python-package.yml/badge.svg
    :target: https://github.com/conestack/cone.tokens/actions/workflows/python-package.yml
    :alt: Package build

.. image:: https://coveralls.io/repos/github/bluedynamics/cone.tokens/badge.svg?branch=master
    :target: https://coveralls.io/github/bluedynamics/cone.tokens?branch=master

This package provides a unique token generator for ``cone.app``.

Features:

* QR Code generation
* JSON API for token management


Application ini file configuration
==================================

- **cone.tokens.config_file**: Required. Path to tokens json config file.

- **cone.tokens.settings_node_path**: Optional. Application node path to token settings node.

- **cone.tokens.entryfactory**: Optional. Node class used as entry node factory.


JSON API
========

``cone.tokens`` provides a JSON API for token management.


query_token
-----------

Query token by value. It expects a ``GET`` request.

**Schema**: URL/tokens/query_token

**Params**

- ``value``: A string containing the token value to look up.

**Response**

- ``success``: True or False.
- ``token``: Token data or null if token not exists.
- ``message``: On failure the error message is returned.


add_token
---------

``add_token`` is for generating a new token. It expects a ``POST`` request.

**Schema**: URL/tokens/add_token

**Params**

- ``value``: A string containing the token value. If empty, the token uuid gets used as value.
- ``valid_from``: A datetime in isoformat. If empty, token has no effective date.
- ``valid_to``: A datetime in isoformat. If empty, token has no expiration date.
- ``usage_count``: An integer defining how often the token can be consumed. If -1, token can be consumed unlimited times.
- ``lock_time``: Time in seconds the token is locked after consumption as integer.

**Response**

- ``success``: True or False.
- ``token_uid``: On success the token uid is returned.
- ``message``: On failure the error message is returned.


consume_token
-------------

``consume_token`` is for consuming a token. It expects a ``GET`` request.

**Schema**: URL/tokens/<UUID>/consume_token

**Params**

- No parametes expected.

**Response**

- ``success``: True or False.
- ``consumed``: On success flag whether token consumption was valid.
- ``message``: On failure the error message is returned.


update_token
------------

``edit_token`` is for editing a token. It expects a ``POST`` request.

**Schema**: URL/tokens/<UUID>/update_token

**Params**

- ``value``: A string containing the token value. If empty, the token uuid gets used as value. Unchanged if parameter is omitted.
- ``valid_from``: A datetime in isoformat. If empty, token has no effective date. Unchanged if parameter is omitted.
- ``valid_to``: A datetime in isoformat. If empty, token has no expiration date. Unchanged if parameter is omitted.
- ``usage_count``: An integer defining how often the token can be consumed. If -1, token can be consumed unlimited times. Unchanged if parameter is omitted.
- ``lock_time``: Time in seconds the token is locked after consumption as integer. Unchanged if parameter is omitted.

**Response**

- ``success``: True or False.
- ``message``: On failure the error message is returned.


delete_token
------------

``delete_token`` is for deleting a token. It expects a ``POST`` request.

**Schema**: URL/tokens/<UUID>/delete_token

**Params**

- No parametes expected.

**Response**

- ``success``: True or False.
- ``message``: On failure the error message is returned.


TODO
====

- Introduce ``consume`` permission for JSON API.


Contributors
============

- Robert Niederreiter
- Torben Baumgartner
- Lena Daxenbichler
