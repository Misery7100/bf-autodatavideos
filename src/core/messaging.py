import boto3

# ---------------------------- #

def connect_to_queue(region: str, queue_name: str):

    sqs = boto3.resource('sqs', region_name=region)
    queue = sqs.get_queue_by_name(QueueName=queue_name)

    return queue

# ---------------------------- #

def send_message(queue: object, body: str = 'Sample text', delay: int = 0, **attrs):
    
    msg_attributes = dict(
        (key, dict(DataType="String", StringValue=str(value))) for key, value in attrs.items()
    )

    queue.send_message(
        MessageBody=body,
        DelaySeconds=delay,
        MessageAttributes=msg_attributes
    )

# ---------------------------- #