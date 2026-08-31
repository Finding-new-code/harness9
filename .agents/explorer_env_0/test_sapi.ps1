
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$wavPath = "g:\Finding-new-code\harness9\.agents\explorer_env_0\test_sapi.wav"
$synth.SetOutputToWaveFile($wavPath)
$synth.Speak("This is a deterministic voice narration test for Harness 9 pipeline.")
$synth.Dispose()
