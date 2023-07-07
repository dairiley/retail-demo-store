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
        sns_role = iam.Role(self, "SNSRole",
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

        self.user_pool_id_str=f"{props['auth_name']}-client"
        """
        Creates a User Pool Client to be used by the identity pool
        """
        self.user_pool_client = cognito.CfnUserPoolClient(self, "UserPoolClient",
                                                          user_pool_id=self.user_pool.ref,
                                                          generate_secret=False,
                                                          client_name=self.user_pool_id_str)

        """
        Creates a federeated Identity pool
        """
        self.identity_pool = cognito.CfnIdentityPool(self, "IdentityPool",
                                                     identity_pool_name=f"{props['auth_name']}Identity",
                                                     allow_unauthenticated_identities=True,
                                                     cognito_identity_providers=[
                                                         cognito.CfnIdentityPool.CognitoIdentityProviderProperty(
                                                             client_id=self.user_pool_id_str,
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
                                           assumed_by=iam.ServicePrincipal("cognito-identity.amazonaws.com"),
                                           inline_policies={
                                               "CustomPolicy": iam.PolicyDocument(
                                                   statements=[iam.PolicyStatement(
                                                       actions=["sts:AssumeRoleWithWebIdentity"],
                                                       resources=["cognito:*"],
                                                       conditions={
                                                           "StringEquals": {"cognito-identity.amazonaws.com:aud": [self.identity_pool.ref]},
                                                           "ForAnyValue:StringLike": {"cognito-identity.amazonaws.com:amr": ['authenticated']}
                                                       },
                                                   )]
                                               ),
                                               "CognitoAuthorizedPolicy": iam.PolicyDocument(
                                                   statements=[iam.PolicyStatement(
                                                       actions=[
                                                           "mobiletargeting:UpdateEndpoint",
                                                           "mobiletargeting:PutEvents",
                                                           "mobileanalytics:PutEvents",
                                                           "personalize:PutEvents",
                                                           "cognito-identity:*",
                                                           "cognito-sync:*",
                                                           "lex:PostText"
                                                       ],
                                                       resources=[
                                                           f"arn:aws:mobiletargeting:{Aws.REGION}:{Aws.ACCOUNT_ID}:apps/{props['pinpoint_app_id']}/*",
                                                           f"arn:aws:cognito-sync:{Aws.REGION}:{Aws.ACCOUNT_ID}:identitypool/{self.identity_pool.ref}",
                                                           f"arn:aws:lex:{Aws.REGION}:{Aws.ACCOUNT_ID}:bot:RetailDemoStore:*"
                                                       ]
                                                   )]
                                               ),
                                           })

        """
        # Create a role for unauthorized access to AWS resources. Very limited access. 
        Only allows users in the previously created Identity Pool
        """
        cognito_unauthorized_role = iam.Role(self, "CognitoUnAuthorizedRole",
                                           assumed_by=iam.ServicePrincipal("cognito-identity.amazonaws.com"),
                                           inline_policies={
                                               "CustomPolicy": iam.PolicyDocument(
                                                   statements=[iam.PolicyStatement(
                                                       actions=["sts:AssumeRoleWithWebIdentity"],
                                                       resources=["cognito:*"],
                                                       conditions={
                                                           "StringEquals": {"cognito-identity.amazonaws.com:aud": [self.identity_pool.ref]},
                                                           "ForAnyValue:StringLike": {"cognito-identity.amazonaws.com:amr": ['authenticated']}
                                                       },
                                                   )]
                                               ),
                                               "CognitoUnauthorizedPolicy": iam.PolicyDocument(
                                                    statements=[iam.PolicyStatement(
                                                        actions=[
                                                            "mobiletargeting:UpdateEndpoint",
                                                            "mobiletargeting:PutEvents",
                                                            "mobileanalytics:PutEvents",
                                                            "personalize:PutEvents",
                                                            "cognito-identity:*",
                                                            "cognito-sync:*",
                                                            "lex:PostText"
                                                        ],
                                                        resources=[
                                                            f"arn:aws:mobiletargeting:{Aws.REGION}:{Aws.ACCOUNT_ID}:apps/{props['pinpoint_app_id']}/*",
                                                            f"arn:aws:cognito-sync:{Aws.REGION}:{Aws.ACCOUNT_ID}:identitypool/{self.identity_pool.ref}",
                                                            f"arn:aws:lex:{Aws.REGION}:{Aws.ACCOUNT_ID}:bot:RetailDemoStore:*"
                                                        ]
                                                    )]
                                                ),
                                           })

        cognito.CfnIdentityPoolRoleAttachment(self, "IdentityPoolRoleMapping",
                                              identity_pool_id=self.identity_pool.ref,
                                              roles=[{
                                                      "authenticated": cognito_authorized_role.role_arn,
                                                      "unauthenticated": cognito_unauthorized_role.role_arn
                                              }])
