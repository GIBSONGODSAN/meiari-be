import json
from django.shortcuts import render
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .geminiservice import get_gemini_response, sample_gemini_response
from .methods import encrypt_password, generate_otp, generate_filename, EmailService
import boto3
from django.conf import settings
from rest_framework.parsers import JSONParser
from .serializers import FolderSerializer  
from django.http import JsonResponse
from .models import MeiAriUser, MeiAriUserBioData, OTPTable
from .serializers import UserSerializer, SignUpSerializer, OTPVerifySerializer
import logging
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404

# Create your views here.
class GeminFlashCheckAPI(APIView):
    def get(self, request):
        return Response({"data": {"message":"GeminFlash API is working fine"}}, status=status.HTTP_200_OK)
    
class SignInAPIView(APIView):
    def post(self, request):
        try:
            print(request.data)
            data = request.data
            email = data.get("email")
            password = data.get("password")
            logger.info(f"Request: {request.method} {request.get_full_path()}")
            user = User.objects.get(email=email)
            logger.info(user)
            encryptPassword = encrypt_password(password) 
            print(user.role)
            if user.subscription:
                if user.role == 'visitor':
                    user.role = 'purchasedUser'
                    user.save()
            if user.password == encryptPassword:
                if user.role == "purchasedUser":
                    token = purchasedUser_encode_token({"id": str(user.id), "role": user.role})
                elif user.role == "CourseSubscribedUser":
                    token = courseSubscribedUser_encode_token({"id": str(user.id), "role": user.role})
                elif user.role == "admin":
                    token = admin_encode_token({"id": str(user.id), "role": user.role})
                elif user.role == "visitor":
                    token = visitor_encode_token({"id": str(user.id), "role": user.role})
                else:
                    return Response(
                        {"message": "Invalid role"}, status=status.HTTP_400_BAD_REQUEST
                    )
                
                refresh = RefreshToken.for_user(user)
                return Response(
                    {
                        "token": str(token),
                        "access": str(refresh.access_token),
                        "data": {"user_id":user.id,'username':user.username, "subscription":user.subscription, "role": user.role},  
                        "message": "User logged in successfully",
                    },
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )
        except User.DoesNotExist:
            logger.info("User not found")
            logger.error("User not found")
            return Response(
                {"message": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(e)
            return Response({"message": str(e)}, status=status.HTTP_502_BAD_GATEWAY)
    
class SignUpAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = SignUpSerializer(data=request.data)
        
        if serializer.is_valid():
            # Encrypt the password
            raw_password = serializer.validated_data['password']
            encrypted_password = encrypt_password(raw_password)
            serializer.validated_data['password'] = encrypted_password
            
            # Save the user
            user = serializer.save()
            
            email_service = EmailService()
            email_service.send_otp_email(user)
            
            return Response({'data': { 'user_id': user.id } , 'message': "User created successfully. OTP sent to email."}, status=status.HTTP_201_CREATED)
        print("Validation Errors:", serializer.errors)  # Debugging
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
class OTPVerifyAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = OTPVerifySerializer(data=request.data)

        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            otp = serializer.validated_data['otp']

            # Get the OTP record for the user
            otp_record = get_object_or_404(OTPTable, user_id=user_id, otp=otp)

            # If OTP is correct, delete the record and return success
            otp_record.delete()
            return Response({'message': 'OTP verified successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
    
class GeminiServiceCheckAPI(APIView):
    def get(self, request):
        response_from_gemini = get_gemini_response("Hello")
        return Response({"data": {"gemini_response": response_from_gemini}}, status=status.HTTP_200_OK)
    
class ReceiveFormDataAPIView(APIView):
    def post(self, request, *args, **kwargs):
        from_user = request.POST.get("from")
        to_user = request.POST.get("to")
        content_body_1 = request.POST.get("content_body_1")
        content_body_2 = request.POST.get("content_body_2")

        if not (from_user and to_user and content_body_1 and content_body_2):
            return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

        response = sample_gemini_response(from_user, to_user, content_body_1, content_body_2)
        
        return Response({"data": {"gemini_response": response}}, status=status.HTTP_200_OK)


class CreateS3FolderView(APIView):
    def post(self, request):
        serializer = FolderSerializer(data=request.data)
        if serializer.is_valid():
            folder_name = serializer.validated_data["folder_name"]

            # Ensure folder name ends with '/'
            if not folder_name.endswith("/"):
                folder_name += "/"

            try:
                s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_S3_REGION_NAME
                )

                # Create an empty object with the folder name (S3 doesn't have actual directories)
                s3_client.put_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=folder_name)

                return Response(
                    {"message": f"Folder '{folder_name}' created successfully in S3"},
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ListS3FoldersView(APIView):
    def get(self, request):
        try:
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )

            # List all objects in the bucket
            response = s3_client.list_objects_v2(Bucket=settings.AWS_STORAGE_BUCKET_NAME)

            # Extract folders manually by checking for prefixes
            folders = set()
            if "Contents" in response:
                for obj in response["Contents"]:
                    key = obj["Key"]
                    if "/" in key:  # Only consider keys that represent directories
                        folder = key.split("/")[0] + "/"
                        folders.add(folder)

            return Response(
                {"data": 
                    { "folders": list(folders)}},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
class ListS3FilesView(APIView):
    def get(self, request, folder_name):
        try:
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )

            # Ensure folder name ends with '/'
            if not folder_name.endswith("/"):
                folder_name += "/"

            # List objects inside the specified folder (prefix)
            response = s3_client.list_objects_v2(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Prefix=folder_name
            )

            # Extract file names (skip folders)
            files = [
                obj["Key"] for obj in response.get("Contents", [])
                if not obj["Key"].endswith("/")
            ]

            return Response(
                { "data" : {"files": files}},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            

class CreateS3TextFileView(APIView):
    parser_classes = [JSONParser]  # Ensure JSON parsing for request body

    def post(self, request):
        try:
            # Get folder name, file name, and content from request body
            folder_name = request.data.get("folder_name")
            file_name = request.data.get("file_name")
            file_content = request.data.get("file_content", "")

            if not folder_name or not file_name:
                return Response(
                    {"error": "folder_name and file_name are required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Ensure folder name ends with '/'
            if not folder_name.endswith("/"):
                folder_name += "/"

            # Construct full file path (folder + file name)
            file_path = f"{folder_name}{file_name}.txt"

            # Initialize S3 client
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )

            # Upload file to S3
            s3_client.put_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=file_path,
                Body=file_content,
                ContentType="text/plain"
            )

            return Response(
                {"message": f"File '{file_name}.txt' created successfully in folder '{folder_name}'"},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class GeminiReportResponse(APIView):
    parser_classes = [JSONParser] 
    def post(self, request):
        try:
            json_data = request.data
            
            # Debug: Log incoming request
            print("Received JSON:", json.dumps(json_data, indent=2))

            if not json_data:
                return Response({"error": "Empty JSON payload"}, status=status.HTTP_400_BAD_REQUEST)

            prompt = f"Create a Detailed report using the content: {json.dumps(json_data)}"
            summary_report = get_gemini_response(prompt)

            return Response({"data":{"summary_report": summary_report}}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 


class GenerateAndUploadReport(APIView):
    parser_classes = [JSONParser]

    def post(self, request):
        try:
            # Step 1: Call GeminiReportResponse API
            gemini_url = "http://127.0.0.1:8000/app/gemini-report-response/"
            gemini_payload = request.data  # Assuming input is given in request

            gemini_response = requests.post(gemini_url, json=gemini_payload)
            
            if gemini_response.status_code != 200:
                return Response(
                    {"error": "Failed to generate report", "details": gemini_response.json()},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Extract summary report text
            summary_report_text = gemini_response.json().get("data", {}).get("summary_report", "")

            if not summary_report_text:
                return Response(
                    {"error": "Generated report is empty."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Step 2: Upload report to S3
            folder_name = "samplefolder"
            file_name = generate_filename("generated_report")
            file_path = f"{folder_name}/{file_name}.txt"

            # Initialize S3 client
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )

            # Upload file to S3
            s3_client.put_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=file_path,
                Body=summary_report_text,
                ContentType="text/plain"
            )

            return Response(
                {"message": f"Report successfully generated and uploaded to S3 at {file_path}"},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )