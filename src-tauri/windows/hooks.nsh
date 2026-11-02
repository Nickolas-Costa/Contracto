; Migração do Inno Setup (AppId=Contracto): remove a instalação antiga antes de instalar.
; Os dados em %APPDATA%\Contracto não pertencem ao desinstalador e ficam intactos.
!macro NSIS_HOOK_PREINSTALL
  ; Sobra das builds 5.2 em arquivo único (o sidecar agora é a pasta sidecar\): 62 MB órfãos.
  Delete "$INSTDIR\Contracto_sidecar.exe"
  ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Contracto_is1" "UninstallString"
  ${If} $0 != ""
    ExecWait '$0 /VERYSILENT /NORESTART'
    ; o desinstalador do Inno relança uma cópia temporária e sai: espera a chave sumir (até ~30 s)
    StrCpy $2 0
    ${Do}
      ReadRegStr $1 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Contracto_is1" "UninstallString"
      ${If} $1 == ""
      ${OrIf} $2 >= 60
        ${ExitDo}
      ${EndIf}
      Sleep 500
      IntOp $2 $2 + 1
    ${Loop}
  ${EndIf}
!macroend
