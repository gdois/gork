from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


def translate_to_pt(text: str, src_lang: str = "eng_Latn") -> str:
    model_name = "facebook/nllb-200-distilled-1.3B"

    tokenizer = AutoTokenizer.from_pretrained(model_name, src_lang=src_lang)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    inputs = tokenizer(text, return_tensors="pt")

    tgt_lang = "por_Latn"
    forced_bos_token_id = tokenizer.convert_tokens_to_ids(tgt_lang)

    generated = model.generate(
        **inputs,
        forced_bos_token_id=forced_bos_token_id,
        max_length=512
    )

    return tokenizer.decode(generated[0], skip_special_tokens=True)