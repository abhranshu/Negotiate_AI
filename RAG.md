Done — RAG is wired in and verified. Here's the summary:

What changed in  AIML/negotiation_ai.py 

1.  NegotiationModerator.__init__  — added a  use_rag: bool = True  flag (you can disable with  NegotiationModerator(use_rag=False) ), with a lazily-built  LegalRetriever .
2.  _get_law_context(state, last_message)  — builds a query from the case fields (dispute type, overdue days, industry) plus the latest message, retrieves top-3 provisions, and returns them formatted. Fails silently (empty string) if RAG is unavailable — negotiation never breaks.
3.  _build_prompt  — injects a  === RELEVANT LAW (retrieved from legal corpus) ===  block, and the task instruction now says: "Cite the retrieved legal provisions by section number when they apply; never invent provisions that are not in the RELEVANT LAW block."

Verified: prompt builds with the law block, Section 16 retrieved for an interest query, single header, correct section order, anti-hallucination instruction present. Both the Groq and local-HF generation paths use  _build_prompt , so they both get RAG.

⚠️ Note: the rule-based fallback ( generate_response_sync ) doesn't use the LLM prompt, so RAG only visibly matters when an actual LLM generates responses — i.e. set  GROQ_API_KEY  in  .env  or use  use_local_hf=True .

Yes — your remaining work is the data

The plumbing is done. To make it real, you need to:
1. Get the legal text — MSMED Act 2006 Sections 15–23, relevant Indian Contract Act sections, and a few MSEFC conciliation orders → save as  .txt / .md  files in  data/legal/  (delete the placeholder  README.txt  first).
2. Install the vector stack (better retrieval than keyword fallback):
// bash
pip install chromadb sentence-transformers
3. Rebuild the index:
// bash
python -m AIML.legal_rag --build
4. Test it: run a negotiation message and check the moderator cites actual section numbers.





📋 Full guide after downloading the model

1. Download the model (from your machine — it caches to  ~/.cache/huggingface/hub/models--bharatgenai--LegalParam ):

// python
from transformers import AutoModelForCausalLM, AutoTokenizer
AutoModelForCausalLM.from_pretrained("bharatgenai/LegalParam", trust_remote_code=True)
AutoTokenizer.from_pretrained("bharatgenai/LegalParam", trust_remote_code=True)

Check it's complete:  ~/.cache/huggingface/hub/models--bharatgenai--LegalParam/snapshots/*  should have all  .safetensors  shards (~11.4GB).

2. Load legal data into RAG (required for the RELEVANT LAW block to have content):

// bash
pip install chromadb sentence-transformers   # vector backend (better)
# put MSMED Act S15–23 + Contract Act text into data/legal/*.txt (delete placeholder README.txt)
python -m AIML.legal_rag --build

3. Enable the model in your app:

// bash
# .env
USE_LOCAL_MODEL=true

4. Test the full chain (expect slow on CPU — minutes to load, tens of seconds per reply):

// bash
uvicorn api.main:app --reload --port 8000
# create a case, then send a negotiation message — mediator should now be LLM-generated
# and cite sections from the RELEVANT LAW block

5. Deploy (AWS) — don't run the fp32 CPU path there. It needs ~11GB RAM and is too slow. For production:
- Serve 4-bit quantized LegalParam with vLLM on a g4dn.xlarge spot (~$0.15–0.20/hr), or
- Skip self-hosting: set  USE_LOCAL_MODEL=false  +  GROQ_API_KEY  — free tier, already wired.

6. (Optional) Fine-tune with QLoRA on ~500 curated dialogues — 1–3 hrs on your 6GB 3050, ~20MB adapter saved, loaded via PEFT.






Straight answer: the download command was there but too minimal, and I never gave you a dedicated test command for the model itself — my guide only had the app-level test. Let me fix that properly now.

Complete download + test commands

