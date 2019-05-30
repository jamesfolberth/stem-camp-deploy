# Setup the IAM account

1. Enter the IAM from the AWS dashboard.
2. Create a user managed force_mfa group Policy:
   Select ‘Policies’ and ‘Create policy’. Enter the JSON tab and replace the text with the following:
```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowAllUsersToListAccounts",
            "Effect": "Allow",
            "Action": [
                "iam:ListAccountAliases",
                "iam:ListUsers",
                "iam:GetAccountSummary"
            ],
            "Resource": "*"
        },
        {
            "Sid": "AllowIndividualUserToSeeAndManageOnlyTheirOwnAccountInformation",
            "Effect": "Allow",
            "Action": [
                "iam:ChangePassword",
                "iam:CreateAccessKey",
                "iam:CreateLoginProfile",
                "iam:DeleteAccessKey",
                "iam:DeleteLoginProfile",
                "iam:GetAccountPasswordPolicy",
                "iam:GetLoginProfile",
                "iam:ListAccessKeys",
                "iam:UpdateAccessKey",
                "iam:UpdateLoginProfile",
                "iam:ListSigningCertificates",
                "iam:DeleteSigningCertificate",
                "iam:UpdateSigningCertificate",
                "iam:UploadSigningCertificate",
                "iam:ListSSHPublicKeys",
                "iam:GetSSHPublicKey",
                "iam:DeleteSSHPublicKey",
                "iam:UpdateSSHPublicKey",
                "iam:UploadSSHPublicKey"
            ],
            "Resource": "arn:aws:iam::accountid:user/${aws:username}"
        },
        {
            "Sid": "AllowIndividualUserToListOnlyTheirOwnMFA",
            "Effect": "Allow",
            "Action": [
                "iam:ListVirtualMFADevices",
                "iam:ListMFADevices"
            ],
            "Resource": [
                "arn:aws:iam::805551924291:mfa/*",
                "arn:aws:iam::805551924291:user/${aws:username}"
            ]
        },
        {
            "Sid": "AllowIndividualUserToManageTheirOwnMFA",
            "Effect": "Allow",
            "Action": [
                "iam:CreateVirtualMFADevice",
                "iam:DeleteVirtualMFADevice",
                "iam:RequestSmsMfaRegistration",
                "iam:FinalizeSmsMfaRegistration",
                "iam:EnableMFADevice",
                "iam:ResyncMFADevice"
            ],
            "Resource": [
                "arn:aws:iam::805551924291:mfa/${aws:username}",
                "arn:aws:iam::805551924291:user/${aws:username}"
            ]
        },
        {
            "Sid": "AllowIndividualUserToDeactivateOnlyTheirOwnMFAOnlyWhenUsingMFA",
            "Effect": "Allow",
            "Action": [
                "iam:DeactivateMFADevice"
            ],
            "Resource": [
                "arn:aws:iam::805551924291:mfa/${aws:username}",
                "arn:aws:iam::805551924291:user/${aws:username}"
            ],
            "Condition": {
                "Bool": {
                    "aws:MultiFactorAuthPresent": "true"
                }
            }
        },
        {
            "Sid": "BlockAnyAccessOtherThanAboveUnlessSignedInWithMFA",
            "Effect": "Deny",
            "NotAction": "iam:*",
            "Resource": "*",
            "Condition": {
                "BoolIfExists": {
                    "aws:MultiFactorAuthPresent": "false"
                }
            }
        }
    ]
}
```
Confirm and exit policies.

3. Select ‘Groups’ from the left panel of AMI and ‘create new group’ with the following policies:
   - AmazonEC2FullAcess
   - AmazonS3FullAccess
   - CloudFrontFullAccess
   - AmazonElasticFileSystemFullAccess
   - AmazonRoute53FullAccess
   - AWSCertificateManagerFullAccess
   - Force_mfa(the policy we created above)

4. Go to user tab and click ‘add user’
   - Access type:  AWS Management Console access, the rest default
   - Add the group you created in the previous step
   - No tags
   Make sure to note down both the sign-in link and the password, because you will need it. (should look like this: https://805551924291.signin.aws.amazon.com/console)

5. Under Account settings > STS, deactivate all of the areas that you are not using. For stem camp we only use US West(Oregon).  

6. Set the security on your account. You will be enabling authy, a virtual multi-factor authentication device.
Go to IAM > select user > security credentials and assign your virtual MFA device (preferably your phone with authy)

