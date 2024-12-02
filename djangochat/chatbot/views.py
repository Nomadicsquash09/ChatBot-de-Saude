
from django.shortcuts import render
from django.http import JsonResponse
from chatbot.ai.chatbot_model import ChatbotAI
from django.core.cache import cache


def index(request):
    # Certifique-se de que a página onde o partial será renderizado está aqui
    return render(request, 'chatbot/pages/index.html')


def ask_question(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        question = data.get('question', '')

        chatbot = ChatbotAI()  # Instância do modelo de IA
        response = chatbot.get_response(question)  # Obtém a resposta da IA

        # Retorna a resposta para o cliente
        return JsonResponse({'response': response})

    return JsonResponse({'response': 'Método não permitido.'}, status=405)


def faq(request):
    # Tenta recuperar os dados do FAQ do cache
    faq_data = cache.get('faq_data')

    if not faq_data:
        # Se os dados não estão no cache, calcula e armazena no cache
        chatbot = ChatbotAI(retrain=False)  # Instancia o chatbot
        # Exemplo: lista de tuplas (pergunta, frequência)
        frequent_questions = chatbot.get_most_frequent_questions()

        # Inicializa uma lista para armazenar perguntas, respostas e contagem
        questions_and_answers = []

        # Calcula as respostas para cada pergunta frequente
        for question, count in frequent_questions:
            response = chatbot.get_response(question)
            questions_and_answers.append({
                'question': question,
                'response': response,
                'count': count
            })

        # Armazena os dados no cache por 10 minutos (600 segundos)
        cache.set('faq_data', questions_and_answers, timeout=600)

        # Passa os dados para o template
        faq_data = questions_and_answers

    # Retorna os dados para o template
    return render(request, 'chatbot/pages/faq.html', {
        # Passa a lista de perguntas, respostas e contagem
        'questions_and_answers': faq_data,
    })
