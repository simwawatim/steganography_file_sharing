from core.Views.Admin.Dashboard.api import AdminDashboardStatsView
from core.Views.Admin.Files.api import FilesListView
from core.Views.Admin.Logs.LogView import ActivityLogDetailView, ActivityLogListView
from core.Views.Admin.Users.api import UsersListView
from core.Views.Dashboard.Stats import DashboardStatsView
from core.Views.File.FileUploadView import FolderFilesView, UserFileDeleteView, UserFileDetailView, UserFileListView, UserFileUpdateView, UserFileUploadView
from core.Views.File.SharedFileViews import ReceivedSharedFilesView, SentSharedFileDetailView, SentSharedFilesView, ShareFileWithSecretView, SharedFileDetailView
from core.Views.Users.UsersView import LogoutView, ProfileDetailView, ProfilePictureDetailView, ProfilePictureUpdateView, ProfileUpdateView, RefreshTokenView, SignupView, LoginView, UserListView
from core.Views.Folder.UserFolderView import UserFolderCreateView, UserFolderDetailView, UserFolderListView
from django.urls import path

urlpatterns = [
    path("signup/", SignupView.as_view()),
    path("login/", LoginView.as_view()),
    path("users/", UserListView.as_view()),
    path("profile/", ProfileDetailView.as_view()),
    path("profile/update/", ProfileUpdateView.as_view()),
    path("profile/picture/", ProfilePictureUpdateView.as_view()),
    path("folders/", UserFolderListView.as_view()),
    path("folders/create/", UserFolderCreateView.as_view()),
    path("folders/<int:pk>/", UserFolderDetailView.as_view()),
    path("files/upload/", UserFileUploadView.as_view()),
    path("files/", UserFileListView.as_view()),
    path("files/<int:pk>/", UserFileDetailView.as_view()),
    path("files/<int:pk>/update/", UserFileUpdateView.as_view()),
    path("files/<int:pk>/delete/", UserFileDeleteView.as_view()),
    path("folders/<int:folder_id>/files/", FolderFilesView.as_view()),
    path("files/share-secret/", ShareFileWithSecretView.as_view()),
    path("shared-files/received/", ReceivedSharedFilesView.as_view()),
    path("shared-files/sent/", SentSharedFilesView.as_view()),
    path("shared-files/sent/<int:file_id>/", SentSharedFileDetailView.as_view()),
    path("shared-files/received/<int:file_id>/", SharedFileDetailView.as_view()),
    path("profile/picture/", ProfilePictureDetailView.as_view()),
    path("auth/token/refresh/", RefreshTokenView.as_view()),
    path("auth/logout/", LogoutView.as_view()),
    path("dashboard/stats/", DashboardStatsView.as_view()),
    path("admin/dashboard/", AdminDashboardStatsView.as_view()),
    path("admin/files/", FilesListView.as_view()),
    path("admin/users/",  UsersListView.as_view()),
    path("logs/", ActivityLogListView.as_view()),
    path("logs/<int:pk>/", ActivityLogDetailView.as_view()),


]