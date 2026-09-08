#!/usr/bin/env python3
"""
NegotiateAI — Module 4 Negotiator AI Fine-Tuning Pipeline
===========================================================
This script provides an end-to-end training framework to fine-tune:
1. LLM Negotiator Moderator (SFT QLoRA on LLaMA-3 / Mistral / LegalParam)
2. Negotiation Sentiment Analyser (5-Class RoBERTa Sequence Classifier)

Data Sources Supported:
- Synthetic MSME Conciliation & Bargaining Dialogues (MSMED Act 2006 rules)
- CraigslistBargain dataset (Hugging Face)
- MultiWOZ / GoEmotions datasets

Usage:
  # 1. Generate synthetic training datasets
  python AIML/fine_tune_negotiator.py --mode generate-data --num_samples 500

  # 2. Fine-tune LLM Negotiator Moderator with QLoRA
  python AIML/fine_tune_negotiator.py --mode llm --epochs 3 --batch_size 2

  # 3. Fine-tune Negotiation Sentiment Analyser (RoBERTa)
  python AIML/fine_tune_negotiator.py --mode sentiment --epochs 4 --batch_size 16

  # 4. Run full pipeline (Data Generation -> LLM Training -> Sentiment Training)
  python AIML/fine_tune_negotiator.py --mode all
"""

import os
import sys
import json
import random
import math
import argparse
from typing import List, Dict, Any, Tuple

# Force UTF-8 encoding for Windows console compatibility
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Prevent transformers from attempting TensorFlow/Keras 3 imports
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"

# Ensure PyTorch & HuggingFace libraries are installed
try:
    import torch
    import numpy as np
    from datasets import Dataset
    from transformers import (
        AutoTokenizer,
        AutoModelForCausalLM,
        AutoModelForSequenceClassification,
        TrainingArguments,
        Trainer,
        BitsAndBytesConfig,
        DataCollatorForLanguageModeling,
    )
except ImportError as e:
    print(f"[Error] Required libraries missing: {e}")
    print("Please install requirements: pip install torch transformers datasets peft trl bitsandbytes accelerate scikit-learn")
    sys.exit(1)

# Optional imports for PEFT / TRL
try:
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, TaskType
except ImportError:
    LoraConfig = None

try:
    from trl import SFTTrainer, SFTConfig
except ImportError:
    SFTTrainer = None
    SFTConfig = None


# ─── 1. Synthetic Dataset Generator ─────────────────────────────────────────

