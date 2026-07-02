from core.Serializers.Users.UsersSerializer import ProfilePictureSerializer, ProfileUpdateSerializer, SignupSerializer, LoginSerializer, UserProfileSerializer
from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.views import APIView
from core.models import UserProfile
from core.Utils.Utils import Utils
from rest_framework import status



UTILS_INSTANCE = Utils()


@extend_schema(
    tags=["Auth"],
    request=SignupSerializer,
    responses={201: UserProfileSerializer},
    examples=[
        OpenApiExample(
            "Signup Example",
            value={
                "username": "john",
                "email": "john@email.com",
                "password": "12345678"
            },
            request_only=True,
        )
    ],
)
class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)

            return Response({
                "status": "success",
                "message": "Account created successfully",
                "data": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user": UserProfileSerializer(
                        user,
                        context={"request": request},
                    ).data,
                },
            }, status=status.HTTP_201_CREATED)

        return Response({
            "status": "fail",
            "message": UTILS_INSTANCE.formatSerializerErrors(serializer.errors),
            "data": None,
        }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Auth"],
    request=LoginSerializer,
    responses={200: UserProfileSerializer},
    examples=[
        OpenApiExample(
            "Login Example",
            value={
                "username": "john",
                "password": "12345678"
            },
            request_only=True,
        )
    ],
)
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data["user"]
            refresh = RefreshToken.for_user(user)

            return Response({
                "status": "success",
                "message": "Login successful",
                "data": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user": UserProfileSerializer(
                        user,
                        context={"request": request},
                    ).data,
                },
            }, status=status.HTTP_200_OK)

        return Response({
            "status": "fail",
            "message": UTILS_INSTANCE.formatSerializerErrors(serializer.errors),
            "data": None,
        }, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    tags=["Profile"],
    responses={200: UserProfileSerializer},
)
class ProfileDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(
            request.user,
            context={"request": request}
        )

        return Response({
            "status": "success",
            "message": "Profile retrieved successfully",
            "data": serializer.data,
        }, status=status.HTTP_200_OK)

@extend_schema(
    tags=["Profile"],
    request=ProfileUpdateSerializer,
    responses={200: UserProfileSerializer},
    examples=[
        OpenApiExample(
            "Update Profile Example",
            value={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@email.com"
            },
            request_only=True,
        )
    ],
)
class ProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = ProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()

            return Response({
                "status": "success",
                "message": "Profile updated successfully",
                "data": UserProfileSerializer(
                    request.user,
                    context={"request": request}
                ).data,
            }, status=status.HTTP_200_OK)

        return Response({
            "status": "fail",
            "message": serializer.errors,
            "data": None,
        }, status=status.HTTP_400_BAD_REQUEST)



@extend_schema(
    tags=["Profile"],
    request=ProfilePictureSerializer,
    responses={200: UserProfileSerializer},
    description="Upload or update profile picture.",
)
class ProfilePictureUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)

        serializer = ProfilePictureSerializer(
            profile,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                {
                    "status": "success",
                    "message": "Profile picture updated successfully",
                    "data": UserProfileSerializer(
                        request.user,
                        context={"request": request},
                    ).data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "status": "fail",
                "message": serializer.errors,
                "data": None,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )