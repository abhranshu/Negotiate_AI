# NegotiateAI — Negotiator AI Fine-Tuning Guide (Module 4)

This document provides a complete guide for fine-tuning the two machine learning components of **Module 4 (Real-Time Multilingual Negotiation AI)** in NegotiateAI:

1. **LLM Negotiation Moderator**: Impartial mediator LLM fine-tuned via QLoRA (SFT) to reframe disputes, maintain neutrality, suggest Nash/Rubinstein compromises, and ground citations in the **MSMED Act 2006 (Sections 15–23)**.
2. **Negotiation Sentiment Analyser**: 5-class RoBERTa sequence classifier (`cooperative`, `neutral`, `frustrated`, `hostile`, `conciliatory`) for real-time conflict and deadlock detection.

---

## 1. System Architecture & Fine-Tuning Pipeline

```
+-----------------------------------------------------------------------------------+
|                            FINE-TUNING DATA PIPELINE                              |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  [ Synthetic MSME Dialogues ]     [ CraigslistBargain ]     [ MultiWOZ / GoEmotions ] |
|  (MSMED Act 2006 context)         (Human Bargaining)        (Conflict Sentiments)   |
|               |                             |                          |          |
|               v                             v                          v          |
|  +--------------------------+  +-------------------------+  +------------------+  |
|  | SFT Dialogue Formatting  |  |  Bargaining Extraction  |  | Sentiment Labels |  |
|  +--------------------------+  +-------------------------+  +------------------+  |
|               \                             |                          /          |
|                +----------------------------+-------------------------+           |
|                                             |                                     |
|                                             v                                     |
|                              +------------------------------+                     |
|                              |    fine_tune_negotiator.py    |                     |
|                              +------------------------------+                     |
|                                      /              \                             |
|                                     /                \                            |
|                                    v                  v                           |
|             +----------------------------+     +----------------------------+     |
|             | 1. LLM Moderator (QLoRA)   |     | 2. Sentiment Classifier    |     |
|             | Base: bharatgenai/LegalParam|    | Base: roberta-base /       |     |
|             |   or Mistral-7B / LLaMA-3  |     | cardiffnlp-roberta-sentiment|     |
|             +----------------------------+     +----------------------------+     |
|                                    |                  |                           |
|                                    v                  v                           |
|             +----------------------------+     +----------------------------+     |
|             | Saved Adapter Checkpoints  |     | Saved Classifier Weights   |     |
|             |  models/negotiator_lora    |     | models/sentiment_roberta   |     |
|             +----------------------------+     +----------------------------+     |
|                                    \                  /                           |
|                                     v                v                            |
|                       +------------------------------------------+                |
|                       | Loaded into AIML/negotiation_ai.py       |                |
|                       +------------------------------------------+                |
+-----------------------------------------------------------------------------------+
```

---

## 2. Hardware & Prerequisites

| Model Component | Minimum Hardware | Recommended Hardware | Quantization |
|---|---|---|---|
| **LLM Moderator (QLoRA)** | 8 GB GPU VRAM (RTX 3060 / T4) | 16+ GB VRAM (RTX 4090 / A10G / A100) | 4-bit NF4 (`bitsandbytes`) |
| **Sentiment Analyser (RoBERTa)** | 4 GB GPU VRAM or CPU | 8 GB VRAM | FP16 / FP32 |

### Environment Requirements

Install core dependencies using Python 3.10+:

```bash
pip install torch>=2.1.0 transformers>=4.40.0 datasets>=2.18.0 accelerate>=0.27.0 peft>=0.9.0 trl>=0.8.0 bitsandbytes>=0.42.0 scikit-learn pandas
```

---

## 3. Dataset Format & Curation

Fine-tuning requires structured data formatted specifically for each sub-model.

### A. LLM Moderator SFT Dataset Structure

The LLM is trained on Instruction/Chat turns formatted as follows:

```json
{
  "instruction": "System prompt containing case facts, claim amount, predicted settlement range, Nash solution, legal RAG context, and recent turn history.",
  "input": "[CLAIMANT]: We delivered 500 units 90 days ago. Payment of ₹5,00,000 is long overdue.",
  "output": "I understand your concern regarding the 90-day payment delay. Under Section 15 of the MSMED Act 2006, payment must be made within 45 days. Respondent, what is your proposal regarding the outstanding balance of ₹5,00,000?"
}
```

Prompt templates follow the chat template convention used by `bharatgenai/LegalParam` and `Mistral-7B`:
```text
<user>
[SYSTEM PROMPT & CASE CONTEXT]
[RECENT DIALOGUE]
[LAST TURN]
<assistant>
[GROUND TRUTH MEDIATOR RESPONSE]
```

### B. Sentiment Classifier Dataset Structure

Sentiment dataset maps negotiation utterances to 5 discrete labels:

```json
{
  "text": "This is total fraud, we will file a criminal suit immediately!",
  "label": 3  // 0: cooperative, 1: neutral, 2: frustrated, 3: hostile, 4: conciliatory
}
```

---

## 4. Running `fine_tune_negotiator.py`

