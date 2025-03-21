from django.db import models
import uuid

# Custom User Model
class MeiAriUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

class MeiAriUserBioData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey("MeiAriUser", on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    home_address = models.TextField()
    phone_number = models.CharField(max_length=15)
    access_id = models.CharField(max_length=15, unique=True, blank=True)
    feature_id_list = models.JSONField(default=list)  # Store multiple access IDs as a list
    encoded_auth = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
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