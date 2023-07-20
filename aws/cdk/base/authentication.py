from aws_cdk import (
    Stack,
    Aws,
    aws_iam as iam,
    aws_cognito as cognito
)
from constructs import Construct

class AuthenticationStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        """
        Creates a role that allows Cognito to send SNS messages
        """
        iam.Role(self, "SNSRole",
                 assumed_by=iam.ServicePrincipal("cognito-idp.amazonaws.com"),
                 inline_policies={
                     "CognitoSNSPolicy": iam.PolicyDocument(
                          statements=[iam.PolicyStatement(
                          actions=["sns:publish"],
                          resources=["*"])]
                     )
                 })

        """
        Creates a user pool in cognito for your app to auth against
        This example requires MFA and validates the phone number to use as MFA
        Other fields can be added to the schema
        """
        self.user_pool = cognito.CfnUserPool(self, "UserPool",
                                             user_pool_name=f"{props['auth_name']}-user-pool",
                                             mfa_configuration="OFF",
                                             auto_verified_attributes=["email"],
                                             schema=[
                                                 cognito.CfnUserPool.SchemaAttributeProperty(
                                                     name="email",
                                                     attribute_data_type="String",
                                                     developer_only_attribute=False,
                                                     mutable=False,
                                                     required=True,
                                                     string_attribute_constraints=cognito.CfnUserPool.StringAttributeConstraintsProperty(
                                                         max_length="200",
                                                         min_length="1"
                                                     )
                                                 ),
                                                 cognito.CfnUserPool.SchemaAttributeProperty(
                                                     name="profile_user_id",
                                                     attribute_data_type="String",
                                                     developer_only_attribute=False,
                                                     mutable=True,
                                                     required=False,
                                                     string_attribute_constraints=cognito.CfnUserPool.StringAttributeConstraintsProperty(
                                                         max_length="200",
                                                         min_length="1"
                                                     )
                                                 ),
                                                 cognito.CfnUserPool.SchemaAttributeProperty(
                                                     name="profile_email",
                                                     attribute_data_type="String",
                                                     developer_only_attribute=False,
                                                     mutable=True,
                                                     required=False,
                                                     string_attribute_constraints=cognito.CfnUserPool.StringAttributeConstraintsProperty(
                                                         max_length="200",
                                                         min_length="1"
                                                     )
                                                 ),
                                                 cognito.CfnUserPool.SchemaAttributeProperty(
                                                     name="profile_first_name",
                                                     attribute_data_type="String",
                                                     developer_only_attribute=False,
                                                     mutable=True,
                                                     required=False,
                                                     string_attribute_constraints=cognito.CfnUserPool.StringAttributeConstraintsProperty(
                                                         max_length="200",
                                                         min_length="1"
                                                     )
                                                 ),
                                                 cognito.CfnUserPool.SchemaAttributeProperty(
                                                     name="profile_last_name",
                                                     attribute_data_type="String",
                                                     developer_only_attribute=False,
                                                     mutable=True,
                                                     required=False,
                                                     string_attribute_constraints=cognito.CfnUserPool.StringAttributeConstraintsProperty(
                                                         max_length="200",
                                                         min_length="1"
                                                     )
                                                 ),
                                                 cognito.CfnUserPool.SchemaAttributeProperty(
                                                     name="profile_gender",
                                                     attribute_data_type="String",
                                                     developer_only_attribute=False,
                                                     mutable=True,
                                                     required=False,
                                                     string_attribute_constraints=cognito.CfnUserPool.StringAttributeConstraintsProperty(
                                                         max_length="200",
                                                         min_length="1"
                                                     )
                                                 ),
                                                 cognito.CfnUserPool.SchemaAttributeProperty(
                                                     name="profile_age",
                                                     attribute_data_type="String",
                                                     developer_only_attribute=False,
                                                     mutable=True,
                                                     required=False,
                                                     string_attribute_constraints=cognito.CfnUserPool.StringAttributeConstraintsProperty(
                                                         max_length="200",
                                                         min_length="1"
                                                     )
                                                 ),
                                                 cognito.CfnUserPool.SchemaAttributeProperty(
                                                     name="profile_persona",
                                                     attribute_data_type="String",
                                                     developer_only_attribute=False,
                                                     mutable=True,
                                                     required=False,
                                                     string_attribute_constraints=cognito.CfnUserPool.StringAttributeConstraintsProperty(
                                                         max_length="200",
                                                         min_length="1"
                                                     )
                                                 ),
                                                 cognito.CfnUserPool.SchemaAttributeProperty(
                                                     name="demo_journey",
                                                     attribute_data_type="String",
                                                     developer_only_attribute=False,
                                                     mutable=True,
                                                     required=False,
                                                     string_attribute_constraints=cognito.CfnUserPool.StringAttributeConstraintsProperty(
                                                         max_length="200",
                                                         min_length="1"
                                                     )
                                                 )
                                             ])

        """
        Creates a User Pool Client to be used by the identity pool
        """
        self.user_pool_client = cognito.CfnUserPoolClient(self, "UserPoolClient",
                                                          user_pool_id=self.user_pool.ref,
                                                          generate_secret=False,
                                                          client_name=f"{props['auth_name']}-client")

        """
        Creates a federeated Identity pool
        """
        self.identity_pool = cognito.CfnIdentityPool(self, "IdentityPool",
                                                     identity_pool_name=f"{props['auth_name']}Identity",
                                                     allow_unauthenticated_identities=True,
                                                     cognito_identity_providers=[
                                                         cognito.CfnIdentityPool.CognitoIdentityProviderProperty(
                                                             client_id=self.user_pool_client.ref,
                                                             provider_name=self.user_pool.attr_provider_name,
                                                             server_side_token_check=False
                                                         )
                                                     ])

        """
        Create a role for authorized access to AWS resources. 
        Control what your user can access. This example only allows Lambda invokation
        Only allows users in the previously created Identity Pool
        """
        cognito_authorized_role = iam.Role(self, "CognitoAuthorizedRole",
                                           assumed_by=iam.FederatedPrincipal("cognito-identity.amazonaws.com", {
                                                                                 "StringEquals": {"cognito-identity.amazonaws.com:aud": [self.identity_pool.ref]},
                                                                                 "ForAnyValue:StringLike": {"cognito-identity.amazonaws.com:amr": ['authenticated']}
                                                                             }, "sts:AssumeRoleWithWebIdentity"),
                                           inline_policies={
                                               "CognitoAuthorizedPolicy": iam.PolicyDocument(
                                                   statements=[iam.PolicyStatement(
                                                       actions=[
                                                           "mobiletargeting:UpdateEndpoint",
                                                           "mobiletargeting:PutEvents"
                                                       ],
                                                       resources=[f"arn:aws:mobiletargeting:{Aws.REGION}:{Aws.ACCOUNT_ID}:apps/{props['pinpoint_app_id']}/*"]
                                                   ),
                                                   iam.PolicyStatement(
                                                      actions=[
                                                          "mobileanalytics:PutEvents",
                                                          "personalize:PutEvents",
                                                      ],
                                                      resources=["*"]
                                                   ),
                                                   iam.PolicyStatement(
                                                       actions=["cognito-identity:*"],
                                                       resources=[f"arn:aws:cognito-identity:{Aws.REGION}:{Aws.ACCOUNT_ID}:identitypool/{self.identity_pool.ref}"]
                                                   ),
                                                   iam.PolicyStatement(
                                                       actions=["cognito-sync:*"],
                                                       resources=[f"arn:aws:cognito-sync:{Aws.REGION}:{Aws.ACCOUNT_ID}:identitypool/{self.identity_pool.ref}"]
                                                   ),
                                                   iam.PolicyStatement(
                                                       actions=["lex:PostText"],
                                                       resources=[f"arn:aws:lex:{Aws.REGION}:{Aws.ACCOUNT_ID}:bot:RetailDemoStore:*"]
                                                   ),
                                                   iam.PolicyStatement(
                                                       actions=[
                                                           "geo:BatchGetDevicePosition",
                                                           "geo:BatchUpdateDevicePosition",
                                                           "geo:DescribeTracker",
                                                           "geo:GetDevicePosition",
                                                           "geo:GetDevicePositionHistory",
                                                           "geo:ListDevicePositions",
                                                           "geo:ListTrackers"
                                                       ],
                                                       resources=[f"arn:aws:geo:{Aws.REGION}:{Aws.ACCOUNT_ID}:tracker/{props['location_resource_prefix']}*"]
                                                   ),
                                                   iam.PolicyStatement(
                                                       actions=[
                                                           "geo:ListGeofences",
                                                           "geo:ListGeofenceCollections",
                                                           "geo:GetGeofence",
                                                           "geo:DescribeGeofenceCollection"
                                                       ],
                                                       resources=[f"arn:aws:geo:{Aws.REGION}:{Aws.ACCOUNT_ID}:geofence-collection/{props['location_resource_prefix']}*"]
                                                   ),
                                                   iam.PolicyStatement(
                                                       actions=[
                                                           "geo:GetMapGlyphs",
                                                           "geo:GetMapSprites",
                                                           "geo:GetMapStyleDescriptor",
                                                           "geo:GetMapTile",
                                                           "geo:DescribeMap",
                                                           "geo:ListMaps"
                                                       ],
                                                       resources=[f"arn:aws:geo:{Aws.REGION}:{Aws.ACCOUNT_ID}:map/{props['location_resource_prefix']}*"]
                                                   )]
                                               )
                                           })

        """
        # Create a role for unauthorized access to AWS resources. Very limited access. 
        Only allows users in the previously created Identity Pool
        """
        cognito_unauthorized_role = iam.Role(self, "CognitoUnAuthorizedRole",
                                             assumed_by=iam.FederatedPrincipal("cognito-identity.amazonaws.com", {
                                                 "StringEquals": {"cognito-identity.amazonaws.com:aud": [self.identity_pool.ref]},
                                                 "ForAnyValue:StringLike": {"cognito-identity.amazonaws.com:amr": ['authenticated']}
                                             }, "sts:AssumeRoleWithWebIdentity"),
                                             inline_policies={
                                                 "CognitoUnauthorizedPolicy": iam.PolicyDocument(
                                                     statements=[iam.PolicyStatement(
                                                         actions=[
                                                             "mobiletargeting:UpdateEndpoint",
                                                             "mobiletargeting:PutEvents"
                                                         ],
                                                         resources=[
                                                             f"arn:aws:mobiletargeting:{Aws.REGION}:{Aws.ACCOUNT_ID}:apps/{props['pinpoint_app_id']}/*"]
                                                     ),
                                                         iam.PolicyStatement(
                                                             actions=[
                                                                 "mobileanalytics:PutEvents",
                                                                 "personalize:PutEvents",
                                                             ],
                                                             resources=["*"]
                                                         ),
                                                         iam.PolicyStatement(
                                                             actions=["cognito-sync:*"],
                                                             resources=[
                                                                 f"arn:aws:cognito-sync:{Aws.REGION}:{Aws.ACCOUNT_ID}:identitypool/{self.identity_pool.ref}"]
                                                         ),
                                                         iam.PolicyStatement(
                                                             actions=["lex:PostText"],
                                                             resources=[
                                                                 f"arn:aws:lex:{Aws.REGION}:{Aws.ACCOUNT_ID}:bot:RetailDemoStore:*"]
                                                         )
                                                     ]
                                                 )
                                             })

        cognito.CfnIdentityPoolRoleAttachment(self, "IdentityPoolRoleMapping",
                                              identity_pool_id=self.identity_pool.ref,
                                              roles={
                                                  "authenticated": cognito_authorized_role.role_arn,
                                                  "unauthenticated": cognito_unauthorized_role.role_arn
                                              })
