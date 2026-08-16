from core.Serializers.File.SharedFileSerializer import ShareFileWithSecretSerializer, SharedFileDetailsSerializer, SharedFileSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from core.services.services import share_file_with_secret
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView
from core.Utils.Utils import Utils
from core.models import SharedFile
from rest_framework import status

from core.Utils.Logs.Decorators import log_activity


UTILS_INSTANCE = Utils()


@extend_schema(
    tags=["File Sharing"],
    request=ShareFileWithSecretSerializer,
    responses={201: SharedFileSerializer},
)
class ShareFileWithSecretView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @log_activity(
        "file.share",
        description=lambda req, res: f"Shared file with {req.data.get('recipient_username')}",
    )
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
            shared_file, passphrase = share_file_with_secret(
                sender=request.user,
                recipient_username=data["recipient_username"],
                file_obj=data["file"],
                message=data["message"],
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
                "data": {
                    **SharedFileSerializer(shared_file).data,
                    "passphrase": passphrase,
                },
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["File Sharing"],
    responses={200: SharedFileSerializer(many=True)},
)
class ReceivedSharedFilesView(APIView):
    permission_classes = [IsAuthenticated]

    @log_activity("file.share.list_received", description="Listed received shared files")
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

    @log_activity(
        "file.share.view",
        description=lambda req, res: f"Viewed shared file {req.parser_context['kwargs'].get('file_id')}",
    )
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

        passphrase = "12345"

        serializer = SharedFileDetailsSerializer(
            shared_file,
            context={"request": request, "passphrase": passphrase},
        )

        return Response(
            {
                "status": "success",
                "message": "Shared file fetched successfully",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )