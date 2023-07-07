from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_iam as iam,
    CustomResource
)
from constructs import Construct

class CloudFrontStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        """
        Web UI
        """

        self.webui_bucket = s3.Bucket(self, "WebUIBucket",
                                      versioned=True,
                                      encryption=s3.BucketEncryption.S3_MANAGED,
                                      server_access_logs_bucket=props['logging_bucket'],
                                      server_access_logs_prefix="webui-logs",
                                      website_index_document="index.html")

        # Empties bucket when stack is deleted
        CustomResource(self, "EmptyWebUIBucket",
                       resource_type="Custom::EmptyStackBucket",
                       service_token=props['cleanup_bucket_lambda_arn'],
                       properties={
                           "bucket_name": self.webui_bucket.bucket_name
                       })

        webui_origin_access_identity = cloudfront.OriginAccessIdentity(self, "WebUIBucketOriginAccessIdentity",
                                                                       comment=f"fOriginAccessIdentity for {self.webui_bucket.bucket_name}")

        self.webui_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                principals=[iam.ArnPrincipal(f"arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity{webui_origin_access_identity.origin_access_identity_id}")],
                resources=[self.webui_bucket.bucket_arn],
            )
        )

        self.distribution = cloudfront.CloudFrontWebDistribution(self, "WebUICDN",
                                                                 comment=f"Retail Demo Store CDN for {self.webui_bucket.bucket_name}",
                                                                 default_root_object="index.html",
                                                                 price_class=cloudfront.PriceClass.PRICE_CLASS_100,
                                                                 http_version=cloudfront.HttpVersion.HTTP2,
                                                                 viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.ALLOW_ALL,
                                                                 origin_configs=[cloudfront.SourceConfiguration(
                                                                     s3_origin_source=cloudfront.S3OriginConfig(
                                                                         s3_bucket_source=self.webui_bucket,
                                                                         origin_access_identity=webui_origin_access_identity
                                                                     ),
                                                                     behaviors=[cloudfront.Behavior(is_default_behavior=True)],
                                                                 )]
                                                             )

        """
        Swagger UI
        """

        self.swaggerui_bucket = s3.Bucket(self, "SwaggerUIBucket",
                                     versioned=True,
                                     encryption=s3.BucketEncryption.S3_MANAGED,
                                     server_access_logs_bucket=props['logging_bucket'],
                                     server_access_logs_prefix="swaggerui-logs",
                                     website_index_document="index.html")

        # Empties bucket when stack is deleted
        CustomResource(self, "EmptyWebUIBucEmptySwaggerUIBucketket",
                       resource_type="Custom::EmptyStackBucket",
                       service_token=props['cleanup_bucket_lambda_arn'],
                       properties={
                           "bucket_name": self.swaggerui_bucket.bucket_name
                       })

        swaggerui_origin_access_identity = cloudfront.OriginAccessIdentity(self, "SwaggerUIBucketOriginAccessIdentity",
                                                                           comment=f"fOriginAccessIdentity for {self.swaggerui_bucket.bucket_name}")

        self.swaggerui_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                principals=[iam.ArnPrincipal(f"arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity{swaggerui_origin_access_identity.origin_access_identity_id}")],
                resources=[self.swaggerui_bucket.bucket_arn],
            )
        )

        self.swaggerui_distribution = cloudfront.CloudFrontWebDistribution(self, "SwaggerUICDN",
                                                                           comment=f"Swagger UI CDN for {self.swaggerui_bucket.bucket_name}",
                                                                           default_root_object="index.html",
                                                                           price_class=cloudfront.PriceClass.PRICE_CLASS_100,
                                                                           http_version=cloudfront.HttpVersion.HTTP2,
                                                                           viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.ALLOW_ALL,
                                                                           origin_configs=[cloudfront.SourceConfiguration(
                                                                               s3_origin_source=cloudfront.S3OriginConfig(
                                                                                   s3_bucket_source=self.swaggerui_bucket,
                                                                                   origin_access_identity=swaggerui_origin_access_identity
                                                                               ),
                                                                               behaviors=[cloudfront.Behavior(is_default_behavior=True)],
                                                                           )]
                                                                       )
