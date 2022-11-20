# BF: Automatized data videos

Automatized data videos creation using sofascore and plainly

## Structure

<img src="./img/bf-autodatavideos.png">

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

**Notes**

- What about celery for pull scheduling?

## Messaging Interface
_based on: AWS SQS_

**Message format**

```json
{
    "event_id"        : 10230541,
    "processing_type" : "line-up"
}
```

**Notes**

## Handler
_based on: AWS Lambda_

**Notes**

export AWS_ACCESS_KEY_ID="ASIASWHC56P3PORWXOJ3"
export AWS_SECRET_ACCESS_KEY="OtalNOhmoVgOhRrQgWz7kehlqKnJmU2+qJ9BbDQc"
export AWS_SESSION_TOKEN="IQoJb3JpZ2luX2VjEG8aDGV1LWNlbnRyYWwtMSJHMEUCIGBDEcXzJY0uOG2/LjnwNTXbF3NuAvwL/3ukkVqvlWcLAiEAwP0dyr1d0lPCkTOz+AoIrZmYBJYarP4WY2jXxFUnPywqgQMIeBAAGgwxODUxNTk1MTMwNzgiDE75/YNt5Qu07c2QrCreAgA2jAQgCdg/xt2o/pzJrVRosqUcU3xfes7VC+mZaJFQwlcTjeZ/WehUpO7TEzLqRQY7uWCmFoToUfIjtG2oILICYI7+rglu2kuQuXr+TJ1Gk8S16HMjtdgz8TelBDBgRG5CQ55ZrfRM3RTMbBNFDCAgWy6GtIpH8N7Mk2mIw1yqcEGXoQ0MiK/+RJQa6U6VLIqWAtvxEjEZxqXR8m28w/xfKLIj+Eij8z7boaMfZ7JCM00XpceJ7WBBBfrMNHxQhuErSEiIfy1dKtxNAyBY1r4Gl934vW1MBvLisNtWBknKrynDwvUcNHZc0DWLJWNzQowqzrvFPdn21n3A7rVIHKRSyn53Ac5ch+XAOCMRbl6LTAk27dgkeg24Yo3U2aT+y0qEK1X8DvO/3YOnhYX3cJSdD6+RbQ4Et0ucs3Otq+PK5q10CCTB/3t/jp+SrsCflCR1SocC5uekApcfYLHAMKKH6ZsGOqYBI5aEh1gaV9ji6DBFO7+ot8byU+iKbnLoOPxUT7my6/oza74+0Zal451NjsqUcjBM41oMNNzbSaDsrxOueh0t1l/KBWruqel+kXP8giwYgOp1VkYpzgr0OL8DCqED4AyMNm7W0B/hPqat112UCRLTkTb5nVoK/OgAJ0rCwzkIunwTli/tAksjSrISYxGLouTMRpF8syrMLagoThzHZl9f/og8ZqMG+w=="