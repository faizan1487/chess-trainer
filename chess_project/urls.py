"""chess_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.core.mail import send_mail
from django.template.loader import render_to_string
import logging
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

logger = logging.getLogger(__name__)

class CustomPasswordResetView(auth_views.PasswordResetView):
    def form_valid(self, form):
        # print("\n=== Password Reset Process Started ===")
        # print("Password reset form is valid")
        # print(f"Email being sent to: {form.cleaned_data['email']}")
        
        # Get the email content before sending
        email = form.cleaned_data['email']
        users = list(form.get_users(email))  # Convert generator to list
        # print(f"Found {len(users)} users with email {email}")
        
        if not users:
            # print("No users found with this email address")
            return super().form_valid(form)
            
        for user in users:
            # print(f"\nGenerating reset link for user: {user.username}")
            token = self.token_generator.make_token(user)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f"{self.request.scheme}://{self.request.get_host()}/accounts/reset/{uidb64}/{token}/"
            # print(f"Reset URL: {reset_url}")
            
            # Get email content
            context = {
                'email': user.email,
                'domain': self.request.get_host(),
                'site_name': 'Chessary',
                'uid': uidb64,
                'user': user,
                'token': token,
                'protocol': self.request.scheme,
            }
            # print("\nEmail Context:")
            # for key, value in context.items():
            #     print(f"{key}: {value}")
            
            # Render email templates
            subject = render_to_string(
                'chess_app/password_reset_subject.txt',
                context
            ).strip()
            message = render_to_string(
                'chess_app/password_reset_email.html',
                context
            )
            
            # print("\nSending email with:")
            # print(f"Subject: {subject}")
            # print(f"Message: {message}")
            
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[user.email],
                    fail_silently=False,
                    html_message=message
                )
                # print("\nPassword reset email sent successfully")
            except Exception as e:
                # print(f"\nError sending password reset email: {str(e)}")
                logger.error(f"Password reset email error: {str(e)}")
                raise
        
        # print("=== Password Reset Process Completed ===\n")
        return super().form_valid(form)

urlpatterns = [
    path('admin/', admin.site.urls),
    # Django authentication URLs
    path(
        'accounts/login/',
        auth_views.LoginView.as_view(
            template_name='chess_app/login.html',
            next_page='home'
        ),
        name='login'
    ),
    path(
        'accounts/logout/',
        auth_views.LogoutView.as_view(next_page='/'),
        name='logout'
    ),
    # Password reset URLs
    path(
        'accounts/password_reset/',
        CustomPasswordResetView.as_view(
            template_name='chess_app/password_reset.html',
            email_template_name='chess_app/password_reset_email.html',
            subject_template_name='chess_app/password_reset_subject.txt',
            success_url=reverse_lazy('password_reset_done')
        ),
        name='password_reset'
    ),
    path(
        'accounts/password_reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='chess_app/password_reset_done.html'
        ),
        name='password_reset_done'
    ),
    path(
        'accounts/reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='chess_app/password_reset_confirm.html',
            success_url=reverse_lazy('password_reset_complete')
        ),
        name='password_reset_confirm'
    ),
    path(
        'accounts/reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='chess_app/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
    # Main application URLs
    path('', include('chess_app.urls')),
]

# Add static file serving for development
if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )
