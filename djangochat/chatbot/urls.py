from django.urls import path
from chatbot.views import index, ask_question, faq

APP_NAME = 'blog'

urlpatterns = [
    # Página principal onde o partial é carregado
    path('', index, name='index'),
    # URL para a requisição AJAX
    path('ask/', ask_question, name='ask_question'),
    # URL para a página de FAQ
    path('faq/', faq, name='faq'),
]
