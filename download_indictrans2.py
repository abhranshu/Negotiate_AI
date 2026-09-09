from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

print("Downloading IndicTrans2 model...")
model = AutoModelForSeq2SeqLM.from_pretrained("ai4bharat/indictrans2-en-indic-dist-200M")
tok   = AutoTokenizer.from_pretrained("ai4bharat/indictrans2-en-indic-dist-200M")

model.save_pretrained("./data/indictrans2")
tok.save_pretrained("./data/indictrans2")

print("Done! Saved to ./data/indictrans2")
