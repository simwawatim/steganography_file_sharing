
from core.Serializers.Users.UsersSerializer import ProfilePictureSerializer, ProfileUpdateSerializer, SignupSerializer, LoginSerializer, UserProfileSerializer
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.exceptions import TokenError
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



UTILS_INSTANCE = Utils()

from django.contrib.auth import get_user_model

User = get_user_model()

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



@extend_schema(
    tags=["Profile"],
    responses={200: ProfilePictureSerializer},
    description="Retrieve the logged-in user's profile picture.",
)
class ProfilePictureDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)

        serializer = ProfilePictureSerializer(
            profile,
            context={"request": request},
        )

        return Response({
            "status": "success",
            "message": "Profile picture retrieved successfully",
            "data": serializer.data,
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Auth"],
    request=TokenRefreshSerializer,
    responses={200: TokenRefreshSerializer},
    examples=[
        OpenApiExample(
            "Refresh Token Example",
            value={"refresh": "<refresh_token>"},
            request_only=True,
        )
    ],
)
class RefreshTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)

        if serializer.is_valid():
            return Response({
                "status": "success",
                "message": "Token refreshed successfully",
                "data": serializer.validated_data,
            }, status=status.HTTP_200_OK)

        return Response({
            "status": "fail",
            "message": UTILS_INSTANCE.formatSerializerErrors(serializer.errors),
            "data": None,
        }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Auth"],
    request=OpenApiExample(
        "Logout Example",
        value={"refresh": "<refresh_token>"},
        request_only=True,
    ),
    responses={200: None},
    description="Blacklist the refresh token to log the user out.",
)
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response({
                "status": "fail",
                "message": "Refresh token is required",
                "data": None,
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({
                "status": "fail",
                "message": "Invalid or expired token",
                "data": None,
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "status": "success",
            "message": "Logout successful",
            "data": None,
        }, status=status.HTTP_200_OK)


class UserListPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


@extend_schema(
    tags=["Users"],
    responses={200: UserProfileSerializer(many=True)},
    description="Retrieve a paginated list of all users in the system.",
)
class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = User.objects.select_related("userprofile").order_by("id")

        paginator = UserListPagination()
        page = paginator.paginate_queryset(users, request)

        serializer = UserProfileSerializer(
            page,
            many=True,
            context={"request": request},
        )

        return Response({
            "status": "success",
            "message": "Users retrieved successfully",
            "data": {
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": serializer.data,
            },
        }, status=status.HTTP_200_OK)