from aws_cdk import (
    Stack,
    Aws,
    Duration,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_s3 as s3,
    CustomResource
)
from constructs import Construct

class ProductsCustomStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        load_data_lambda_role = iam.Role(self, "LoadDataLambdaRole",
                                         assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                         inline_policies={
                                             "DynamoDB": iam.PolicyDocument(
                                                 statements=[iam.PolicyStatement(
                                                     actions=[
                                                         "dynamodb:DescribeTable",
                                                         "dynamodb:PutItem",
                                                     ],
                                                     resources=[
                                                         props['products_table'].ref,
                                                         props['categories_table'].ref
                                                     ]
                                                 )
                                             ]),
                                             "S3": iam.PolicyDocument(statements=[
                                                 iam.PolicyStatement(
                                                     actions=["s3:GetObject"],
                                                     resources=[f"arn:aws:s3:::{props['resource_bucket']}"]
                                                 )
                                             ]),
                                             "CloudWatch": iam.PolicyDocument(statements=[
                                                 iam.PolicyStatement(
                                                     actions=[
                                                         "logs:CreateLogGroup",
                                                         "logs:PutLogEvents",
                                                         "logs:CreateLogStream"
                                                     ],
                                                     resources=["arn:aws:logs:*:*:*"]
                                                 )
                                             ])
                                         })

        load_data_lambda_function = lambda_.Function(self, "LoadDataLambdaFunction",
                                                     runtime=lambda_.Runtime.GO_1_X,
                                                     description="Retail Demo Store deployment utility function that loads product and category information into DynamoDB tables",
                                                     handler="main",
                                                     code=lambda_.Code.from_bucket(s3.Bucket.from_bucket_attributes(self, "LoadDataLambdaFunctionBucket", bucket_name=props['resource_bucket']), f"{props['resource_bucket_relative_path']}aws-lambda/retaildemostore-lambda-load-products.zip"),
                                                     role=load_data_lambda_role,
                                                     timeout=Duration.seconds(900))

        CustomResource(self, "CustomLoadDataProducts",
                       resource_type="Custom::CustomLoadData",
                       service_token=load_data_lambda_function.function_arn,
                       properties={
                           "Bucket": props['resource_bucket'],
                           "File": f"{props['resource_bucket_relative_path']}data/products.yaml",
                           "Table": props['products_table'].ref,
                           "Datatype": "products"
                       })

        CustomResource(self, "CustomLoadDataCategories",
                       resource_type="Custom::CustomLoadData",
                       service_token=load_data_lambda_function.function_arn,
                       properties={
                           "Bucket": props['resource_bucket'],
                           "File": f"{props['resource_bucket_relative_path']}data/categories.yaml",
                           "Table": props['categories_table'].ref,
                           "Datatype": "categories"
                       })
