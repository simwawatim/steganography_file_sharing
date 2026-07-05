
from core.Serializers.File.SharedFileSerializer import ShareFileWithSecretSerializer, SharedFileDetailsSerializer, SharedFileSerializer
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.parsers import MultiPartParser, FormParser
from core.services.services import share_file_with_secret
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from core.Utils.Utils import Utils
from core.models import SharedFile
from rest_framework import status





UTILS_INSTANCE = Utils()


@extend_schema(
    tags=["File Sharing"],
    request=ShareFileWithSecretSerializer,
    responses={201: SharedFileSerializer},
)
class ShareFileWithSecretView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = ShareFileWithSecretSerializer(data=request.data, context={"request": request})

        if not serializer.is_valid():
            return Response(
                {
                    "status": "fail",
                    "message": UTILS_INSTANCE.formatSerializerErrors(serializer.errors),
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        try:
            shared_file = share_file_with_secret(
                sender=request.user,
                recipient_username=data["recipient_username"],
                file_obj=data["file"],
                message=data["message"],
                carrier_image_file=data["carrier_image"],
                can_download=data.get("can_download", True),
            )
        except ValueError as e:
            return Response(
                {"status": "fail", "message": str(e), "data": None},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "status": "success",
                "message": "File shared with encrypted secret message successfully",
                "data": SharedFileSerializer(shared_file).data,
            },
            status=status.HTTP_201_CREATED,
        )
    



@extend_schema(
    tags=["File Sharing"],
    responses={200: SharedFileSerializer(many=True)},
)
class ReceivedSharedFilesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        shared_files = SharedFile.objects.filter(
            shared_with=request.user
        ).order_by("-id")

        serializer = SharedFileSerializer(shared_files, many=True)

        return Response(
            {
                "status": "success",
                "message": "Received shared files fetched successfully",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
    



@extend_schema(
    tags=["File Sharing"],
    responses={200: SharedFileDetailsSerializer},
)
class SharedFileDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, file_id):
        try:
            shared_file = SharedFile.objects.get(
                id=file_id,
                shared_with=request.user
            )
        except SharedFile.DoesNotExist:
            return Response(
                {
                    "status": "fail",
                    "message": "Shared file not found",
                    "data": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "status": "success",
                "message": "Shared file fetched successfully",
                "data": SharedFileDetailsSerializer(shared_file).data,
            },
            status=status.HTTP_200_OK,
        )