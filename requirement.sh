pip install transformers
pip install torch
python -c "from transformers import AutoTokenizer, AutoModelForSequenceClassification; global tokenizer, model; tokenizer = AutoTokenizer.from_pretrained('mariagrandury/roberta-base-finetuned-sms-spam-detection'); model = AutoModelForSequenceClassification.from_pretrained('mariagrandury/roberta-base-finetuned-sms-spam-detection')"