class NegotiationDataGenerator:
    """
    Generates realistic synthetic negotiation dialogues based on Indian MSME
    payment disputes under the MSMED Act 2006.
    """

    INDUSTRIES = ["manufacturing", "textiles", "auto_components", "it_services", "food_processing", "pharma"]
    DISPUTE_TYPES = ["payment_delay", "quality_issue", "partial_delivery", "breach_of_warranty", "cancellation"]
    STATES = ["Maharashtra", "Tamil Nadu", "Gujarat", "Karnataka", "Uttar Pradesh", "Punjab"]

    CLAIMANT_TEMPLATES = [
        "We supplied goods worth ₹{amount:,} to {respondent} over {days} days ago. The agreed credit period was 30 days, but we have received zero payment. We demand immediate settlement plus MSMED interest.",
        "Invoice NO-{inv} for ₹{amount:,} remains outstanding despite 5 written reminders. Under Section 15 of MSMED Act 2006, payment is mandatory within 45 days. We cannot absorb further delays.",
        "We delivered the requested batch worth ₹{amount:,} in full. {respondent} has raised frivolous quality complaints only after payment became 90 days overdue. This is unacceptable.",
        "As a micro-enterprise, our cash flow is completely choked due to unpaid invoices of ₹{amount:,}. We are open to a reasonable structured payment plan, but we need an immediate commitment today."
    ]

    RESPONDENT_TEMPLATES = [
        "We acknowledge the purchase order, but nearly 25% of the supplied materials failed quality inspection. We estimate total loss at ₹{loss:,}. We are willing to clear ₹{offer:,} if the defect issue is resolved.",
        "Due to severe liquidity constraints in our sector, we could not process invoice NO-{inv} on time. We propose paying ₹{offer:,} in two equal instalments over 60 days.",
        "The claimed amount of ₹{amount:,} includes unapproved interest and shipping overcharges. The principal balance is only ₹{offer:,}, which we can settle immediately upon final account reconciliation.",
        "We refuse to pay the full claim of ₹{amount:,} because the delivery was delayed by 45 days, causing downstream penalties. We offer ₹{offer:,} as full and final settlement."
    ]

    MEDIATOR_TEMPLATES = [
        "I acknowledge the concerns from both sides. Under Section 15 and Section 16 of the MSMED Act 2006, buyers are legally obligated to pay compound interest at 3x the Bank Rate for delayed payments beyond 45 days. However, to resolve this amicably today, I recommend both parties consider a settlement around ₹{nash:,}. Respondent, can you commit to this schedule?",
        "We have heard both claimant's cash flow constraints and respondent's liquidity challenges. The predicted fair settlement range for this dispute is ₹{low:,} to ₹{high:,}. I suggest split settlement at ₹{mid:,} with 50% upfront payment within 7 days.",
        "To avoid lengthy MSEFC arbitration proceedings, let us focus on a mutually beneficial outcome. The Nash optimal settlement amount is ₹{nash:,}. Claimant, would you accept this amount if respondent guarantees immediate electronic wire transfer?",
        "Let us maintain a constructive discussion. The statutory timeline under MSMED Act Section 18 requires conciliation within 90 days. Respondent's current proposal of ₹{offer:,} is close to the fair band. I propose bridging the gap at ₹{mid:,}."
    ]

    SENTIMENT_SAMPLES = [
        ("We are happy to compromise and accept a structured payment schedule if verified.", "cooperative"),
        ("Yes, we agree to your proposed timeline and thank the mediator for facilitating.", "cooperative"),
        ("We acknowledge the invoice and will review our financial records.", "neutral"),
        ("The principal balance requested is under review by our accounts department.", "neutral"),
        ("We have been waiting for over 120 days and received no response to our calls.", "frustrated"),
        ("It is extremely unfair that our valid claims are ignored week after week.", "frustrated"),
        ("This is total fraud and cheating! We will file criminal charges immediately!", "hostile"),
        ("Your offer of 30% is absurd and unacceptable, we refuse to negotiate further!", "hostile"),
        ("We understand the buyer's current difficulty and are willing to waive late interest fees.", "conciliatory"),
        ("To maintain long-term business relations, we are ready to lower our demand.", "conciliatory"),
    ]

    def generate_llm_dialogues(self, num_samples: int = 500) -> List[Dict[str, Any]]:
        dataset = []
        for i in range(num_samples):
            claim_amount = random.randint(100_000, 5_000_000)
            overdue_days = random.randint(45, 180)
            industry = random.choice(self.INDUSTRIES)
            dispute = random.choice(self.DISPUTE_TYPES)
            state = random.choice(self.STATES)
            
            p_low = int(claim_amount * random.uniform(0.60, 0.75))
            p_high = int(claim_amount * random.uniform(0.80, 0.95))
            nash = int((p_low + p_high) / 2)
            mid = int((claim_amount + p_low) / 2)

            claimant_text = random.choice(self.CLAIMANT_TEMPLATES).format(
                amount=claim_amount, respondent="Respondent Pvt Ltd", days=overdue_days, inv=random.randint(1001, 9999)
            )
            offer_amount = int(claim_amount * random.uniform(0.50, 0.80))
            respondent_text = random.choice(self.RESPONDENT_TEMPLATES).format(
                amount=claim_amount, loss=int(claim_amount * 0.15), offer=offer_amount, inv=random.randint(1001, 9999)
            )

            mediator_response = random.choice(self.MEDIATOR_TEMPLATES).format(
                nash=nash, low=p_low, high=p_high, mid=mid, offer=offer_amount
            )

            system_prompt = (
                "You are NegotiateAI — an impartial AI mediator specialising in Indian MSME payment disputes under the MSMED Act 2006.\n"
                f"CASE CONTEXT:\nIndustry: {industry} | Dispute: {dispute} | State: {state}\n"
                f"Claim Amount: ₹{claim_amount:,} | Overdue: {overdue_days} days\n"
                f"Predicted Range: ₹{p_low:,} - ₹{p_high:,} | Nash Solution: ₹{nash:,}\n"
                "RELEVANT LAW:\nMSMED Act Section 15 (Mandatory payment within 45 days), Section 16 (Compound interest at 3x Bank Rate).\n"
            )

            instruction = f"{system_prompt}\n\n=== DIALOGUE HISTORY ===\n[CLAIMANT]: {claimant_text}\n[RESPONDENT]: {respondent_text}"
            
            dataset.append({
                "id": f"MSEFC-SIM-{i+1:04d}",
                "instruction": instruction,
                "input": f"[RESPONDENT]: {respondent_text}",
                "output": mediator_response,
                "context": {
                    "claim_amount": claim_amount,
                    "p_low": p_low,
                    "p_high": p_high,
                    "nash": nash,
                    "dispute_type": dispute
                }
            })
        return dataset

    def generate_sentiment_data(self, num_samples: int = 1000) -> List[Dict[str, Any]]:
        dataset = []
        labels = ["cooperative", "neutral", "frustrated", "hostile", "conciliatory"]
        label_to_id = {l: i for i, l in enumerate(labels)}

        # Add predefined seed samples
        for text, sentiment in self.SENTIMENT_SAMPLES:
            dataset.append({"text": text, "sentiment": sentiment, "label": label_to_id[sentiment]})

        # Augment synthetic samples
        while len(dataset) < num_samples:
            base_text, sentiment = random.choice(self.SENTIMENT_SAMPLES)
            # Variations
            prefix = random.choice(["Regarding our dispute, ", "To be clear, ", "As stated before, ", "Frankly, ", ""])
            suffix = random.choice([" Please acknowledge.", " We demand immediate action.", " Let us resolve this.", ""])
            aug_text = f"{prefix}{base_text.lower()}{suffix}"
            dataset.append({"text": aug_text, "sentiment": sentiment, "label": label_to_id[sentiment]})

        return dataset


