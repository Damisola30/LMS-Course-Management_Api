from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.conf import settings

from .seed_utils import seed_into_workspace
from .permissions import HasDeveloper, IsUserUnderDeveloper

class SeedThisWorkspaceView(APIView):
    """
    Dev-only endpoint to populate the *request.workspace* with demo data.
    Protect this in prod.
    """
    permission_classes = [HasDeveloper]

    def post(self, request):
        ws = request.workspace

        # Optional: protect with staff-only or DEBUG
        if not settings.DEBUG and not request.user.is_staff:
            return Response({"detail": "Not allowed in production."}, status=status.HTTP_403_FORBIDDEN)

        # You can accept counts via body, with defaults:
        teacher_count = int(request.data.get("teacher_count", 2))
        student_count = int(request.data.get("student_count", 3))
        guest_count   = int(request.data.get("guest_count", 2))

        seed_into_workspace(ws, username_prefix=None,
                            teacher_count=teacher_count,
                            student_count=student_count,
                            guest_count=guest_count)

        return Response(
            {
                "detail": f"Seeded workspace '{ws.name}'",
                "teachers": teacher_count,
                "students": student_count,
                "guests": guest_count,
            },
            status=status.HTTP_201_CREATED,
        )
