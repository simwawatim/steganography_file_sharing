from core.Serializers.Users.UsersSerializer import SignupSerializer, LoginSerializer, UserProfileSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from core.Utils.Utils import Utils

UTILS_INSTANCE = Utils()


class SignupView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=SignupSerializer,
        responses={201: dict},
    )
    def post(self, request):
        serializer = SignupSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)

            return Response(
                {
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
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "status": "fail",
                "message": UTILS_INSTANCE.formatSerializerErrors(serializer.errors),
                "data": None,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginSerializer,
        responses={200: dict},
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data["user"]
            refresh = RefreshToken.for_user(user)

            return Response(
                {
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
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "status": "fail",
                "message": UTILS_INSTANCE.formatSerializerErrors(serializer.errors),
                "data": None,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: dict})
    def get(self, request):
        serializer = UserProfileSerializer(
            request.user,
            context={"request": request},
        )

        return Response(
            {
                "status": "success",
                "message": "Profile retrieved successfully",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )