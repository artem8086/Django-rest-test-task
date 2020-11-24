from django.db import IntegrityError
from django.http import Http404
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import CreateAPIView, GenericAPIView, RetrieveUpdateDestroyAPIView, ListAPIView, \
    ListCreateAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework_jwt.serializers import jwt_payload_handler, jwt_encode_handler

from users.models import User, BlogPost
from users.serializers import UserRegistrationSerializer, UserLoginSerializer, TokenSerializer, UserAdminSerializer, \
    UserSerializer, BlogPostSerializer, BlogPostOwnerSerializer
from users.tokens import account_activation_token


class UserRegistrationAPIView(CreateAPIView):
    permission_classes = ()
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        user = serializer.instance
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)

        data = {
            "uid": uid,
            "token": token,
            "activate_link": reverse('users:activate', args=[uid, token], request=request)
        }

        headers = self.get_success_headers(serializer.data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(is_active=False)


@api_view(['GET'])
@permission_classes([])
def user_activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        data = UserAdminSerializer(user).data
        data['jwt_token'] = token
        return Response(data, status=status.HTTP_201_CREATED)
    else:
        return Response({'detail': 'Activation link is invalid!'}, status=status.HTTP_400_BAD_REQUEST)


class UserLoginAPIView(GenericAPIView):
    permission_classes = ()
    serializer_class = UserLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.user

            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
            return Response(
                data=TokenSerializer({'key': token}).data,
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )


class UserListAPIView(ListAPIView):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['date_joined']


class UserMeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            data=UserAdminSerializer(request.user).data,
            status=status.HTTP_200_OK,
        )


class AdminUserListCreateAPIView(ListCreateAPIView):
    queryset = User.objects.all()
    permission_classes = [IsAdminUser]
    serializer_class = UserAdminSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['date_joined']


class AdminUserManagementAPIView(RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    permission_classes = [IsAdminUser]
    serializer_class = UserAdminSerializer


class BlogPostListCreateAPIView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BlogPostSerializer
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ['^title']
    ordering_fields = ['created']
    ordering = ['created']

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        return BlogPost.objects.filter(owner=self.request.user)


class BlogPostSubscriberListAPIView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BlogPostSerializer
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ['^title']
    ordering_fields = ['created']
    ordering = ['created']

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        if not self.request.user.subscriptions.filter(pk=user_id).exists():
            raise Http404
        return BlogPost.objects.filter(owner=user_id)


class FeedBlogPostListAPIView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BlogPostOwnerSerializer
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ['^title']
    ordering_fields = ['created']
    ordering = ['created']

    def get_queryset(self):
        return BlogPost.objects.filter(owner__in=self.request.user.subscriptions.all())


class BlogPostManagementAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BlogPostSerializer

    def get_queryset(self):
        return BlogPost.objects.filter(owner=self.request.user)


class AdminBlogPostListAPIView(ListAPIView):
    queryset = BlogPost.objects.all()
    permission_classes = [IsAdminUser]
    serializer_class = BlogPostOwnerSerializer
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ['^title']
    ordering_fields = ['created']
    ordering = ['created']


class AdminBlogPostManagementAPIView(RetrieveUpdateDestroyAPIView):
    queryset = BlogPost.objects.all()
    permission_classes = [IsAdminUser]
    serializer_class = BlogPostSerializer


class ListSubscribersAPIView(ListAPIView):
    queryset = BlogPost.objects.all()
    permission_classes = [IsAdminUser]
    serializer_class = UserSerializer

    def get_queryset(self):
        return self.request.user.subscriptions.all()


class UserSubscribeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        user = request.user
        if user_id == user.id:
            return Response(
                data={'detail': 'You cann\'t subscribe on yourself!'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            if user.subscriptions.filter(pk=user_id).exists():
                return Response(
                    data={'detail': f'You are already subscribe on user with id {user_id}'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.subscriptions.add(user_id)
            user.save()
            return Response(
                data={'message': f'You successfully subscribe on user with id {user_id}'},
                status=status.HTTP_200_OK,
            )
        except IntegrityError:
            return Response(
                data={'detail': f'User with id {user_id} not found!'},
                status=status.HTTP_404_NOT_FOUND,
            )


class UserUnsubscribeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        user = request.user
        if user_id == user.id:
            return Response(
                data={'detail': 'You cann\'t unsubscribe on yourself!'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not user.subscriptions.filter(pk=user_id).exists():
            return Response(
                data={'detail': f'You are not subscribe on user with id {user_id}'},
                status=status.HTTP_404_NOT_FOUND,
            )
        user.subscriptions.remove(user_id)
        user.save()
        return Response(
            data={'message': f'You successfully unsubscribe on user with id {user_id}'},
            status=status.HTTP_200_OK,
        )

