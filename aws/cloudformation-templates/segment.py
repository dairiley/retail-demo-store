from aws_cdk import (
    Stack,
    Aws,
    Duration,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_s3 as s3
)
from constructs import Construct

class SegmentStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        iam.Role(self, "SegmentCrossAccountLambdaExecutionRole",
                 description="Required role for Segment to execute a Lambda from the Segment Personalize destination",
                 inline_policies={
                     "root": iam.PolicyDocument(statements=[iam.PolicyStatement(
                         actions=["lambda:InvokeFunction"],
                         principal=iam.ArnPrincipal("arn:aws:iam::595280932656:root"),
                         resources=[f"arn:aws:lambda:{Aws.REGION}:{Aws.ACCOUNT_ID}:function:SegmentPersonalize*"],
                         conditions={"sts:ExternalId": "123456789"}
                     )])
                 })

        segment_personalize_destination_lambda_execution_role = iam.Role(self, "SegmentPersonalizeDestinationLambdaExecutionRole",
                                                                         assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                                                         description="Execution role for the two Lambdas provided with the Segment workshop",
                                                                         inline_policies={
                                                                             "root": iam.PolicyDocument(statements=[
                                                                                 iam.PolicyStatement(
                                                                                     actions=[
                                                                                         "logs:CreateLogStream",
                                                                                         "logs:PutLogEvents",
                                                                                         "logs:CreateLogGroup",
                                                                                         "personalize:GetRecommendations",
                                                                                         "personalize:PutEvents"
                                                                                     ],
                                                                                     resource=["*"]
                                                                                 ),
                                                                                 iam.PolicyStatement(
                                                                                     actions=["ssm:GetParameter"],
                                                                                     resources=[f"arn:aws:ssm:{Aws.REGION}:{Aws.ACCOUNT_ID}:parameter/retaildemostore*"]
                                                                                 )
                                                                             ])
                                                                         })

        lambda_.Function(self, "SegmentPersonalizeEventsDestinationLambda",
                         runtime=lambda_.Runtime.PYTHON_3_8,
                         description="Handles sending events passed from Segment to the Personalize tracker for user-item interactions",
                         function_name="SegmentPersonalizeEventsDestination",
                         handler="segment-personalize-events-destination.lambda_handler",
                         code=lambda_.Code.from_bucket(s3.Bucket.from_bucket_attributes(self, "PersonalizeEventsDestinationLambdaBucket", bucket_name=props['resource_bucket']), f"{props['resource_bucket_relative_path']}aws-lambda/segment-personalize-events-destination.zip"),
                         timeout=Duration.seconds(900),
                         role=segment_personalize_destination_lambda_execution_role,
                         environment={"personalize_tracking_id": ""})

        lambda_.Function(self, "SegmentPersonalizeInferenceDestinationLambda",
                         runtime=lambda_.Runtime.PYTHON_3_8,
                         description="Handles events passed from Segment to Personalize for inference",
                         function_name="SegmentPersonalizeInferenceDestination",
                         handler="segment-personalize-inference-destination.lambda_handler",
                         code=lambda_.Code.from_bucket(s3.Bucket.from_bucket_attributes(self, "SegmentPersonalizeInferenceDestinationLambdaBucket", bucket_name=props['resource_bucket']), f"{props['resource_bucket_relative_path']}aws-lambda/segment-personalize-inference-destination.zip"),
                         timeout=Duration.seconds(900),
                         role=segment_personalize_destination_lambda_execution_role,
                         environment={
                             "personalize_campaign_id": "",
                             "segment_personas_write_key": ""
                         })
