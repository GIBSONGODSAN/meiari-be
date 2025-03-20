from rest_framework import serializers
from .models import ( MeiAriUser, MeiAriUserBioData, )
from .methods import encrypt_password

class FolderSerializer(serializers.Serializer):
    folder_name = serializers.CharField(max_length=255)
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeiAriUser
        fields = '__all__'
    
class MeiAriUserBioDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeiAriUserBioData
        fields = ['first_name', 'last_name', 'date_of_birth', 'home_address', 'phone_number']

class SignUpSerializer(serializers.ModelSerializer):
    bio_data = MeiAriUserBioDataSerializer(write_only=True)  # Nested bio-data

    class Meta:
        model = MeiAriUser
        fields = ['email', 'password', 'bio_data']

    def create(self, validated_data):
        bio_data = validated_data.pop('bio_data', None)
        
        # Create the user and hash the password
        user = MeiAriUser.objects.create(**validated_data)
        raw_password = validated_data['password']
        user.password = encrypt_password(raw_password)
        user.save()

        # Create user bio-data if provided
        if bio_data:
            MeiAriUserBioData.objects.create(user=user, **bio_data)

        return user
    
class OTPVerifySerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    otp = serializers.CharField(max_length=4)
    
class SignInSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        # Check if user exists
        try:
            user = MeiAriUser.objects.get(email=email)
        except MeiAriUser.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password")

        # Validate password
        if not check_password(password, user.password):
            raise serializers.ValidationError("Invalid email or password")

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        # Fetch user's biodata
        try:
            bio_data = MeiAriUserBioData.objects.get(user=user)
            first_name = bio_data.first_name
            last_name = bio_data.last_name
            phone_number = bio_data.phone_number
        except MeiAriUserBioData.DoesNotExist:
            first_name, last_name, phone_number = None, None, None

        return {
            "user_id": str(user.id),
            "email": user.email,
            "first_name": first_name,
            "last_name": last_name,
            "phone_number": phone_number,
        }