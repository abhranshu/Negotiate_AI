"""
Translation Service — IndicTrans2 (AI4Bharat)
=============================================
Wraps ai4bharat/indictrans2-en-indic-dist-200M for:
  - English → Indic  (for settlement output to user's language)
  - Indic  → English (for processing user voice/text input)

Used by:
  - voice_pipeline.py   → translate Hindi/regional input to English
  - settlement_generator.py → translate settlement to user's language

Install:
    pip install git+https://github.com/AI4Bharat/IndicTransToolkit.git
    pip install transformers torch sentencepiece

Supported language codes (ISO 639):
    hi=Hindi, ta=Tamil, te=Telugu, bn=Bengali, mr=Marathi,
    kn=Kannada, ml=Malayalam, gu=Gujarati, pa=Punjabi, or=Odia
"""

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

# ─── Language code maps ──────────────────────────────────────────────────────

# Map ISO 639-1 (whisper/spaCy standard) → IndicTrans2 script codes
ISO_TO_INDICTRANS = {
    "hi": "hin_Deva",
    "ta": "tam_Taml",
    "te": "tel_Telu",
    "bn": "ben_Beng",
    "mr": "mar_Deva",
    "kn": "kan_Knda",
    "ml": "mal_Mlym",
    "gu": "guj_Gujr",
    "pa": "pan_Guru",
    "or": "ory_Orya",
    "as": "asm_Beng",
    "en": "eng_Latn",
}

EN_INDIC_MODEL = "ai4bharat/indictrans2-en-indic-dist-200M"
INDIC_EN_MODEL = "ai4bharat/indictrans2-indic-en-dist-200M"


# ─── Translator class ────────────────────────────────────────────────────────

class IndicTranslator:
    """
    Bidirectional English ↔ Indian language translator using IndicTrans2.

    Usage:
        translator = IndicTranslator()

        # Indic → English (for processing user input)
        en_text = translator.to_english("मेरा भुगतान नहीं हुआ", src_lang="hi")

        # English → Indic (for sending settlement to user)
        hi_text = translator.from_english("Your case has been settled.", tgt_lang="hi")
    """

    def __init__(self, device: str = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._en_indic_loaded = False
        self._indic_en_loaded = False

        # Lazy load — models are loaded only when first used
        self._en_indic_tokenizer = None
        self._en_indic_model     = None
        self._indic_en_tokenizer = None
        self._indic_en_model     = None
        self._ip                 = None  # IndicProcessor

    def _load_processor(self):
        if self._ip is None:
            try:
                from IndicTransToolkit.processor import IndicProcessor
                self._ip = IndicProcessor(inference=True)
            except ImportError:
                raise ImportError(
                    "IndicTransToolkit not installed.\n"
                    "Run: pip install git+https://github.com/AI4Bharat/IndicTransToolkit.git"
                )

    def _load_en_indic(self):
        if not self._en_indic_loaded:
            print(f"[Translator] Loading EN→Indic model ({EN_INDIC_MODEL})...")
            self._en_indic_tokenizer = AutoTokenizer.from_pretrained(
                EN_INDIC_MODEL, trust_remote_code=True
            )
            self._en_indic_model = AutoModelForSeq2SeqLM.from_pretrained(
                EN_INDIC_MODEL,
                trust_remote_code=True,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            ).to(self.device)
            self._en_indic_model.eval()
            self._en_indic_loaded = True

    def _load_indic_en(self):
        if not self._indic_en_loaded:
            print(f"[Translator] Loading Indic→EN model ({INDIC_EN_MODEL})...")
            self._indic_en_tokenizer = AutoTokenizer.from_pretrained(
                INDIC_EN_MODEL, trust_remote_code=True
            )
            self._indic_en_model = AutoModelForSeq2SeqLM.from_pretrained(
                INDIC_EN_MODEL,
                trust_remote_code=True,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            ).to(self.device)
            self._indic_en_model.eval()
            self._indic_en_loaded = True

    def _get_indictrans_code(self, iso_code: str) -> str:
        code = ISO_TO_INDICTRANS.get(iso_code)
        if not code:
            raise ValueError(
                f"Unsupported language '{iso_code}'. "
                f"Supported: {list(ISO_TO_INDICTRANS.keys())}"
            )
        return code

    def _translate(
        self,
        sentences: list[str],
        src_lang: str,
        tgt_lang: str,
        tokenizer,
        model,
    ) -> list[str]:
        self._load_processor()

        batch = self._ip.preprocess_batch(
            sentences, src_lang=src_lang, tgt_lang=tgt_lang
        )
        inputs = tokenizer(
            batch,
            truncation=True,
            padding="longest",
            return_tensors="pt",
            return_attention_mask=True,
        ).to(self.device)

        with torch.no_grad():
            generated_tokens = model.generate(
                **inputs,
                use_cache=True,
                min_length=0,
                max_length=256,
                num_beams=5,
                num_return_sequences=1,
            )

        decoded = tokenizer.batch_decode(
            generated_tokens,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True,
        )
        return self._ip.postprocess_batch(decoded, lang=tgt_lang)

    # ── Public API ────────────────────────────────────────────────────────────

    def to_english(self, text: str, src_lang: str) -> str:
        """
        Translate Indic language text → English.
        Args:
            text     : Input text in an Indian language
            src_lang : ISO 639-1 code (e.g. 'hi', 'ta', 'bn')
        Returns:
            Translated English string
        """
        if src_lang == "en":
            return text
        self._load_indic_en()
        src = self._get_indictrans_code(src_lang)
        results = self._translate(
            [text], src, "eng_Latn",
            self._indic_en_tokenizer, self._indic_en_model
        )
        return results[0]

    def from_english(self, text: str, tgt_lang: str) -> str:
        """
        Translate English text → Indian language.
        Args:
            text     : Input English text
            tgt_lang : ISO 639-1 code (e.g. 'hi', 'ta', 'bn')
        Returns:
            Translated string in target language
        """
        if tgt_lang == "en":
            return text
        self._load_en_indic()
        tgt = self._get_indictrans_code(tgt_lang)
        results = self._translate(
            [text], "eng_Latn", tgt,
            self._en_indic_tokenizer, self._en_indic_model
        )
        return results[0]

    def batch_to_english(self, texts: list[str], src_lang: str) -> list[str]:
        """Batch translate multiple Indic sentences → English."""
        if src_lang == "en":
            return texts
        self._load_indic_en()
        src = self._get_indictrans_code(src_lang)
        return self._translate(
            texts, src, "eng_Latn",
            self._indic_en_tokenizer, self._indic_en_model
        )

    def batch_from_english(self, texts: list[str], tgt_lang: str) -> list[str]:
        """Batch translate multiple English sentences → Indic language."""
        if tgt_lang == "en":
            return texts
        self._load_en_indic()
        tgt = self._get_indictrans_code(tgt_lang)
        return self._translate(
            texts, "eng_Latn", tgt,
            self._en_indic_tokenizer, self._en_indic_model
        )


# ─── Singleton (shared across modules) ──────────────────────────────────────

_translator_instance: IndicTranslator | None = None


def get_translator() -> IndicTranslator:
    """Returns a shared IndicTranslator instance (lazy-loaded)."""
    global _translator_instance
    if _translator_instance is None:
        _translator_instance = IndicTranslator()
    return _translator_instance


# ─── Quick test ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    translator = IndicTranslator()

    samples = [
        ("मेरा भुगतान नहीं हुआ। 4 लाख रुपये बकाया है।", "hi"),
        ("என் பணம் திரும்ப வரவில்லை.", "ta"),
    ]

    print("=== Indic → English ===")
    for text, lang in samples:
        en = translator.to_english(text, src_lang=lang)
        print(f"  [{lang}] {text}")
        print(f"  [en]   {en}\n")

    print("=== English → Hindi ===")
    en_text = "Your dispute has been successfully resolved. Payment of INR 4,00,000 will be made within 30 days."
    hi = translator.from_english(en_text, tgt_lang="hi")
    print(f"  [en] {en_text}")
    print(f"  [hi] {hi}")
