# BF: Automatized data videos

Automatized data videos creation using sofascore and plainly

## Structure

<-- lucidchart diagram -->

## Main Logic

The crawler continuously polls Sofascore API for new events data. Events data preprocessed and pushed to database for further purposes. Alongside the crawler check for events available for queuing into the messaging interface (by positive time difference between event start timestamp and current timestamp, by status to obtain ended events). Suitable events IDs and processing types are pushed as messages to the messaging interface to be processed by the handler. 

### Line-ups

The handler look at processing type firstly to define processing branch. For line-ups handler get a message from the messaging interface, send a request to corresponding Sofascore API endpoint, check confirmation of a line-up. If a line-up is confirmed - handler process the data and make a post request to plainly service, otherwise data ignored, corresponding message is replicated with reasonable delay to replicate handling process and recheck confirmation. 

It's impossible to avoid such procedure while we don't have any lightweight endpoint from Sofascore that can return only confirmation status. Also it's not reasonable to store line-up data into a database at this step, because we can't retrieve partial data for any line-up.

### Results

For results handler get a message from the messaging interface, send two requests: first to extract line-up data after game, second to extract statistics. This data processed by another handler branch and the handler make a post request to plainly service. Alongside with the plainly request extracted data stored into database for further aggregation and processing tournament statistics.

### Tournament statistics

No description given.

## Crawler
_based on: AWS EC2_

## Messaging Interface
_based on: AWS SQS_

__Message format__

```json
{
    "event_id"        : 10230541,
    "processing_type" : "line-up"
}
```

## Handler
_based on: AWS Lambda_