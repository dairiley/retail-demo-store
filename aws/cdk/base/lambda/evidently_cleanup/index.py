import boto3
import cfnresponse


def handler(event, context):
    print(event)

    response_data = {}
    response_status = cfnresponse.SUCCESS

    try:
        project_name = event['ResourceProperties']['EvidentlyProjectName']

        if event['RequestType'] == 'Delete':
            evidently = boto3.client('evidently')

            experiments_stopped = 0
            experiments_deleted = 0
            paginator = evidently.get_paginator('list_experiments')
            for paginate_result in paginator.paginate(project=project_name):
                for experiment in paginate_result['experiments']:
                    if experiment['status'] == 'RUNNING':
                        print(f"Experiment {experiment['name']} is still running; cancelling")
                        evidently.stop_experiment(desiredState='CANCELLED',
                                                  experiment=experiment['name'],
                                                  project=project_name
                                                  )
                        experiments_stopped += 1

                    print(f"Deleting experiment {experiment['name']}")
                    evidently.delete_experiment(experiment=experiment['name'],
                                                project=project_name
                                                )
                    experiments_deleted += 1

            message = f"Stopped {experiments_stopped} experiments and deleted {experiments_deleted} experiments"
            response_data['Message'] = message
        else:
            response_data['Message'] = "Nothing to do for this request type"

    except Exception as e:
        print("Error: " + str(e))
        response_status = cfnresponse.FAILED
        response_data['Message'] = "Resource {} failed: {}".format(event['RequestType'], e)

    cfnresponse.send(event, context, response_status, response_data)