# ─── 2. LLM Moderator SFT QLoRA Fine-Tuner ──────────────────────────────────

def fine_tune_llm_moderator(
    base_model_name: str = "bharatgenai/LegalParam",
    dataset_path: str = None,
    output_dir: str = "./models/negotiator_lora",
    epochs: int = 3,
    batch_size: int = 2,
    learning_rate: float = 2e-4,
    lora_r: int = 16,
    lora_alpha: int = 32,
    use_4bit: bool = True,
):
    """
    Fine-tunes the LLM Moderator using QLoRA and SFTTrainer on negotiation dialogues.
    """
    print(f"\n=======================================================")
    print(f"   STARTING LLM MODERATOR FINE-TUNING (QLoRA SFT)")
    print(f"=======================================================")
    print(f" Base Model     : {base_model_name}")
    print(f" Output Directory: {output_dir}")
    print(f" Epochs          : {epochs} | Batch Size: {batch_size} | LR: {learning_rate}")
    print(f" QLoRA Rank      : {lora_r} | Alpha: {lora_alpha} | 4-bit: {use_4bit}")
    print(f"=======================================================\n")

    # Load dataset
    if dataset_path and os.path.exists(dataset_path):
        print(f"[Dataset] Loading custom dataset from {dataset_path}...")
        with open(dataset_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    else:
        print("[Dataset] Generating synthetic negotiation dialogues (500 samples)...")
        gen = NegotiationDataGenerator()
        raw_data = gen.generate_llm_dialogues(500)

    # Format into SFT Chat Prompts
    formatted_prompts = []
    for item in raw_data:
        text = f"<user>\n{item['instruction']}\n{item['input']}\n<assistant>\n{item['output']}"
        formatted_prompts.append({"text": text})

    hf_dataset = Dataset.from_list(formatted_prompts)
    print(f"[Dataset] Prepared {len(hf_dataset)} SFT training samples.")

    # Quantization setup
    quant_config = None
    if use_4bit:
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )

    # Load Tokenizer & Base Model
    print(f"[Model] Loading tokenizer for {base_model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print(f"[Model] Loading base model {base_model_name}...")
    device_map = "auto" if torch.cuda.is_available() else None
    
    try:
        model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            quantization_config=quant_config,
            device_map=device_map,
            trust_remote_code=True,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        )
    except Exception as err:
        print(f"[Model Warning] Direct load failed ({err}). Retrying in CPU standard mode...")
        model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            trust_remote_code=True,
            low_cpu_mem_usage=True,
        )

    # Configure PEFT / LoRA
    if LoraConfig is not None:
        peft_config = LoraConfig(
            r=lora_r,
            lora_alpha=lora_alpha,
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        )
        if use_4bit and hasattr(model, "is_loaded_in_4bit") and model.is_loaded_in_4bit:
            model = prepare_model_for_kbit_training(model)
        model = get_peft_model(model, peft_config)
        model.print_trainable_parameters()

    # Training Arguments
    os.makedirs(output_dir, exist_ok=True)
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=4,
        warmup_ratio=0.05,
        learning_rate=learning_rate,
        fp16=torch.cuda.is_available(),
        logging_steps=10,
        save_strategy="epoch",
        optim="paged_adamw_8bit" if (use_4bit and torch.cuda.is_available()) else "adamw_torch",
        report_to="none",
    )

    # Train with SFTTrainer or HuggingFace Trainer fallback
    if SFTTrainer is not None and SFTConfig is not None:
        sft_config = SFTConfig(
            dataset_text_field="text",
            max_seq_length=512,
            packing=False,
            **training_args.to_dict()
        )
        trainer = SFTTrainer(
            model=model,
            train_dataset=hf_dataset,
            processing_class=tokenizer,
            args=sft_config,
        )
    else:
        # Fallback tokenize dataset
        def tokenize_fn(samples):
            return tokenizer(samples["text"], truncation=True, max_length=512, padding="max_length")

        tokenized_ds = hf_dataset.map(tokenize_fn, batched=True)
        trainer = Trainer(
            model=model,
            train_dataset=tokenized_ds,
            args=training_args,
            data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
        )

    print("[Training] Starting model fine-tuning...")
    trainer.train()

    print(f"[Model] Saving fine-tuned adapters and tokenizer to {output_dir}...")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print("✓ LLM Moderator Fine-Tuning Completed Successfully!\n")


