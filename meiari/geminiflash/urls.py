from django.urls import path
from .views import ( GeminFlashCheckAPI, GeminiServiceCheckAPI, ReceiveFormDataAPIView, CreateS3FolderView, ListS3FoldersView,
                     ListS3FilesView, CreateS3TextFileView, GeminiReportResponse, GenerateAndUploadReport, SignUpAPIView, OTPVerifyAPIView ) 

urlpatterns = [
    path('check/', GeminFlashCheckAPI.as_view(), name = 'geminiapp-check'),

    path('gemini/', GeminiServiceCheckAPI.as_view(), name = 'geminiflash-check'),
    path('form-response/', ReceiveFormDataAPIView.as_view(), name = 'send-data'),
    path('gemini-report-response/', GeminiReportResponse.as_view(), name = 'gemini-report-response'),
    path('generate-and-upload-report/', GenerateAndUploadReport.as_view(), name = 'generate-and-upload-report'),

    path("create-folder/", CreateS3FolderView.as_view(), name="create-s3-folder"),
    path("list-folders/", ListS3FoldersView.as_view(), name="list-s3-folders"),
    path("list-files/<str:folder_name>/", ListS3FilesView.as_view(), name="list-s3-files"),
    path("create-txt-file/", CreateS3TextFileView.as_view(), name="create-s3-txt-file"),
    
    path("signup/", SignUpAPIView.as_view(), name="signup"),
    path("verify-otp/", OTPVerifyAPIView.as_view(), name="verify_otp"),

]