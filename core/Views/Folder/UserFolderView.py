from core.Serializers.Folder.UserFolderSerializer import UserFolderSerializer
from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from core.models import UserFolder
from core.Utils.Utils import Utils

UTILS_INSTANCE = Utils()


@extend_schema(
    tags=["Folders"],
    responses={200: UserFolderSerializer(many=True)},
)
class UserFolderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        folders = UserFolder.objects.filter(
            user=request.user
        ).order_by("-created_at")

        serializer = UserFolderSerializer(folders, many=True)

        return Response(
            {
                "status": "success",
                "message": "Folders retrieved successfully",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(
    tags=["Folders"],
    request=UserFolderSerializer,
    responses={201: UserFolderSerializer},
    examples=[
        OpenApiExample(
            "Create Folder",
            value={
                "folder_name": "My Secret Files"
            },
            request_only=True,
        )
    ],
)
class UserFolderCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UserFolderSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user)

            return Response(
                {
                    "status": "success",
                    "message": "Folder created successfully",
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
    tags=["Folders"],
    responses={200: UserFolderSerializer},
)
class UserFolderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return UserFolder.objects.get(pk=pk, user=request.user)
        except UserFolder.DoesNotExist:
            return None

    def get(self, request, pk):
        folder = self.get_object(request, pk)

        if not folder:
            return Response(
                {
                    "status": "fail",
                    "message": "Folder not found",
                    "data": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = UserFolderSerializer(folder)

        return Response(
            {
                "status": "success",
                "message": "Folder retrieved successfully",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        request=UserFolderSerializer,
        responses={200: UserFolderSerializer},
    )
    def patch(self, request, pk):
        folder = self.get_object(request, pk)

        if not folder:
            return Response(
                {
                    "status": "fail",
                    "message": "Folder not found",
                    "data": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = UserFolderSerializer(
            folder,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                {
                    "status": "success",
                    "message": "Folder updated successfully",
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

    def delete(self, request, pk):
        folder = self.get_object(request, pk)

        if not folder:
            return Response(
                {
                    "status": "fail",
                    "message": "Folder not found",
                    "data": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        folder.delete()

        return Response(
            {
                "status": "success",
                "message": "Folder deleted successfully",
                "data": None,
            },
            status=status.HTTP_200_OK,
        )