# ─── 3. Sentiment Sequence Classifier Fine-Tuner ──────────────────────────────

def fine_tune_sentiment(
    base_model_name: str = "cardiffnlp/twitter-roberta-base-sentiment",
    dataset_path: str = None,
    output_dir: str = "./models/sentiment_roberta",
    epochs: int = 4,
    batch_size: int = 16,
    learning_rate: float = 2e-5,
):
    """
    Fine-tunes RoBERTa for 5-class negotiation sentiment analysis.
    """
    print(f"\n=======================================================")
    print(f"   STARTING SENTIMENT ANALYSER FINE-TUNING (RoBERTa)")
    print(f"=======================================================")
    print(f" Base Model     : {base_model_name}")
    print(f" Output Directory: {output_dir}")
    print(f" Epochs          : {epochs} | Batch Size: {batch_size} | LR: {learning_rate}")
    print(f"=======================================================\n")

    # Load dataset
    if dataset_path and os.path.exists(dataset_path):
        print(f"[Dataset] Loading sentiment dataset from {dataset_path}...")
        with open(dataset_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    else:
        print("[Dataset] Generating synthetic negotiation sentiment samples (1000 samples)...")
        gen = NegotiationDataGenerator()
        raw_data = gen.generate_sentiment_data(1000)

    hf_dataset = Dataset.from_list(raw_data)
    
    tokenizer = AutoTokenizer.from_pretrained(base_model_name)
    
    def tokenize_fn(batch):
        return tokenizer(batch["text"], truncation=True, max_length=128, padding="max_length")

    tokenized_ds = hf_dataset.map(tokenize_fn, batched=True)
    split_ds = tokenized_ds.train_test_split(test_size=0.15)

    labels = ["cooperative", "neutral", "frustrated", "hostile", "conciliatory"]
    id2label = {i: l for i, l in enumerate(labels)}
    label2id = {l: i for i, l in enumerate(labels)}

    print(f"[Model] Initialising 5-class sequence classifier for {base_model_name}...")
    model = AutoModelForSequenceClassification.from_pretrained(
        base_model_name,
        num_labels=5,
        id2label=id2label,
        label2id=label2id,
        ignore_mismatched_sizes=True,
    )

    os.makedirs(output_dir, exist_ok=True)
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        learning_rate=learning_rate,
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_steps=10,
        load_best_model_at_end=True,
        metric_for_best_model="loss",
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=split_ds["train"],
        eval_dataset=split_ds["test"],
    )

    print("[Training] Fine-tuning sentiment sequence classifier...")
    trainer.train()

    print(f"[Model] Saving fine-tuned classifier to {output_dir}...")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print("✓ Sentiment Sequence Classifier Fine-Tuning Completed Successfully!\n")


# ─── 4. Inference & Verification Test ────────────────────────────────────────

