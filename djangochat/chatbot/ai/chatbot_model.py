import os
import json
from pathlib import Path
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, Trainer,
    TrainingArguments, DataCollatorWithPadding
)
from datasets import Dataset
from collections import Counter

BASE_DIR = Path(__file__).parent
CACHE_DIR = BASE_DIR / 'transformers_cache'
os.environ['TRANSFORMERS_CACHE'] = str(CACHE_DIR)
os.environ['TORCH_HOME'] = str(CACHE_DIR)

DATA_FILE = BASE_DIR / 'data.json'
USER_DATA_FILE = BASE_DIR / 'user_quest.json'
MODEL_DIR = BASE_DIR / 'saved_model_opt'


class ChatbotAI():
    def __init__(self, retrain=False):
        if MODEL_DIR.exists() and not retrain:
            self.model = AutoModelForCausalLM.from_pretrained(MODEL_DIR)
            self.tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
            self.tokenizer.pad_token = self.tokenizer.eos_token
        else:
            with open(DATA_FILE, 'r', encoding='utf-8') as file:
                data = json.load(file)
            self.dataset = Dataset.from_list(data)
            train_test_split = self.dataset.train_test_split(test_size=.2)
            self.train_dataset = train_test_split['train']
            self.val_dataset = train_test_split['test']
            self.tokenizer = AutoTokenizer.from_pretrained('facebook/opt-350m')
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.tokenized_train_dataset = self.train_dataset.map(
                self.tokenize_data_function, batched=True)
            self.tokenized_val_dataset = self.val_dataset.map(
                self.tokenize_data_function, batched=True)
            self.model = AutoModelForCausalLM.from_pretrained(
                'facebook/opt-350m')
            self.training_args = TrainingArguments(
                output_dir=str(BASE_DIR / 'results'),
                num_train_epochs=3,
                per_device_train_batch_size=4,
                gradient_accumulation_steps=2,
                save_steps=10_000,
                save_total_limit=1,
                fp16=True,
                run_name='opt_finetuning',
                report_to="none",
                logging_dir=str(BASE_DIR / 'logs'),
                evaluation_strategy='epoch',
            )
            self.data_collator = DataCollatorWithPadding(
                tokenizer=self.tokenizer)
            self.trainer = Trainer(
                model=self.model,
                args=self.training_args,
                train_dataset=self.tokenized_train_dataset,
                eval_dataset=self.tokenized_val_dataset,
                data_collator=self.data_collator,
            )
            self.train()

    def tokenize_data_function(self, data_dict) -> list:
        questions = [
            f"Pergunta: {data_dict['pergunta'][i]}"
            for i in range(len(data_dict['pergunta']))
        ]
        responses = [
            f"Resposta: {data_dict['resposta'][i]}"
            for i in range(len(data_dict['resposta']))
        ]
        inputs = [
            f"Pergunta: {pergunta} \nResposta: {resposta}"
            for pergunta, resposta in zip(questions, responses)
        ]

        encodings = self.tokenizer(
            inputs,
            padding='max_length',
            truncation=True,
            max_length=150,
            return_tensors='pt',
        )
        encodings['labels'] = encodings['input_ids'].clone()
        return encodings

    def train(self):
        self.trainer.train()
        self.model.save_pretrained(MODEL_DIR)
        self.tokenizer.save_pretrained(MODEL_DIR)

    def get_response(self, question):
        input_text = f"Pergunta: {question} Resposta:"
        input_ids = self.tokenizer.encode(input_text, return_tensors='pt')
        output = self.model.generate(
            input_ids,
            max_length=150,
            num_return_sequences=1,
            do_sample=True,
            top_k=50,
            top_p=0.75,
            temperature=0.5,
            repetition_penalty=1.2,
        )
        response = self.tokenizer.decode(output[0], skip_special_tokens=True)
        response = response.split("Resposta:")[-1].strip()

        self._save_response(question, response)

        return response

    def get_most_frequent_questions(self, n=5):
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as file:
            data = json.load(file)

        questions = [entry["pergunta"] for entry in data]
        question_counts = Counter(questions)
        most_common_questions = question_counts.most_common(n)

        return most_common_questions

    def _save_response(self, question, response):
        user_data = {
            "pergunta": question,
            "resposta": response
        }

        if USER_DATA_FILE.exists():
            with open(USER_DATA_FILE, 'r', encoding='utf-8') as file:
                data = json.load(file)
        else:
            data = []

        data.append(user_data)
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    chatbot = ChatbotAI(retrain=False)
    while True:
        question = input("Escreve ai: ")
        response = chatbot.get_response(question)
        print(response)
