"""
 This is a simple AWS Lambda function template.
 It will load the main job function and execute it.
 """
from src.job_processor import JobProcessor

def lambda_handler(event, context):
    # This function is executed when the Lambda function is invoked
    # You can add your code here to process the event
    print("Event: ", event)
    print("Context: ", context)


    jobs = JobProcessor()
    jobs.process_active_jobs()
    
    # Example response
    return {
        'statusCode': 200,
        'body': 'Job completed successfully!'
    }