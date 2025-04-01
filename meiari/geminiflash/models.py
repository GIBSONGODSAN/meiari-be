from django.db import models
import uuid

# Custom User Model
class MeiAriUser(models.Model):
    cug_phone_number = models.CharField(max_length=20)
    cug_email_address = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    access_list = models.TextField()
    role = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

class MeiAriUserBioData(models.Model):
    user = models.ForeignKey(MeiAriUser, on_delete=models.CASCADE)
    user_name = models.CharField(max_length=255)
    active = models.BooleanField(default=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    alternative_email_address = models.EmailField()
    access_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def generate_access_id(self):
        """Generate an access_id using first 5 characters of first name + DOB (DDMM)."""
        name_part = (self.first_name[:5]).ljust(5, "X")  # Ensure at least 5 characters
        dob_part = self.date_of_birth.strftime("%d%m")  # Extract DDMM from DOB
        return f"{name_part}{dob_part}"

    def save(self, *args, **kwargs):
        """Automatically set access_id before saving the instance."""
        if not self.access_id:  # Generate only if not already set
            self.access_id = self.generate_access_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.access_id}"
    
class OTPTable(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('MeiAriUser', on_delete=models.CASCADE)
    otp = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"OTP {self.otp} for {self.user.email}"
    
from django.db import models

class TNGovtDept(models.Model):
    department_name = models.CharField(max_length=255)
    level = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

class TNGovtDeptContact(models.Model):
    department = models.ForeignKey(TNGovtDept, on_delete=models.CASCADE)
    cug_minister_email = models.EmailField()
    cug_minister_phone_number = models.CharField(max_length=20)
    minister_name = models.CharField(max_length=255)
    stg_email = models.EmailField()
    stg_phone_number = models.CharField(max_length=20)
    stg_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

class TNGovtSubDept(models.Model):
    department = models.ForeignKey(TNGovtDept, on_delete=models.CASCADE)
    sub_department_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

class SubDeptDetails(models.Model):
    sub_dept = models.ForeignKey(TNGovtSubDept, on_delete=models.CASCADE)
    sub_dept_office = models.CharField(max_length=255)
    sub_dept_hod = models.CharField(max_length=255)
    sub_dept_cug_email = models.EmailField()
    sub_dept_cug_phone_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

class SubDeptOfficeDetails(models.Model):
    sub_dept = models.ForeignKey(TNGovtSubDept, on_delete=models.CASCADE)
    sub_dept_office_location = models.CharField(max_length=255)
    sub_dept_street_address = models.TextField()
    sub_dept_district = models.CharField(max_length=255)
    sub_dept_taluk = models.CharField(max_length=255)
    sub_dept_access_code = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

class WorkGroup(models.Model):
    sub_dept_office = models.ForeignKey(SubDeptOfficeDetails, on_delete=models.CASCADE)
    group_id = models.CharField(max_length=100, unique=True)
    group_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

class WorkGroupDetails(models.Model):
    work_group = models.ForeignKey(WorkGroup, on_delete=models.CASCADE)
    group_description = models.TextField()
    group_photo = models.ImageField(upload_to='group_photos/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

class WorkGroupMember(models.Model):
    work_group = models.ForeignKey(WorkGroup, on_delete=models.CASCADE)
    user_id = models.IntegerField()
    role_name = models.CharField(max_length=100)
    joined_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

class WorkGroupTicket(models.Model):
    work_group = models.ForeignKey(WorkGroup, on_delete=models.CASCADE)
    ticket_code = models.CharField(max_length=100, unique=True)
    ticket_title = models.CharField(max_length=255)
    ticker_description = models.TextField()
    ticket_status = models.CharField(max_length=50)
    priority = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

class WorkGroupMessage(models.Model):
    ticket = models.ForeignKey(WorkGroupTicket, on_delete=models.CASCADE)
    sender_id = models.IntegerField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class WorkGroupAttachment(models.Model):
    message = models.ForeignKey(WorkGroupMessage, on_delete=models.CASCADE)
    file_id = models.IntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

class WorkGroupS3Details(models.Model):
    file_name = models.CharField(max_length=255)
    s3_file_url = models.URLField()
    sent_by = models.IntegerField()

class WorkTaskPerson(models.Model):
    task_id = models.IntegerField()
    assigned_to = models.IntegerField()
    assigned_by = models.IntegerField()
    assigned_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)

class WorkTaskDetails(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    group_id = models.IntegerField()
    created_by = models.IntegerField()
    status = models.CharField(max_length=50)
    due_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

class WorkTaskReport(models.Model):
    report_id = models.CharField(max_length=100, unique=True)
    report_content = models.TextField()
    assigned_to = models.IntegerField()
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

class WorkTestVerification(models.Model):
    report = models.ForeignKey(WorkTaskReport, on_delete=models.CASCADE)
    verified_by = models.IntegerField()
    verification_status = models.CharField(max_length=50)
    verification_date = models.DateTimeField()
    comments = models.TextField()

class WorkTaskSignature(models.Model):
    report = models.ForeignKey(WorkTaskReport, on_delete=models.CASCADE)
    collector_id = models.IntegerField()
    signed_at_date = models.DateTimeField()
    status = models.CharField(max_length=50)
    official_name = models.CharField(max_length=255)


