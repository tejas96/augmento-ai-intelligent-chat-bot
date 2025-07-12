import boto3
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from loguru import logger
from botocore.exceptions import ClientError

from config.settings import settings

class S3Service:
    """Service for handling S3 operations"""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            aws_session_token=settings.AWS_SESSION_TOKEN,
        )
        self.bucket_name = settings.S3_BUCKET_NAME
        
    async def generate_presigned_upload_url(
        self,
        filename: str,
        content_type: str,
        expiry_seconds: int = None
    ) -> Dict[str, Any]:
        """Generate presigned URL for image upload"""
        try:
            if expiry_seconds is None:
                expiry_seconds = settings.S3_PRESIGNED_URL_EXPIRY
            
            # Generate unique key
            upload_id = str(uuid.uuid4())
            file_extension = filename.split('.')[-1] if '.' in filename else 'jpg'
            key = f"uploads/{upload_id}.{file_extension}"
            
            # Generate presigned URL
            presigned_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key,
                    'ContentType': content_type,
                },
                ExpiresIn=expiry_seconds
            )
            
            # Generate image access URL
            image_url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
            
            expires_at = datetime.now() + timedelta(seconds=expiry_seconds)
            
            logger.info(f"Generated presigned upload URL for {filename}")
            
            return {
                'upload_url': presigned_url,
                'image_url': image_url,
                'upload_id': upload_id,
                'key': key,
                'expires_at': expires_at
            }
            
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            raise Exception(f"Failed to generate presigned URL: {str(e)}")
    
    async def generate_presigned_download_url(
        self,
        key: str,
        expiry_seconds: int = None
    ) -> str:
        """Generate presigned URL for downloading/viewing image"""
        try:
            if expiry_seconds is None:
                expiry_seconds = settings.S3_PRESIGNED_URL_EXPIRY
            
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key,
                },
                ExpiresIn=expiry_seconds
            )
            
            logger.info(f"Generated presigned download URL for {key}")
            return presigned_url
            
        except ClientError as e:
            logger.error(f"Error generating presigned download URL: {str(e)}")
            raise Exception(f"Failed to generate presigned download URL: {str(e)}")
    
    async def upload_image_direct(
        self,
        image_data: bytes,
        filename: str,
        content_type: str
    ) -> Dict[str, Any]:
        """Upload image directly to S3"""
        try:
            # Generate unique key
            upload_id = str(uuid.uuid4())
            file_extension = filename.split('.')[-1] if '.' in filename else 'jpg'
            key = f"uploads/{upload_id}.{file_extension}"
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=image_data,
                ContentType=content_type,
                Metadata={
                    'original_filename': filename,
                    'upload_timestamp': datetime.now().isoformat()
                }
            )
            
            # Generate access URL
            image_url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
            
            logger.info(f"Uploaded image {filename} to S3 as {key}")
            
            return {
                'image_url': image_url,
                'upload_id': upload_id,
                'key': key,
                'bucket': self.bucket_name
            }
            
        except ClientError as e:
            logger.error(f"Error uploading image to S3: {str(e)}")
            raise Exception(f"Failed to upload image to S3: {str(e)}")
    
    async def delete_image(self, key: str) -> bool:
        """Delete image from S3"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            logger.info(f"Deleted image {key} from S3")
            return True
            
        except ClientError as e:
            logger.error(f"Error deleting image from S3: {str(e)}")
            return False
    
    async def check_image_exists(self, key: str) -> bool:
        """Check if image exists in S3"""
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                logger.error(f"Error checking image existence: {str(e)}")
                raise Exception(f"Failed to check image existence: {str(e)}")
    
    async def get_image_metadata(self, key: str) -> Dict[str, Any]:
        """Get image metadata from S3"""
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            return {
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength'),
                'last_modified': response.get('LastModified'),
                'metadata': response.get('Metadata', {}),
                'etag': response.get('ETag')
            }
            
        except ClientError as e:
            logger.error(f"Error getting image metadata: {str(e)}")
            raise Exception(f"Failed to get image metadata: {str(e)}")
    
    async def create_bucket_if_not_exists(self) -> bool:
        """Create S3 bucket if it doesn't exist"""
        try:
            # Check if bucket exists
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket {self.bucket_name} already exists")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                # Bucket doesn't exist, create it
                try:
                    if settings.AWS_REGION == 'us-east-1':
                        # us-east-1 doesn't need LocationConstraint
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': settings.AWS_REGION}
                        )
                    
                    # Enable CORS for web access
                    cors_config = {
                        'CORSRules': [
                            {
                                'AllowedHeaders': ['*'],
                                'AllowedMethods': ['GET', 'PUT', 'POST'],
                                'AllowedOrigins': ['*'],
                                'ExposeHeaders': ['ETag'],
                                'MaxAgeSeconds': 3000
                            }
                        ]
                    }
                    
                    self.s3_client.put_bucket_cors(
                        Bucket=self.bucket_name,
                        CORSConfiguration=cors_config
                    )
                    
                    logger.info(f"Created bucket {self.bucket_name} with CORS configuration")
                    return True
                    
                except ClientError as create_error:
                    logger.error(f"Error creating bucket: {str(create_error)}")
                    return False
            else:
                logger.error(f"Error checking bucket: {str(e)}")
                return False

# Global service instance
s3_service = S3Service() 