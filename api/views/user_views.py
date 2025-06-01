from django.http import JsonResponse
from rest_framework import permissions, status
from rest_framework.views import APIView

from api.serializers import RegisterUserSerializer


class SignupView(APIView):
    """
    View to handle user registration.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return JsonResponse({'message': 'User created successfully', 'user_id': user.id}, status=status.HTTP_201_CREATED)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
