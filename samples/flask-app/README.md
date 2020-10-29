# elektra

Elektra service to provide block price conversion and price determination.  The `elektra` service utilizes the [elektra PIP package](https://pypi.org/project/elektra/)

## End-Points

Two primary end-points:

1. `/create` returns json containing a single price
2. `/scrub` returns json containing a collection of prices