# placeholder lambda

def lambda_handler(event, context):

    # some change
    x = 130222
    
    return {
        'statusCode': 200,
        'body': str(x),
        'headers': {
            "Content-Type": "application/json"
        }
    }