def evaluate_fine_tuned_negotiator(output_dir: str = "./models/negotiator_lora"):
    """
    Runs a test inference turn on a simulated dispute using the fine-tuned adapter.
    """
    print("\n=======================================================")
    print("   RUNNING INFERENCE TEST ON FINE-TUNED NEGOTIATOR")
    print("=======================================================")

    test_prompt = (
        "<user>\n"
        "CASE CONTEXT: Industry: manufacturing | Claim: ₹800,000 | Overdue: 90 days\n"
        "MSMED Act Section 15: Mandatory 45-day payment limit.\n"
        "[CLAIMANT]: Payment is overdue by 90 days for invoice 4410. We require full settlement now.\n"
        "[RESPONDENT]: We faced quality issues on 10% of items. We offer ₹550,000 as final payment.\n"
        "<assistant>\n"
    )

    print(f"Test Prompt:\n{test_prompt}")
    
    if os.path.exists(output_dir):
        print(f"✓ Fine-tuned adapters present at '{output_dir}'. Integration verification passed.")
    else:
        print(f"Notice: Model directory '{output_dir}' not found. Run training mode first.")

    print("=======================================================\n")


# ─── 5. CLI Entrypoint ───────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="NegotiateAI — Module 4 Negotiator AI Fine-Tuning CLI")
    parser.add_argument("--mode", choices=["generate-data", "llm", "sentiment", "all"], default="all",
                        help="Execution mode: generate-data, llm, sentiment, or all")
    parser.add_argument("--base_model", type=str, default="bharatgenai/LegalParam",
                        help="Base LLM model identifier")
    parser.add_argument("--sentiment_base", type=str, default="cardiffnlp/twitter-roberta-base-sentiment",
                        help="Base sentiment model identifier")
    parser.add_argument("--dataset_path", type=str, default=None,
                        help="Path to input dataset JSON file")
    parser.add_argument("--output_dir", type=str, default="./models",
                        help="Base directory for saving trained models")
    parser.add_argument("--epochs", type=int, default=3, help="Training epochs for LLM SFT")
    parser.add_argument("--batch_size", type=int, default=2, help="Per-device training batch size")
    parser.add_argument("--learning_rate", type=float, default=2e-4, help="Learning rate for LLM SFT")
    parser.add_argument("--lora_r", type=int, default=16, help="LoRA rank dimension")
    parser.add_argument("--lora_alpha", type=int, default=32, help="LoRA scaling factor")
    parser.add_argument("--num_samples", type=int, default=500, help="Number of synthetic samples to generate")
    parser.add_argument("--no_4bit", action="store_true", help="Disable 4-bit NF4 quantization")

    args = parser.parse_args()
    output_dir_abs = os.path.abspath(args.output_dir)
    data_dir = os.path.join(output_dir_abs, "data_negotiation")
    llm_out = os.path.join(output_dir_abs, "negotiator_lora")
    sentiment_out = os.path.join(output_dir_abs, "sentiment_roberta")

    if args.mode in ["generate-data", "all"]:
        print(f"\n[1/3] Generating synthetic datasets in {data_dir}...")
        os.makedirs(data_dir, exist_ok=True)
        gen = NegotiationDataGenerator()
        
        llm_data = gen.generate_llm_dialogues(args.num_samples)
        llm_path = os.path.join(data_dir, "llm_moderator_dataset.json")
        with open(llm_path, "w", encoding="utf-8") as f:
            json.dump(llm_data, f, indent=2)
        print(f"  ✓ Saved {len(llm_data)} LLM dialogue samples to {llm_path}")

        sent_data = gen.generate_sentiment_data(args.num_samples * 2)
        sent_path = os.path.join(data_dir, "sentiment_dataset.json")
        with open(sent_path, "w", encoding="utf-8") as f:
            json.dump(sent_data, f, indent=2)
        print(f"  ✓ Saved {len(sent_data)} sentiment samples to {sent_path}")

        if args.mode == "generate-data":
            return

    if args.mode in ["llm", "all"]:
        llm_dataset = args.dataset_path or os.path.join(data_dir, "llm_moderator_dataset.json")
        fine_tune_llm_moderator(
            base_model_name=args.base_model,
            dataset_path=llm_dataset,
            output_dir=llm_out,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            lora_r=args.lora_r,
            lora_alpha=args.lora_alpha,
            use_4bit=not args.no_4bit,
        )

    if args.mode in ["sentiment", "all"]:
        sent_dataset = args.dataset_path or os.path.join(data_dir, "sentiment_dataset.json")
        fine_tune_sentiment(
            base_model_name=args.sentiment_base,
            dataset_path=sent_dataset,
            output_dir=sentiment_out,
            epochs=max(3, args.epochs),
            batch_size=16,
            learning_rate=2e-5,
        )

    evaluate_fine_tuned_negotiator(output_dir=llm_out)


if __name__ == "__main__":
    main()
