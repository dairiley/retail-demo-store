from aws_cdk import (
    Stack,
    Duration,
    aws_ssm as ssm
)
from constructs import Construct

class SsmStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ssm.StringParameter(self, "ParameterStackBucketName",
                            parameter_name="retaildemostore-stack-bucket",
                            string_value=props['stack_bucket_name'],
                            description="Retail Demo Store Stack Bucket Parameter")

        ssm.StringParameter(self, "ParameterPersonalizeRelatedItemsArn",
                            parameter_name="/retaildemostore/personalize/related-items-arn",
                            string_value="NONE",
                            description="Retail Demo Store Related Items Campaign/Recommender Arn Parameter")

        ssm.StringParameter(self, "ParameterPersonalizePopularItemsArn",
                            parameter_name="/retaildemostore/personalize/popular-items-arn",
                            string_value="NONE",
                            description="Retail Demo Store Popular Items Campaign/Recommender Arn Parameter")

        ssm.StringParameter(self, "ParameterPersonalizeRecommendedForYouArn",
                            parameter_name="/retaildemostore/personalize/recommended-for-you-arn",
                            string_value="NONE",
                            description="Retail Demo Store Recommended For You Campaign/Recommender Arn Parameter")

        ssm.StringParameter(self, "ParameterPersonalizePersonalizedRankingArn",
                            parameter_name="/retaildemostore/personalize/personalized-ranking-arn",
                            string_value="NONE",
                            description="Retail Demo Store Personalized Ranking Campaign/Recommender Arn Parameter")

        ssm.StringParameter(self, "ParameterPersonalizePersonalizedOffersArn",
                            parameter_name="/retaildemostore/personalize/personalized-offers-arn",
                            string_value="NONE",
                            description="Retail Demo Store Personalized Coupon Offers Campaign/Recommender Arn Parameter")

        ssm.StringParameter(self, "ParameterPersonalizeFilterPurchasedArn",
                            parameter_name="/retaildemostore/personalize/filters/filter-purchased-arn",
                            string_value="NONE",
                            description="Retail Demo Store Personalize Filter Purchased Products Arn Parameter")

        ssm.StringParameter(self, "ParameterPersonalizeFilterCStoreArn",
                            parameter_name="/retaildemostore/personalize/filters/filter-cstore-arn",
                            string_value="NONE",
                            description="Retail Demo Store Filter C-Store Products Arn Parameter")

        ssm.StringParameter(self, "ParameterPersonalizeFilterPurchasedAndCStoreArn",
                            parameter_name="/retaildemostore/personalize/filters/filter-purchased-and-cstore-arn",
                            string_value="NONE",
                            description="Retail Demo Store Filter Purchased and C-Store Products Arn Parameter")

        ssm.StringParameter(self, "ParameterPersonalizeFilterIncludeCategoriesArn",
                            parameter_name="/retaildemostore/personalize/filters/filter-include-categories-arn",
                            string_value="NONE",
                            description="Retail Demo Store Filter to Include by Categories Arn Parameter")

        ssm.StringParameter(self, "ParameterPersonalizePromotedItemsFilterArn",
                            parameter_name="/retaildemostore/personalize/filters/promoted-items-filter-arn",
                            string_value="NONE",
                            description="Retail Demo Store Promotional Filter to Include Promoted Items Arn Parameter")

        ssm.StringParameter(self, "ParameterPersonalizePromotedItemsNoCStoreFilterArn",
                            parameter_name="/retaildemostore/personalize/filters/promoted-items-no-cstore-filter-arn",
                            string_value="NONE",
                            description="Retail Demo Store Promotional Filter to Include Promoted Non CStore Items Arn Parameter")

        self.parameter_personalize_event_tracker_id = ssm.StringParameter(self, "ParameterPersonalizeEventTrackerId",
                                                                          parameter_name="/retaildemostore/personalize/event-tracker-id",
                                                                          string_value="NONE",
                                                                          description="Retail Demo Store Personalize Event Tracker ID Parameter")

        ssm.StringParameter(self, "ParameterExperimentStrategyTableName",
                            parameter_name="retaildemostore-experiment-strategy-table-name",
                            string_value=props['experiment_strategy_table_name'],
                            description="Retail Demo Store Experiment Strategy DDB Table Name")

        if props['amplitude_api_key'] == "":
            props['amplitude_api_key'] = "NONE"
        self.parameter_amplitude_api_key = ssm.StringParameter(self, "ParameterAmplitudeApiKey",
                                                               parameter_name="retaildemostore-amplitude-api-key",
                                                               string_value=props['amplitude_api_key'],
                                                               description="Retail Demo Store Amplitude API key")

        if props['optimizely_sdk_key'] == "":
            props['optimizely_sdk_key'] = "NONE"
        self.parameter_optimizely_sdk_key = ssm.StringParameter(self, "ParameterOptimizelySdkKey",
                                                                parameter_name="retaildemostore-optimizely-sdk-key",
                                                                string_value=props['optimizely_sdk_key'],
                                                                description="Retail Demo Store Optimizely SDK key")

        self.parameter_ivs_video_channel_map = ssm.StringParameter(self, "ParameterIVSVideoChannelMap",
                                                                   parameter_name="retaildemostore-ivs-video-channel-map",
                                                                   string_value="NONE",
                                                                   description="Retail Demo Store video file to IVS channel mapping")

        if props['segment_write_key'] == "":
            props['segment_write_key'] = "NONE"
        self.parameter_segment_write_key = ssm.StringParameter(self, "ParameterSegmentWriteKey",
                                                               parameter_name="retaildemostore-segment-write-key",
                                                               string_value=props['segment_write_key'],
                                                               description="Retail Demo Store Segment source write key")

        if props['mparticle_org_id'] == "":
            props['mparticle_org_id'] = "NONE"
        ssm.StringParameter(self, "ParametermParticleOrgId",
                            parameter_name="retaildemostore-mparticle-org-id",
                            string_value=props['mparticle_org_id'],
                            description="Retail Demo Store mParticle org id")

        if props['mparticle_api_key'] == "":
            props['mparticle_api_key'] = "NONE"
        ssm.StringParameter(self, "ParametermParticleApiKey",
                            parameter_name="/retaildemostore/webui/mparticle_api_key",
                            string_value=props['mparticle_api_key'],
                            description="Retail Demo Store mParticle API key")

        if props['mparticle_secret_key'] == "":
            props['mparticle_secret_key'] = "NONE"
        ssm.StringParameter(self, "ParametermParticleSecretKey",
                            parameter_name="/retaildemostore/webui/mparticle_secret_key",
                            string_value=props['mparticle_secret_key'],
                            description="Retail Demo Store mParticle secret key")

        if props['mparticle_s2s_api_key'] == "":
            props['mparticle_s2s_api_key'] = "NONE"
        ssm.StringParameter(self, "ParametermParticleS2SApiKey",
                            parameter_name="/retaildemostore/webui/mparticle_s2s_api_key",
                            string_value=props['mparticle_s2s_api_key'],
                            description="Retail Demo Store mParticle server to server API key - used for Kinesis processing")

        if props['mparticle_s2s_secret_key'] == "":
            props['mparticle_s2s_secret_key'] = "NONE"
        ssm.StringParameter(self, "ParametermParticleS2SSecretKey",
                            parameter_name="/retaildemostore/webui/mparticle_s2s_secret_key",
                            string_value=props['mparticle_s2s_secret_key'],
                            description="Retail Demo Store mParticle server to server secret key - used for Kinesis processing")

        if props['pinpoint_sms_long_code'] == "":
            props['pinpoint_sms_long_code'] = "NONE"
        ssm.StringParameter(self, "ParameterPinpointSMSLongCode",
                            parameter_name="retaildemostore-pinpoint-sms-longcode",
                            string_value=props['pinpoint_sms_long_code'],
                            description="Retail Demo Store Pinpoint SMS Long code")

        if props['google_analytics_measurement_id'] == "":
            props['google_analytics_measurement_id'] = "NONE"
        self.parameter_google_analytics_measurement_id = ssm.StringParameter(self, "ParameterGoogleAnalyticsMeasurementId",
                                                                             parameter_name="retaildemostore-google-analytics-measurement-id",
                                                                             string_value=props['google_analytics_measurement_id'],
                                                                             description="Retail Demo Store Google Analytics Measurement Id")