Step 1 — Download (use the CLI, it's cleaner and resumable):

// bash
pip install -U "huggingface_hub[cli]"
huggingface-cli download bharatgenai/LegalParam

This saves to  ~/.cache/huggingface/hub/models--bharatgenai--LegalParam/  — which is exactly where your code ( pipeline(model="bharatgenai/LegalParam") ) already looks, so no code changes needed for the download location. Verify it finished:

// bash
du -sh ~/.cache/huggingface/hub/models--bharatgenai--LegalParam   # expect ~11.4GB

Step 2 — Test the raw model loads:

// bash
python -c "from transformers import AutoModelForCausalLM, AutoTokenizer; AutoModelForCausalLM.from_pretrained('bharatgenai/LegalParam', trust_remote_code=True); AutoTokenizer.from_pretrained('bharatgenai/LegalParam', trust_remote_code=True); print('MODEL LOADED OK')"

⚠️ This takes minutes on CPU and ~11GB RAM. If it OOMs, that's a machine-limit, not a code bug.

Step 3 — Test the model actually answers (the model-card format, exactly what the fix uses):

// bash
python - <<'EOF'
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
tok = AutoTokenizer.from_pretrained("bharatgenai/LegalParam", trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained("bharatgenai/LegalParam",
    trust_remote_code=True, torch_dtype=torch.float32, device_map="cpu")
prompt = "<user>\nWhat is the interest rate under Section 16 of the MSMED Act?<assistant>\n"
inputs = tok(prompt, return_tensors="pt")
with torch.no_grad():
    out = model.generate(**inputs, max_new_tokens=200, do_sample=True,
                         top_k=50, top_p=0.95, temperature=0.6,
                         eos_token_id=tok.eos_token_id)
print(tok.decode(out[0], skip_special_tokens=True))
EOF

If this returns a coherent answer → the model + format are fixed. If it's still nonsense → the problem is elsewhere (e.g. the custom architecture needs a specific transformers version), and we'd debug from here.

Step 4 — Test the full app chain (as in the guide):

// bash
# .env: USE_LOCAL_MODEL=true
python -m AIML.legal_rag --build    # after adding law text to data/legal/
uvicorn api.main:app --reload --port 8000

────────────────────────────────────────────────────────────────────────────────

Everything I changed this session

Security
1.  api/config.py  — removed all hardcoded credentials (Supabase DB password/URL, Supabase keys, JWT secret); everything now reads from env with safe non-secret defaults (SQLite default DB, fake dev JWT secret); added  SUPABASE_SECRET_KEY ,  SUPABASE_JWKS_URL ,  GROQ_API_KEY ,  USE_LOCAL_MODEL  fields; switched to modern  SettingsConfigDict .
2.  .env.example  — created (was gitignored, never existed) with placeholder values.
3.  .gitignore  — un-ignored  .env.example  so the template is commit-able. (⚠️ Real credentials are still in git history — rotate them.)

RAG (new)
4.  AIML/legal_rag.py  — created:  LegalRetriever  with ChromaDB + multilingual embeddings (primary) and pure-stdlib TF-IDF keyword fallback; section-aware chunking; case-aware query builder; prompt formatting with anti-hallucination instruction;  --build / --query  CLI; keyword-corpus persistence across processes.
5.  data/legal/README.txt  — placeholder corpus showing the format (replace with real MSMED Act text).

Moderator wiring (AIML/negotiation_ai.py)
6. Added  use_rag  flag + lazy  LegalRetriever ; new  _get_law_context() ; injected  === RELEVANT LAW ===  block into  _build_prompt  + "never invent provisions" instruction.
7. Fixed the nonsense-output bug: prompts now wrapped in  <user>\n...<assistant>\n  (LegalParam's required format), generation params corrected to the model card values ( temperature=0.6, top_k=50, top_p=0.95, max_new_tokens=300 ), leftover  <assistant>  tokens stripped.
8.  NegotiationSession  now accepts and forwards  use_local_hf  /  use_api  /  use_rag .

API wiring
9.  api/routes/negotiate.py  — reads  USE_LOCAL_MODEL  /  USE_EXTERNAL_LLM  from settings and enables the local model when set (previously the API could never use it).

Verified along the way: all files compile; RAG build/retrieve/format tested (keyword backend); prompt injection tested; local-model path tested with mocks (format + params + wiring all confirmed). Not tested: the real model output — needs the 11.4GB download (only 15GB free disk here).

Want me to kick off the actual download + raw-model test now? It'll take a while on this connection and disk is tight (15GB free vs 11.4GB needed), but I can start it and monitor.














Short answer:  data/legal/  at your project root — on your machine that's exactly:

C:\Users\Lenovo\OneDrive\Desktop\MSME Major project\data\legal\

That folder already exists (it has my placeholder  README.txt  in it). Here's how to use it properly.

What goes in, what doesn't

┌────────────────────────────────────┬───────────────────────────────────────────────────────────────────┐
│ ✅ Put here                        │ ❌ Don't put here                                                 │
├────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
│ .txt or .md files (plain text)     │ PDFs, images, Word docs — must convert to text first              │
│ MSMED Act 2006 Sections 15–23      │ Anything in data/chroma/ (that's the auto-built index — never     │
│                                    │ touch it)                                                         │
│ Indian Contract Act relevant       │ Files in data/ root, uploads/, or anywhere else                   │
│ sections                           │                                                                   │
│ MSEFC conciliation orders (text)   │ —                                                                 │
└────────────────────────────────────┴───────────────────────────────────────────────────────────────────┘

The code only reads  *.txt  and  *.md , UTF-8 encoded, one act per file is fine.

Formatting that makes RAG work best

1. Keep  Section N.  at the start of a paragraph. The chunker detects it to tag each chunk with its section (that's the  [msmed_act.txt | Section 16]  citation you saw). So write it as:
Section 16. Date from which and rate at which interest is payable.
 
Where any buyer fails to make payment of the amount to the supplier, as
required under section 15, the buyer shall ... be liable to pay compound
interest with monthly rests ...
2. Separate sections with blank lines — each becomes a chunk boundary.
3. Name files meaningfully — the filename is shown in citations ( [msmed_act.txt | Section 17] ). Good names:  msmed_act.txt ,  indian_contract_act.txt ,  msefc_order_001.txt .
4. Delete my placeholder  README.txt  first (or it'll be indexed too — harmless, but noisy).
5. ~600 chars per chunk is automatic — long sections get split into multiple overlapping chunks; each remembers its section. No manual chunking needed.

Converting PDFs to text (if your source is PDF)

// bash
# quickest for scanned/text PDFs — or reuse your own document_intelligence module
pip install pypdf
python -c "from pypdf import PdfReader; r=PdfReader('msmed_act.pdf'); open('data/legal/msmed_act.txt','w',encoding='utf-8').write('\n\n'.join(p.extract_text() or '' for p in r.pages))"

Then rebuild

// bash
pip install chromadb sentence-transformers   # once — enables the vector backend
python -m AIML.legal_rag --build
python -m AIML.legal_rag --query "compound interest section 16"   # sanity check

After that, the moderator pulls from this corpus automatically — no other wiring needed.

Where to get the actual text: MSMED Act →  indiacode.nic.in/handle/123456789/1556  (copy-paste Sections 15–23); Contract Act →  indiacode.nic.in ; conciliation orders →  samadhaan.msme.gov.in  (anonymize party names first). All public, no RTI needed for the Act text itself.