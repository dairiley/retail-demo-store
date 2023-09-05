from aws_cdk import (
    Stack,
    aws_s3 as s3,
    Aws,
    aws_cloudfront as cloudfront,
    aws_iam as iam,
    CustomResource,
    Duration
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
                           "BucketName": self.webui_bucket.bucket_name
                       })

        webui_origin_access_identity = cloudfront.OriginAccessIdentity(self, "WebUIBucketOriginAccessIdentity",
                                                                       comment=f"fOriginAccessIdentity for {self.webui_bucket.bucket_name}")

        origin_access_control = cloudfront.CfnOriginAccessControl(self, "UIOriginAccessControl",
                                                                  origin_access_control_config=cloudfront.CfnOriginAccessControl.OriginAccessControlConfigProperty(
                                                                      name=props['stack_name'],
                                                                      origin_access_control_origin_type="s3",
                                                                      signing_behavior="always",
                                                                      signing_protocol="sigv4",
                                                                  ))

        ui_cache_policy = cloudfront.CachePolicy(self, "UICachePolicy",
                                                 cache_policy_name=props['stack_name'],
                                                 default_ttl=Duration.seconds(86400),
                                                 min_ttl=Duration.seconds(86400),
                                                 max_ttl=Duration.seconds(31536000),
                                                 cookie_behavior=cloudfront.CacheCookieBehavior.none(),
                                                 header_behavior=cloudfront.CacheHeaderBehavior.none(),
                                                 query_string_behavior=cloudfront.CacheQueryStringBehavior.all())

        ui_origin_request_policy = cloudfront.OriginRequestPolicy(self, "UIOriginRequestPolicy",
                                                                  origin_request_policy_name="WebUIOriginRequestPolicy",
                                                                  cookie_behavior=cloudfront.OriginRequestCookieBehavior.none(),
                                                                  header_behavior=cloudfront.OriginRequestHeaderBehavior.none(),
                                                                  query_string_behavior=cloudfront.OriginRequestQueryStringBehavior.all())

        self.distribution = cloudfront.CloudFrontWebDistribution(self, "WebUICDN",
                                                                 comment=f"Retail Demo Store CDN for {self.webui_bucket.bucket_name}",
                                                                 default_root_object="index.html",
                                                                 price_class=cloudfront.PriceClass.PRICE_CLASS_100,
                                                                 http_version=cloudfront.HttpVersion.HTTP2_AND_3,
                                                                 viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.ALLOW_ALL,
                                                                 origin_configs=[cloudfront.SourceConfiguration(
                                                                     s3_origin_source=cloudfront.S3OriginConfig(
                                                                         s3_bucket_source=self.webui_bucket,
                                                                         #origin_access_identity=webui_origin_access_identity
                                                                     ),
                                                                     behaviors=[cloudfront.Behavior(
                                                                         is_default_behavior=True,
                                                                         viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS
                                                                     )]
                                                                 )]
                                                             )
        cfn_distribution = self.distribution.node.default_child
        cfn_distribution.add_property_override("DistributionConfig.DefaultCacheBehavior.CachePolicyId", ui_cache_policy.cache_policy_id)
        cfn_distribution.add_property_override("DistributionConfig.DefaultCacheBehavior.OriginRequestPolicyId", ui_origin_request_policy.origin_request_policy_id)
        cfn_distribution.add_property_override('DistributionConfig.Origins.0.OriginAccessControlId', origin_access_control.get_att('Id'))
        cfn_distribution.add_property_override("DistributionConfig.DefaultCacheBehavior.ResponseHeadersPolicyId", "60669652-455b-4ae9-85a4-c4c02393f86c") # id for the SimpleCORS AWS Managed response header policies:https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/using-managed-response-headers-policies.html#managed-response-headers-policies-cors


        self.webui_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                principals=[iam.ServicePrincipal("cloudfront.amazonaws.com",
                                                 conditions={"StringEquals": {
                                                     "AWS:SourceArn": f"arn:aws:cloudfront::{Aws.ACCOUNT_ID}:distribution/{self.distribution.distribution_id}"
                                                 }})],
                resources=[f"{self.webui_bucket.bucket_arn}/*"],
            )
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
        CustomResource(self, "EmptyWebUIBucEmptySwaggerUIBucket",
                       resource_type="Custom::EmptyStackBucket",
                       service_token=props['cleanup_bucket_lambda_arn'],
                       properties={
                           "BucketName": self.swaggerui_bucket.bucket_name
                       })

        swaggerui_origin_access_identity = cloudfront.OriginAccessIdentity(self, "SwaggerUIBucketOriginAccessIdentity",
                                                                           comment=f"fOriginAccessIdentity for {self.swaggerui_bucket.bucket_name}")

        self.swaggerui_distribution = cloudfront.CloudFrontWebDistribution(self, "SwaggerUICDN",
                                                                           comment=f"Swagger UI CDN for {self.swaggerui_bucket.bucket_name}",
                                                                           default_root_object="index.html",
                                                                           price_class=cloudfront.PriceClass.PRICE_CLASS_100,
                                                                           http_version=cloudfront.HttpVersion.HTTP2_AND_3,
                                                                           viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.ALLOW_ALL,
                                                                           origin_configs=[cloudfront.SourceConfiguration(
                                                                               s3_origin_source=cloudfront.S3OriginConfig(
                                                                                   s3_bucket_source=self.swaggerui_bucket,
                                                                                   #origin_access_identity=swaggerui_origin_access_identity
                                                                               ),
                                                                               behaviors=[cloudfront.Behavior(
                                                                                   is_default_behavior=True,
                                                                                   viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS
                                                                               )]
                                                                           )]
                                                                       )
        cfn_distribution = self.swaggerui_distribution.node.default_child
        cfn_distribution.add_property_override("DistributionConfig.DefaultCacheBehavior.CachePolicyId", ui_cache_policy.cache_policy_id)
        cfn_distribution.add_property_override("DistributionConfig.DefaultCacheBehavior.OriginRequestPolicyId", ui_origin_request_policy.origin_request_policy_id)
        cfn_distribution.add_property_override('DistributionConfig.Origins.0.OriginAccessControlId', origin_access_control.get_att('Id'))
        cfn_distribution.add_property_override("DistributionConfig.DefaultCacheBehavior.ResponseHeadersPolicyId", "60669652-455b-4ae9-85a4-c4c02393f86c") # id for the SimpleCORS AWS Managed response header policies:https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/using-managed-response-headers-policies.html#managed-response-headers-policies-cors

        self.swaggerui_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                principals=[iam.ServicePrincipal("cloudfront.amazonaws.com",
                                                 conditions={"StringEquals": {
                                                     "AWS:SourceArn": f"arn:aws:cloudfront::{Aws.ACCOUNT_ID}:distribution/{self.swaggerui_distribution.distribution_id}"
                                                 }})],
                resources=[f"{self.swaggerui_bucket.bucket_arn}/*"],
            )
        )
