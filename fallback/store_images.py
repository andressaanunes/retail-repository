"""Fallback hardcoded de URLs de imagens por categoria.
Usado apenas quando a tabela public.store_images do Supabase
esta indisponivel ou vazia."""

STORE_IMAGES_FALLBACK = {
    "drive-thru": [
        "https://gemini.google.com/share/16778a86984b",
        "https://gemini.google.com/share/dbfec4c8b29c",
        "https://gemini.google.com/share/db143da05c8a",
        "https://gemini.google.com/share/806ced321cce",
        "https://gemini.google.com/share/a15a010ec4dd",
    ],
    "flagship": [
        "https://gemini.google.com/share/770ccdf94762",
        "https://gemini.google.com/share/dc1bb374ff07",
        "https://gemini.google.com/share/a3f443263674",
        "https://gemini.google.com/share/28d429a3ec66",
        "https://gemini.google.com/share/4dfbf4cffcf9",
    ],
    "quiosque": [
        "https://gemini.google.com/share/ae8e5f882ce3",
        "https://gemini.google.com/share/1af23442a446",
        "https://gemini.google.com/share/8d39e719fd64",
        "https://gemini.google.com/share/a27cfbfa7ea5",
        "https://gemini.google.com/share/9cc191a1a252",
    ],
    "core": [
        "https://gemini.google.com/share/54113c782257",
        "https://gemini.google.com/share/e2fa61508eaf",
        "https://gemini.google.com/share/578fa5f552b4",
        "https://gemini.google.com/share/77286e4aca24",
        "https://gemini.google.com/share/d418e2945e7f",
    ],
}
