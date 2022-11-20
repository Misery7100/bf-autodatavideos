def lambda_handler(event, context):

    # some change
    x = 130222

    print(event)
    print(dir(event))
    print(context)
    print(dir(context))
    
    return {
        'statusCode': 200,
        'body': str(x),
        'headers': {
            "Content-Type": "application/json"
        }
    }