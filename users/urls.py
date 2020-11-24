from django.urls import path, include
from users.views import UserRegistrationAPIView, UserLoginAPIView, AdminUserManagementAPIView, UserListAPIView, \
    AdminUserListCreateAPIView, BlogPostListCreateAPIView, BlogPostManagementAPIView, AdminBlogPostManagementAPIView, \
    AdminBlogPostListAPIView, UserSubscribeAPIView, UserUnsubscribeAPIView, FeedBlogPostListAPIView, UserMeAPIView, \
    user_activate, BlogPostSubscriberListAPIView, ListSubscribersAPIView

admin_urls = [
    path('users', AdminUserListCreateAPIView.as_view(), name="user_admin_list"),
    path('users/<int:pk>', AdminUserManagementAPIView.as_view(), name="admin_user_management"),

    path('posts', AdminBlogPostListAPIView.as_view(), name="admin_post_list"),
    path('posts/<int:pk>', AdminBlogPostManagementAPIView.as_view(), name="post_management"),
]

post_urls = [
    path('my', BlogPostListCreateAPIView.as_view(), name="post_list"),
    path('<int:user_id>/sub', BlogPostSubscriberListAPIView.as_view(), name="post_list"),
    path('feed', FeedBlogPostListAPIView.as_view(), name="post_feed"),
    path('<int:pk>', BlogPostManagementAPIView.as_view(), name="post_management"),
]

user_urls = [
    path('', UserListAPIView.as_view(), name="user_list"),
    path('me', UserMeAPIView.as_view(), name="user_me"),

    path('<int:user_id>/subscribe', UserSubscribeAPIView.as_view(), name="subscribe"),
    path('<int:user_id>/unsubscribe', UserUnsubscribeAPIView.as_view(), name="unsubscribe"),

    path('subscriptions', ListSubscribersAPIView.as_view(), name='subs'),
]

account_urls = [
    path('register', UserRegistrationAPIView.as_view(), name="register"),
    path('login', UserLoginAPIView.as_view(), name="login"),
    path('activate/<uidb64>/<token>', user_activate, name="activate"),
]

urlpatterns = [
    path('admin/', include(admin_urls)),
    path('users/', include(user_urls)),
    path('posts/', include(post_urls)),
    path('account/', include(account_urls)),
]

app_name = 'users'