The script [`fine_tune_negotiator.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/fine_tune_negotiator.py) provides a CLI to run dataset generation, LLM fine-tuning, sentiment classifier training, or all steps sequentially.

### Command Line Reference

```bash
python fine_tune_negotiator.py [OPTIONS]
```

| Argument | Type | Default | Description |
|---|---|---|---|
| `--mode` | `str` | `all` | Training mode: `generate-data`, `llm`, `sentiment`, or `all` |
| `--base_model` | `str` | `bharatgenai/LegalParam` | Base LLM model ID on Hugging Face |
| `--sentiment_base` | `str` | `cardiffnlp/twitter-roberta-base-sentiment` | Base sentiment model ID |
| `--dataset_path` | `str` | `None` | Path to custom JSON dataset (generates synthetic data if omitted) |
| `--output_dir` | `str` | `./models` | Directory to save fine-tuned adapters and checkpoints |
| `--epochs` | `int` | `3` | Number of training epochs for LLM SFT |
| `--batch_size` | `int` | `4` | Per-device training batch size |
| `--learning_rate` | `float` | `2e-4` | Learning rate for LoRA training |
| `--lora_r` | `int` | `16` | LoRA rank dimension |
| `--lora_alpha` | `int` | `32` | LoRA scaling factor |
| `--use_4bit` | `flag` | `True` | Enable 4-bit NF4 quantization via `bitsandbytes` |
| `--num_samples` | `int` | `500` | Number of synthetic negotiation samples to generate |

---

## 5. Usage Workflows

### Step 1: Generate Synthetic Dataset Only

```bash
python fine_tune_negotiator.py --mode generate-data --num_samples 500 --output_dir ./data/negotiation_ft
```

Generates:
- `./data/negotiation_ft/llm_moderator_dataset.json` (LLM dialogue samples)
- `./data/negotiation_ft/sentiment_dataset.json` (Annotated sentiment utterances)

### Step 2: Fine-Tune the LLM Moderator (QLoRA SFT)

```bash
python fine_tune_negotiator.py \
  --mode llm \
  --base_model bharatgenai/LegalParam \
  --dataset_path ./data/negotiation_ft/llm_moderator_dataset.json \
  --output_dir ./models/negotiator_lora \
  --epochs 3 \
  --batch_size 2 \
  --learning_rate 2e-4
```

Output:
- Fine-tuned PEFT/LoRA adapter weights saved in `./models/negotiator_lora`

### Step 3: Fine-Tune the Negotiation Sentiment Analyser (RoBERTa)

```bash
python fine_tune_negotiator.py \
  --mode sentiment \
  --sentiment_base cardiffnlp/twitter-roberta-base-sentiment \
  --dataset_path ./data/negotiation_ft/sentiment_dataset.json \
  --output_dir ./models/sentiment_roberta \
  --epochs 4 \
  --batch_size 16 \
  --learning_rate 2e-5
```

Output:
- Fine-tuned 5-class sequence classifier saved in `./models/sentiment_roberta`

### Step 4: Run End-to-End Synthetic Data + Training + Evaluation

```bash
python fine_tune_negotiator.py --mode all --num_samples 500 --epochs 3
```

---

## 6. Hyperparameter Optimization & Technical Details

### QLoRA Target Modules
LoRA is applied to key projection matrices of the base transformer architecture:
- `q_proj`, `k_proj`, `v_proj`, `o_proj` (Attention projections)
- `gate_proj`, `up_proj`, `down_proj` (MLP feed-forward layers)

```python
LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
)
```

### 4-bit Quantization Config (bitsandbytes)

```python
BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True
)
```

---

## 7. Model Integration into `AIML/negotiation_ai.py`

Once fine-tuning is completed:

1. **LLM Moderator**: Point `_build_local_pipe()` or `NegotiationModerator` in [`AIML/negotiation_ai.py`](file:///c:/Users/Lenovo/OneDrive/Desktop/MSME%20Major%20project/AIML/negotiation_ai.py) to load the base model merged with `./models/negotiator_lora` adapters:

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

base_model = AutoModelForCausalLM.from_pretrained("bharatgenai/LegalParam")
model = PeftModel.from_pretrained(base_model, "./models/negotiator_lora")
```

2. **Sentiment Analyser**: Load `./models/sentiment_roberta` inside `NegotiationSentimentAnalyser`:

```python
self.pipe = hf_pipeline(
    "text-classification",
    model="./models/sentiment_roberta",
    device=0 if torch.cuda.is_available() else -1
)
```

---

## 8. Summary Checklist

- [x] Dependencies installed (`peft`, `trl`, `bitsandbytes`, `transformers`)
- [x] Synthetic negotiation data generator configured with MSMED Act 2006 rules
- [x] LLM SFT QLoRA script tested (`fine_tune_negotiator.py`)
- [x] 5-Class RoBERTa sentiment classifier trainer integrated
- [x] Output model directories created (`./models/negotiator_lora`, `./models/sentiment_roberta`)
- [x] Adapter loading verified for `AIML/negotiation_ai.py`
