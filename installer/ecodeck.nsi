; Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
Unicode true
ManifestDPIAware true
RequestExecutionLevel user
SetCompressor /SOLID lzma
!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"
!include "Sections.nsh"
!include "x64.nsh"

Name "CrashSounds"
OutFile "${OUTPUT_DIR}\CrashSounds-${APP_VERSION}-setup.exe"
InstallDir "$LOCALAPPDATA\Programs\CrashSounds"
InstallDirRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\EcoDeck" "InstallLocation"
BrandingText "CrashSounds - Copyright (c) 2026 Murilo Siqueira Toledo"
VIProductVersion "${APP_VERSION}.0"
VIAddVersionKey /LANG=1046 "ProductName" "CrashSounds"
VIAddVersionKey /LANG=1046 "FileDescription" "Instalador do CrashSounds"
VIAddVersionKey /LANG=1046 "FileVersion" "${APP_VERSION}"
VIAddVersionKey /LANG=1046 "LegalCopyright" "Copyright (c) 2026 Murilo Siqueira Toledo. Licença MIT."

!define MUI_ICON "${REPO_DIR}\assets\CrashSounds.ico"
!define MUI_UNICON "${REPO_DIR}\assets\CrashSounds.ico"
!define MUI_WELCOMEPAGE_TITLE "CrashSounds: seu som, na hora certa."
!define MUI_WELCOMEPAGE_TEXT "Soundboard gratuito e open source para Windows.$\r$\n$\r$\nInstalação apenas para sua conta, sem pedir administrador.$\r$\n$\r$\nCopyright (c) 2026 Murilo Siqueira Toledo. Licença MIT."
!define MUI_COMPONENTSPAGE_TEXT_TOP "Escolha os atalhos e se deseja iniciar com o Windows. O áudio só será ativado por você dentro do app."
!define MUI_FINISHPAGE_TEXT "O CrashSounds está pronto. Abra pelo Menu Iniciar ou pelo atalho da Área de Trabalho, se selecionado.$\r$\n$\r$\nA biblioteca pessoal é preservada nas atualizações e na desinstalação."
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${REPO_DIR}\LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "PortugueseBR"

Var QAMode
!define UNINSTALL_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\EcoDeck"
!define RUN_KEY "Software\Microsoft\Windows\CurrentVersion\Run"

Section "CrashSounds (obrigatório)" SEC_CORE
  SectionIn RO
  SetShellVarContext current
  SetOutPath "$INSTDIR"
  File /r "${PACKAGE_DIR}\*.*"
  WriteUninstaller "$INSTDIR\Desinstalar.exe"
  ${If} $QAMode == "1"
    FileOpen $0 "$INSTDIR\.ecodeck-installer-qa" w
    FileClose $0
  ${Else}
    ; Só retirar legados quando a instalação registrada corresponde a esta pasta.
    ReadRegStr $2 HKCU "${UNINSTALL_KEY}" "InstallLocation"
    ${If} $2 == $INSTDIR
      Delete "$INSTDIR\EcoDeck.exe"
      Delete "$INSTDIR\assets\EcoDeck.ico"
      Delete "$DESKTOP\EcoDeck.lnk"
      Delete "$SMPROGRAMS\EcoDeck\EcoDeck.lnk"
      Delete "$SMPROGRAMS\EcoDeck\Desinstalar EcoDeck.lnk"
      RMDir "$SMPROGRAMS\EcoDeck"
      ReadRegStr $0 HKCU "${RUN_KEY}" "EcoDeck"
      ${If} $0 == '$\"$INSTDIR\EcoDeck.exe$\" --minimized'
        DeleteRegValue HKCU "${RUN_KEY}" "EcoDeck"
      ${EndIf}
    ${EndIf}
    WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayName" "CrashSounds"
    WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKCU "${UNINSTALL_KEY}" "Publisher" "Murilo Siqueira Toledo"
    WriteRegStr HKCU "${UNINSTALL_KEY}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayIcon" "$INSTDIR\assets\CrashSounds.ico"
    WriteRegStr HKCU "${UNINSTALL_KEY}" "UninstallString" '$\"$INSTDIR\Desinstalar.exe$\"'
    WriteRegStr HKCU "${UNINSTALL_KEY}" "QuietUninstallString" '$\"$INSTDIR\Desinstalar.exe$\" /S'
    WriteRegStr HKCU "${UNINSTALL_KEY}" "URLInfoAbout" "https://github.com/Toled0o/CrashSounds"
    WriteRegDWORD HKCU "${UNINSTALL_KEY}" "NoModify" 1
    WriteRegDWORD HKCU "${UNINSTALL_KEY}" "NoRepair" 1
    CreateDirectory "$SMPROGRAMS\CrashSounds"
    CreateShortcut "$SMPROGRAMS\CrashSounds\CrashSounds.lnk" "$INSTDIR\CrashSounds.exe" "" "$INSTDIR\assets\CrashSounds.ico"
    CreateShortcut "$SMPROGRAMS\CrashSounds\Desinstalar CrashSounds.lnk" "$INSTDIR\Desinstalar.exe"
    ; Retirar apenas a entrada desta instalação antes de aplicar a opção escolhida.
    ReadRegStr $0 HKCU "${RUN_KEY}" "CrashSounds"
    ${If} $0 == '$\"$INSTDIR\CrashSounds.exe$\" --minimized'
      DeleteRegValue HKCU "${RUN_KEY}" "CrashSounds"
    ${EndIf}
  ${EndIf}
