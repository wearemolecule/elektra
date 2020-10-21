# elektra

The purpose of the `elektra` project is to provide a utility to create and convert power prices to their respective block constructs.

There are two primary methods implemented in the elektra project

* create_prices
* scrub_hourly_prices

## Create Prices

The *create_prices* method takes the following parameters:

* `flow_date` - *date* | The as of date for the power prices
* `ticker` - *string* | The ticker symbol for the power product
* `node` - *string* | The node on the power grid
* `iso` - *string* | The short name of the Independent Service Operator
* `block` - *string* | The power block for the prices
* `frequency` *string* | The price frequency, either Daily or Monthly
* `prices` *dataframe* | A Python dataframe of prices consisting of `flow_date`, `hour_ending`, and `price`

The response from the method is a single price *float* the provided attributes.

## Scrub Hourly Prices

The *scrub_hourly_prices* method takes the following parameters:

* `flow_date` - *date* | The as of date for the power prices
* `ticker` - *string* | The ticker symbol for the power product
* `node` - *string* | The node on the power grid
* `iso` - *string* | The short name of the Independent Service Operator
* `prices` *dataframe* | A python dataframe of prices consisting of `flow_date`, `hour_ending`, and `price`

The response from the method is a Python dataframe with the following columns of data:

* Hour Beginning
* Hour Ending
* Required
* Special
* Value