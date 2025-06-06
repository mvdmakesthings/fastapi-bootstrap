"""
AWS utility functions for CLI commands.
"""

from typing import Optional

import boto3


def get_aws_session(
    profile_name: Optional[str] = None,
    region_name: Optional[str] = None,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_session_token: Optional[str] = None,
):
    """
    Create a boto3 session with the specified profile and region or credentials.

    Args:
        profile_name: AWS profile name to use
        region_name: AWS region to use
        aws_access_key_id: AWS access key ID
        aws_secret_access_key: AWS secret access key
        aws_session_token: AWS session token

    Returns:
        boto3.Session: Configured AWS session
    """
    return boto3.Session(
        profile_name=profile_name,
        region_name=region_name,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
    )


def get_account_id(session: Optional[boto3.Session] = None) -> str:
    """
    Get the AWS account ID for the current session.

    Args:
        session: Boto3 session to use

    Returns:
        str: AWS account ID
    """
    if session is None:
        session = get_aws_session()

    sts_client = session.client("sts")
    return sts_client.get_caller_identity()["Account"]


def create_s3_bucket(
    bucket_name: str, region: str, session: Optional[boto3.Session] = None
) -> bool:
    """
    Create an S3 bucket with the specified name.

    Args:
        bucket_name: Name of the S3 bucket to create
        region: AWS region to create the bucket in
        session: Boto3 session to use

    Returns:
        bool: True if bucket was created or already exists, False otherwise
    """
    if session is None:
        session = get_aws_session(region_name=region)

    s3_client = session.client("s3")

    try:
        # Create the bucket
        if region == "us-east-1":
            # us-east-1 requires a different API call
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": region},
            )

        # Enable versioning
        s3_client.put_bucket_versioning(
            Bucket=bucket_name, VersioningConfiguration={"Status": "Enabled"}
        )

        # Enable encryption
        s3_client.put_bucket_encryption(
            Bucket=bucket_name,
            ServerSideEncryptionConfiguration={
                "Rules": [
                    {"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}
                ]
            },
        )

        return True

    except s3_client.exceptions.BucketAlreadyOwnedByYou:
        # Bucket already exists and is owned by this account
        return True
    except Exception as e:
        print(f"Error creating S3 bucket: {e}")
        return False


def create_dynamodb_table(
    table_name: str, region: str, session: Optional[boto3.Session] = None
) -> bool:
    """
    Create a DynamoDB table for state locking.

    Args:
        table_name: Name of the DynamoDB table to create
        region: AWS region to create the table in
        session: Boto3 session to use

    Returns:
        bool: True if table was created or already exists, False otherwise
    """
    if session is None:
        session = get_aws_session(region_name=region)

    dynamodb_client = session.client("dynamodb")

    try:
        # Create the table
        dynamodb_client.create_table(
            TableName=table_name,
            KeySchema=[{"AttributeName": "LockID", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "LockID", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        # Wait for table to be created
        dynamodb_client.get_waiter("table_exists").wait(TableName=table_name)
        return True

    except dynamodb_client.exceptions.ResourceInUseException:
        # Table already exists
        return True
    except Exception as e:
        print(f"Error creating DynamoDB table: {e}")
        return False


def create_kms_key(
    description: str,
    alias_name: str,
    region: str,
    session: Optional[boto3.Session] = None,
) -> Optional[str]:
    """
    Create a KMS key for encryption.

    Args:
        description: Description of the KMS key
        alias_name: Alias name for the key (without the 'alias/' prefix)
        region: AWS region to create the key in
        session: Boto3 session to use

    Returns:
        Optional[str]: KMS key ID if created successfully, None otherwise
    """
    if session is None:
        session = get_aws_session(region_name=region)

    kms_client = session.client("kms")

    try:
        # Check if alias already exists
        try:
            response = kms_client.describe_key(KeyId=f"alias/{alias_name}")
            # Key already exists, return its ID
            return response["KeyMetadata"]["KeyId"]
        except kms_client.exceptions.NotFoundException:
            # Alias doesn't exist, create a new key
            response = kms_client.create_key(Description=description)
            key_id = response["KeyMetadata"]["KeyId"]

            # Create alias
            kms_client.create_alias(AliasName=f"alias/{alias_name}", TargetKeyId=key_id)

            return key_id

    except Exception as e:
        print(f"Error creating KMS key: {e}")
        return None


def put_ssm_parameter(
    name: str,
    value: str,
    parameter_type: str,
    region: str,
    session: Optional[boto3.Session] = None,
    key_id: Optional[str] = None,
) -> bool:
    """
    Create or update an SSM parameter.

    Args:
        name: Parameter name
        value: Parameter value
        parameter_type: Parameter type (String, StringList, SecureString)
        region: AWS region
        session: Boto3 session to use
        key_id: KMS key ID for encryption (only used if parameter_type is SecureString)

    Returns:
        bool: True if parameter was created/updated successfully, False otherwise
    """
    if session is None:
        session = get_aws_session(region_name=region)

    ssm_client = session.client("ssm")

    try:
        params = {
            "Name": name,
            "Value": value,
            "Type": parameter_type,
            "Overwrite": True,
        }

        if parameter_type == "SecureString" and key_id:
            params["KeyId"] = key_id

        ssm_client.put_parameter(**params)
        return True

    except Exception as e:
        print(f"Error creating/updating SSM parameter: {e}")
        return False


def get_ecr_repository_uri(
    repository_name: str, session: Optional[boto3.Session] = None
) -> Optional[str]:
    """
    Get the URI for an ECR repository.

    Args:
        repository_name: Name of the ECR repository
        session: Boto3 session to use

    Returns:
        str: Repository URI if found, None otherwise
    """
    if session is None:
        session = get_aws_session()

    ecr_client = session.client("ecr")

    try:
        response = ecr_client.describe_repositories(repositoryNames=[repository_name])
        if response["repositories"]:
            return response["repositories"][0]["repositoryUri"]
    except ecr_client.exceptions.RepositoryNotFoundException:
        return None
    except Exception as e:
        print(f"Error getting ECR repository URI: {e}")
        return None
