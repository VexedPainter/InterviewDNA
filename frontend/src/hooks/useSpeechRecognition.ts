import { useState, useEffect, useRef } from 'react'

export function useSpeechRecognition() {
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [supported, setSupported] = useState(false)
  const recognitionRef = useRef<any>(null)

  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (SpeechRecognition) {
      setSupported(true)
      const instance = new SpeechRecognition()
      instance.continuous = true
      instance.interimResults = true
      instance.lang = 'en-US'

      instance.onresult = (event: any) => {
        let current = ''
        for (let i = 0; i < event.results.length; i++) {
          current += event.results[i][0].transcript
        }
        setTranscript(current)
      }

      instance.onerror = (err: any) => {
        console.warn('Speech recognition error:', err)
        setIsListening(false)
      }

      instance.onend = () => {
        setIsListening(false)
      }

      recognitionRef.current = instance
    }
  }, [])

  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      try {
        setTranscript('')
        recognitionRef.current.start()
        setIsListening(true)
      } catch (e) {
        console.warn(e)
      }
    }
  }

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      try {
        recognitionRef.current.stop()
        setIsListening(false)
      } catch (e) {
        console.warn(e)
      }
    }
  }

  return {
    isListening,
    transcript,
    supported,
    startListening,
    stopListening,
  }
}
