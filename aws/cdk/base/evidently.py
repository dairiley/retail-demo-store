from aws_cdk import (
    Stack,
    Duration,
    Aws,
    aws_evidently as evidently,
    aws_iam as iam,
    aws_lambda as lambda_,
    BundlingOptions
)
from constructs import Construct

class EvidentlyStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        evidently_project = evidently.CfnProject(self, "EvidentlyProject",
                                                 name=props['uid'],
                                                 description="Retail Demo Store features and experiments")

        evidently.CfnFeature(self, "FeatureHomeProductRecs",
                             name="home_product_recs",
                             project=evidently_project.ref,
                             default_variation="Personalize-UserPersonalization",
                             description="Home page product recommendations",
                             evaluation_strategy="ALL_RULES",
                             variations=[
                                 evidently.CfnFeature.VariationObjectProperty(
                                     variation_name="FeaturedProducts",
                                     string_value='{"type":"product"}'
                                 ),
                                 evidently.CfnFeature.VariationObjectProperty(
                                     variation_name="Personalize-UserPersonalization",
                                     string_value='{"type":"personalize-recommendations","arn":"arn:'+Aws.PARTITION+':personalize:'+Aws.REGION+':'+Aws.ACCOUNT_ID +':recommender/retaildemostore-recommended-for-you"}'
                                 ),
                             ])

        evidently.CfnFeature(self, "FeatureHomeProductRecsCold",
                             name="home_product_recs_cold",
                             project=evidently_project.ref,
                             default_variation="Personalize-PopularItems",
                             description="Home page product recommendations for new/cold users",
                             evaluation_strategy="ALL_RULES",
                             variations=[
                                 evidently.CfnFeature.VariationObjectProperty(
                                     variation_name="FeaturedProducts",
                                     string_value='{"type":"product"}'
                                 ),
                                 evidently.CfnFeature.VariationObjectProperty(
                                     variation_name="Personalize-PopularItems",
                                     string_value='{"type":"personalize-recommendations","arn":"arn:'+Aws.PARTITION+':personalize:'+Aws.REGION+':'+Aws.ACCOUNT_ID +':recommender/retaildemostore-popular-items"}'
                                 )
                             ])

        evidently.CfnFeature(self, "FeatureHomeFeaturedRerank",
                             name="home_featured_rerank",
                             project=evidently_project.ref,
                             default_variation="Personalize-PopularItems",
                             description="Home page featured products carousel",
                             evaluation_strategy="ALL_RULES",
                             variations=[
                                 evidently.CfnFeature.VariationObjectProperty(
                                     variation_name="RankingNoOp",
                                     string_value='{"type":"ranking-no-op"}'
                                 ),
                                 evidently.CfnFeature.VariationObjectProperty(
                                     variation_name="Personalize-PopularItems",
                                     string_value='{"type":"personalize-ranking","arn":"arn:'+Aws.PARTITION+':personalize:'+Aws.REGION+':'+Aws.ACCOUNT_ID +':campaign/retaildemostore-personalized-ranking"}'
                                 )
                             ])

        evidently.CfnFeature(self, "FeatureProductDetailRelated",
                             name="product_detail_related",
                             project=evidently_project.ref,
                             default_variation="Personalize-Similar-Items",
                             description="Product detail related products carousel",
                             evaluation_strategy="ALL_RULES",
                             variations=[
                                 evidently.CfnFeature.VariationObjectProperty(
                                     variation_name="ProductsInSameCategory",
                                     string_value='{"type":"product"}'
                                 ),
                                 evidently.CfnFeature.VariationObjectProperty(
                                     variation_name="OpenSearchMoreLikeThis",
                                     string_value='{"type":"similar"}'
                                 ),
                                 evidently.CfnFeature.VariationObjectProperty(
                                     variation_name="Personalize-Similar-Items",
                                     string_value='{"type":"personalize-recommendations","arn":"arn:'+Aws.PARTITION+':personalize:'+Aws.REGION+':'+Aws.ACCOUNT_ID +':campaign/retaildemostore-related-items"}'
                                 )
                             ])

        evidently.CfnFeature(self, "FeatureSearchResults",
                             name="search_results",
                             project=evidently_project.ref,
                             default_variation="Personalize-PersonalizedRanking",
                             description="Search control auto-complete",
                             evaluation_strategy="ALL_RULES",
                             variations=[
                                 evidently.CfnFeature.VariationObjectProperty(
                                     variation_name="RankingNoOp",
                                     string_value='{"type":"ranking-no-op"}'
                                 ),
                                 evidently.CfnFeature.VariationObjectProperty(
                                     variation_name="Personalize-PersonalizedRanking",
                                     string_value='{"type":"personalize-ranking","arn":"arn:'+Aws.PARTITION+':personalize:'+Aws.REGION+':'+Aws.ACCOUNT_ID +':campaign/retaildemostore-personalized-ranking"}'
                                 )
                             ])

        evidently.CfnFeature(self, "FeatureLiveStreamProductRecs",
                             name="live_stream_prod_recommendation",
                             project=evidently_project.ref,
                             default_variation="Personalize-PersonalizedRanking",
                             description="Live stream product recommendations",
                             evaluation_strategy="ALL_RULES",
                             variations=[
                                 evidently.CfnFeature.VariationObjectProperty(
                                     variation_name="RankingNoOp",
                                     string_value='{"type":"ranking-no-op"}'
                                 ),
                                 evidently.CfnFeature.VariationObjectProperty(
                                     variation_name="Personalize-PersonalizedRanking",
                                     string_value='{"type":"personalize-ranking","arn":"arn:'+Aws.PARTITION+':personalize:'+Aws.REGION+':'+Aws.ACCOUNT_ID +':campaign/retaildemostore-personalized-ranking"}'
                                 )
                             ])

        evidently.CfnFeature(self, "FeatureLiveStreamProductDiscounts",
                             name="live_stream_prod_discounts",
                             project=evidently_project.ref,
                             default_variation="Personalize-PersonalizedRanking",
                             description="Live stream product discounts",
                             evaluation_strategy="ALL_RULES",
                             variations=[
                                 evidently.CfnFeature.VariationObjectProperty(
                                     variation_name="RankingNoOp",
                                     string_value='{"type":"ranking-no-op"}'
                                 ),
                                 evidently.CfnFeature.VariationObjectProperty(
                                     variation_name="Personalize-PersonalizedRanking",
                                     string_value='{"type":"personalize-ranking","arn":"arn:'+Aws.PARTITION+':personalize:'+Aws.REGION+':'+Aws.ACCOUNT_ID +':campaign/retaildemostore-personalized-ranking"}'
                                 )
                             ])

        evidently_cleanup_execution_role = iam.Role(self, "EvidentlyCleanupLambdaExecutionRole",
                                                    assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                                    inline_policies={
                                                        "LoggingPolicy": iam.PolicyDocument(
                                                            statements=[iam.PolicyStatement(
                                                                actions=[
                                                                    "logs:CreateLogStream",
                                                                    "logs:PutLogEvents",
                                                                    "logs:CreateLogGroup",
                                                                ],
                                                                resources=["*"]
                                                            )]
                                                        ),
                                                        "Evidently": iam.PolicyDocument(
                                                             statements=[iam.PolicyStatement(
                                                                 actions=["evidently:*"],
                                                                 resources=["*"]
                                                             )]
                                                         )
                                                    })

        lambda_.Function(self, "EvidentlyCleanupLambdaFunction",
                         runtime=lambda_.Runtime.PYTHON_3_10 ,
                         description="Retail Demo Store deployment utility function that cancels and deletes experiments to allow project to be fully deleted",
                         handler="index.handler",
                         code=lambda_.Code.from_asset("base/lambda/evidently_cleanup",
                                                      bundling=BundlingOptions(
                                                          image=lambda_.Runtime.PYTHON_3_10.bundling_image,
                                                          command=[
                                                              "bash", "-c",
                                                              "pip install --no-cache -r requirements.txt -t /asset-output && cp -au . /asset-output"
                                                          ],
                                                      )),
                         timeout=Duration.seconds(120),
                         role=evidently_cleanup_execution_role)

