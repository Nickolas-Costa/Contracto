"""Camada de ports: interfaces p/ desacoplar backend da UI atual (Tk).

Fase A (pywebview) e Fase B (Tauri V2) implementam estes ports sem tocar
em services/. Hoje as implementações default delegam ao comportamento
Windows/Tk existente.
"""
