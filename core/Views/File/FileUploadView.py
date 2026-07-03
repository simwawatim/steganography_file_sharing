from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from core.Serializers.File.UserFileSerializer import UserFileSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.paginator import Paginator
from rest_framework.views import APIView
from rest_framework import status

from core.models import UserFile, UserFolder
from core.Utils.Utils import Utils

UTILS_INSTANCE = Utils()


@extend_schema(
    tags=["Files"],
    request=UserFileSerializer,
    responses={201: UserFileSerializer},
    examples=[
        OpenApiExample(
            "Upload File",
            value={
                "file": "example.png",
                "folder": 1
            },
            request_only=True,
        )
    ],
)
class UserFileUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = UserFileSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user)

            return Response(
                {
                    "status": "success",
                    "message": "File uploaded successfully",
                    "data": serializer.data,
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


@extend_schema(
    tags=["Files"],
    responses={200: UserFileSerializer(many=True)},
)
class UserFileListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        files = UserFile.objects.filter(user=request.user).order_by("-uploaded_at")
        serializer = UserFileSerializer(files, many=True)

        return Response(
            {
                "status": "success",
                "message": "Files retrieved successfully",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(
    tags=["Files"],
    responses={200: UserFileSerializer},
)
class UserFileDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return UserFile.objects.get(pk=pk, user=request.user)
        except UserFile.DoesNotExist:
            return None

    def get(self, request, pk):
        file_obj = self.get_object(request, pk)

        if not file_obj:
            return Response(
                {
                    "status": "fail",
                    "message": "File not found",
                    "data": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = UserFileSerializer(file_obj)

        return Response(
            {
                "status": "success",
                "message": "File retrieved successfully",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(
    tags=["Files"],
    request=UserFileSerializer,
    responses={200: UserFileSerializer},
)
class UserFileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return UserFile.objects.get(pk=pk, user=request.user)
        except UserFile.DoesNotExist:
            return None

    def patch(self, request, pk):
        file_obj = self.get_object(request, pk)

        if not file_obj:
            return Response(
                {
                    "status": "fail",
                    "message": "File not found",
                    "data": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = UserFileSerializer(
            file_obj,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                {
                    "status": "success",
                    "message": "File updated successfully",
                    "data": serializer.data,
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


@extend_schema(
    tags=["Files"],
    responses={200: None},
)
class UserFileDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return UserFile.objects.get(pk=pk, user=request.user)
        except UserFile.DoesNotExist:
            return None

    def delete(self, request, pk):
        file_obj = self.get_object(request, pk)

        if not file_obj:
            return Response(
                {
                    "status": "fail",
                    "message": "File not found",
                    "data": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        file_obj.delete()

        return Response(
            {
                "status": "success",
                "message": "File deleted successfully",
                "data": None,
            },
            status=status.HTTP_200_OK,
        )
    


@extend_schema(
    tags=["Files"],
    responses={200: UserFileSerializer},
)
class UserFileDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return UserFile.objects.get(pk=pk, user=request.user)
        except UserFile.DoesNotExist:
            return None

    def get(self, request, pk):
        file_obj = self.get_object(request, pk)

        if not file_obj:
            return Response(
                {
                    "status": "fail",
                    "message": "File not found",
                    "data": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = UserFileSerializer(file_obj)

        return Response(
            {
                "status": "success",
                "message": "File retrieved successfully",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
    

@extend_schema(
    tags=["Files"],
    parameters=[
        OpenApiParameter(name="page", type=int, description="Page number"),
        OpenApiParameter(name="limit", type=int, description="Items per page"),
    ],
)
class FolderFilesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, folder_id):
        try:
            folder = UserFolder.objects.get(id=folder_id, user=request.user)
        except UserFolder.DoesNotExist:
            return Response(
                {
                    "status": "fail",
                    "message": "Folder not found",
                    "data": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        files_qs = UserFile.objects.filter(
            folder=folder,
            user=request.user
        ).order_by("-uploaded_at")


        total_files = files_qs.count()

        total_size = sum(
            f.file.size for f in files_qs if f.file
        )

        page = int(request.GET.get("page", 1))
        limit = int(request.GET.get("limit", 10))

        paginator = Paginator(files_qs, limit)
        page_obj = paginator.get_page(page)

        serializer = UserFileSerializer(page_obj.object_list, many=True)

        return Response(
            {
                "status": "success",
                "message": "Folder files retrieved successfully",
                "data": {
                    "folder": {
                        "id": folder.id,
                        "name": folder.folder_name,
                    },
                    "stats": {
                        "total_files": total_files,
                        "total_size_bytes": total_size,
                        "total_size_mb": round(total_size / (1024 * 1024), 2),
                    },
                    "pagination": {
                        "page": page,
                        "limit": limit,
                        "total_pages": paginator.num_pages,
                        "has_next": page_obj.has_next(),
                        "has_previous": page_obj.has_previous(),
                    },
                    "files": serializer.data,
                },
            },
            status=status.HTTP_200_OK,
        )