SectionEnd

Section "Criar atalho na área de trabalho" SEC_DESKTOP
  ${If} $QAMode != "1"
    CreateShortcut "$DESKTOP\CrashSounds.lnk" "$INSTDIR\CrashSounds.exe" "" "$INSTDIR\assets\CrashSounds.ico"
  ${EndIf}
SectionEnd

Section /o "Iniciar com o Windows" SEC_STARTUP
  ${If} $QAMode != "1"
    WriteRegStr HKCU "${RUN_KEY}" "CrashSounds" '$\"$INSTDIR\CrashSounds.exe$\" --minimized'
  ${EndIf}
SectionEnd

Function .onInit
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "O CrashSounds requer Windows x64."
    Abort
  ${EndIf}
  SetRegView 64
  SetShellVarContext current
  StrCpy $QAMode "0"
  ${GetParameters} $0
  ClearErrors
  ${GetOptions} $0 "/QA" $1
  ${IfNot} ${Errors}
    StrCpy $QAMode "1"
  ${EndIf}
  ${If} $QAMode == "1"
    ; QA nunca pode cair na pasta padrão se /D tiver formato incorreto.
    ReadEnvStr $INSTDIR "ECODECK_INSTALLER_QA_DIR"
    ${If} $INSTDIR == ""
      SetErrorLevel 2
      Quit
    ${EndIf}
  ${EndIf}
  ${If} $QAMode != "1"
    ReadRegStr $0 HKCU "${RUN_KEY}" "CrashSounds"
    ${If} $0 == '$\"$INSTDIR\CrashSounds.exe$\" --minimized'
      !insertmacro SelectSection ${SEC_STARTUP}
    ${EndIf}
    ReadRegStr $0 HKCU "${RUN_KEY}" "EcoDeck"
    ${If} $0 == '$\"$INSTDIR\EcoDeck.exe$\" --minimized'
      !insertmacro SelectSection ${SEC_STARTUP}
    ${EndIf}
  ${EndIf}
FunctionEnd

Function un.onInit
  SetRegView 64
  SetShellVarContext current
  StrCpy $QAMode "0"
  IfFileExists "$INSTDIR\.ecodeck-installer-qa" 0 +2
    StrCpy $QAMode "1"
FunctionEnd

Section "Uninstall"
  ${If} $QAMode != "1"
    ReadRegStr $0 HKCU "${RUN_KEY}" "CrashSounds"
    ${If} $0 == '$\"$INSTDIR\CrashSounds.exe$\" --minimized'
      DeleteRegValue HKCU "${RUN_KEY}" "CrashSounds"
    ${EndIf}
    ReadRegStr $0 HKCU "${UNINSTALL_KEY}" "InstallLocation"
    ${If} $0 == $INSTDIR
      DeleteRegKey HKCU "${UNINSTALL_KEY}"
    ${EndIf}
    Delete "$DESKTOP\CrashSounds.lnk"
    Delete "$SMPROGRAMS\CrashSounds\CrashSounds.lnk"
    Delete "$SMPROGRAMS\CrashSounds\Desinstalar CrashSounds.lnk"
    RMDir "$SMPROGRAMS\CrashSounds"
  ${EndIf}
  ; Lista explícita gerada no build. Nunca apagar a pasta de forma recursiva.
  !include "${UNINSTALL_INCLUDE}"
  Delete "$INSTDIR\.ecodeck-installer-qa"
  Delete "$INSTDIR\Desinstalar.exe"
  RMDir "$INSTDIR"
  ; Não remover %LOCALAPPDATA%\EcoDeck: sons e preferências pertencem ao usuário.
SectionEnd
