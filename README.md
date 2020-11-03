# elektra

Elektra is Molecule's core framework for block-logic (i.e., how to compute mwh from 5x16, 2x16, etc. blocks). It's derived from a set of our core logic internal to the Molecule application, and we're happy to share it with the world -- because nobody should ever have to fight with North American power block logic, ever, again.

Elektra is in pre-release mode, which means that signatures may change over time as we evolve the project to 1.0. Submissions are welcome.

These are the primary methods implemented in the elektra project, although many constructs and sub-functions are currently public.

* create_prices
* scrub_hourly_prices
* convert
* translateBlocks

## Create Prices
This method creates block prices, given hourly prices for a period of time and a handful of other parameters. A key function of this method is that it validates whether enough prices have been submitted to do the calculation. So, if the `block` is 5x16, but a price is missing for a Wednesday at 11 AM, an exception will be thrown. Daylight Savings Time is also contemplated.

The *create_prices* method takes the following parameters:

* `flow_date` - *date* | The as of date for the power prices (i.e., the settlement/reporting date needed)
* `ticker` - *string* | The ticker symbol for the power product (Molecule ticker; used for identification, not calculation)
* `node` - *string* | The node on the power grid (used for identification, not calculation)
* `iso` - *Elektra.Iso* | The name of the Independent Service Operator
* `block` - *Elektra.Block* | The desired power block for the output prices
* `frequency` *Elektra.Frequency* | The desired frequency for the output prices either Daily or Monthly
* `prices` *DataFrame* | A Pandas dataframe of prices consisting of `flow_date`, `hour_ending`, and `price`

The response from the method is a single price *float* the provided attributes.

## Scrub Hourly Prices
This method validates that a submitted dataframe contains all the necessary hourly prices for a flow date, and returns a DataFrame with these prices. Daylight Savings Time (long-day and short-day) is contemplated.

The *scrub_hourly_prices* method takes the following parameters:

* `flow_date` - *date* | The as of date for the power prices (i.e., the settlement/reporting date needed)
* `ticker` - *string* | The ticker symbol for the power product (Molecule ticker; used for identification, not calculation)
* `node` - *string* | The node on the power grid (used for identification, not calculation)
* `iso` - *Elektra.Iso* | The name of the Independent Service Operator
* `prices` *DataFrame* | A Pandas dataframe of prices consisting of `flow_date`, `hour_ending`, and `price`

The response from the method is a Pandas dataframe with the following columns of data:

* Hour Beginning
* Hour Ending
* Required
* Special
* Value

## Convert (Alpha)
Given a flow date and an input block (i.e., 5x16), this method returns the number of hours in another block.

For example, if today is Wednesday, November 4, 2020, and I have a 7x24 block (24 hours), but I want to see how many 5x16 hours that implies -- I'll get 16. On the other hand, if today is Saturday, October 31, 2020, and I have a Wrap block (24 hours that day), that only implies 8 hours of 7x8. This is useful when trying to convert a position purchased in one block, to a volume of another block. It works in tandem with the TranslateBlocks method.

The *convert* method takes the following parameters:

* `flow_date` - *date* | The as of date for the power prices (i.e., the settlement/reporting date needed)
* `input_block` -- (text: Wrap, 5x16, 2x16, 7x8, 7x16, 1x1) | The input block.
* `output_block` -- (text: Wrap, 5x16, 2x16, 7x8, 7x16, 1x1) | The block for which we want to see hours.

## Translate Blocks (Alpha)
Wrapper for `convert`, which adds the ability to convert a MW position for a term block (i.e., 7x24 monthly) to another block (or blocks) for that same term (i.e., 5x16, 2x16).

The *translateBlocks* method takes the following parameters:
* `iso` - *string* | The short name of the Independent Service Operator (Elektra.Iso). This is not currently used, so beware when using for CAISO.
* `mw` - *decimal* | The number of megawatts on the input block to be used for mw/mwh computation
* `frequency` - *text* | monthly, daily, or hourly. Currently only monthly is implemented.
* `contract_start` *date* | The first flow date of the block. This method will compute the last flow date.
* `in_block` - *string* | 7x24, 5x16, Wrap, 2x16, 7x8
* `out_blocks` - *string array* | accepted values include 7x24, 5x16, Wrap, 2x16, 7x8
* `out_uom` - *string* | Set to `MW` for a megawatt number. Default is `mwh`.

## Samples

Included in the *samples* directory, there is an example flask application which utilizes the `elektra` PIP package.
