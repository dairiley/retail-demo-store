import boto3
import cfnresponse


def handler(event, context):
    print(event)
    responseData = {}
    responseStatus = cfnresponse.SUCCESS

    try:
        registryId = event['ResourceProperties']['RegistryId']
        repositoryName = event['ResourceProperties']['RepositoryName']

        if event['RequestType'] == 'Create':
            responseData['Message'] = "Repository creation succeeded"
        elif event['RequestType'] == 'Update':
            responseData['Message'] = "Repository update succeeded"
        elif event['RequestType'] == 'Delete':
            # Delete the registry
            ecr = boto3.client('ecr')
            ecr.delete_repository(
                registryId=registryId,
                repositoryName=repositoryName,
                force=True
            )

            responseData['Message'] = "Repository deletion succeeded"

    except Exception as e:
        print("Error: " + str(e))
        responseStatus = cfnresponse.FAILED
        responseData['Message'] = "Repository {} failed: {}".format(event['RequestType'], e)

    cfnresponse.send(event, context, responseStatus, responseData)
