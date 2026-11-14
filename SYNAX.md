# SYNAX.md — SYNAX Code ajanının proje hafızası

`synax code` bu dosyayı her oturumda sistem istemine ekler. Kısa ve güncel tutun.

- Dil kaynakları: `src/synax/` (lexer, parser, type_system, interpreter, backends/). CLI: `synax_cli.py`.
- `.sx` örnekleri: `examples/`. Kontrol: `./synax check <dosya.sx>`, çalıştırma: `./synax run <dosya.sx>`.
- Tek test dosyası çalıştırma: `python3 tests/<test_dosyası>.py`. Tüm paket: `./synax test`.
- VS Code eklentisi: `editors/vscode-synax/`; paket: `python3 scripts/build_vsix.py`.
- Klinik/biyomedikal çıktılar araştırma amaçlıdır; tıbbi doğruluk iddiası eklemeyin (`MEDICAL_RESEARCH_DISCLAIMER.md`).
