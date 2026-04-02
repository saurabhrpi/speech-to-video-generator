import { useState, useRef, useCallback } from 'react';
import { Audio } from 'expo-av';

interface UseRecordingResult {
  isRecording: boolean;
  metering: number;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<{ uri: string } | null>;
}

export function useRecording(): UseRecordingResult {
  const [isRecording, setIsRecording] = useState(false);
  const [metering, setMetering] = useState(-160);
  const recordingRef = useRef<Audio.Recording | null>(null);

  const startRecording = useCallback(async () => {
    const { status } = await Audio.requestPermissionsAsync();
    if (status !== 'granted') return;

    await Audio.setAudioModeAsync({
      allowsRecordingIOS: true,
      playsInSilentModeIOS: true,
    });

    const recording = new Audio.Recording();
    await recording.prepareToRecordAsync({
      ...Audio.RecordingOptionsPresets.HIGH_QUALITY,
      isMeteringEnabled: true,
    });

    recording.setOnRecordingStatusUpdate((status) => {
      if (status.metering !== undefined) {
        setMetering(status.metering);
      }
    });

    await recording.startAsync();
    recordingRef.current = recording;
    setIsRecording(true);
  }, []);

  const stopRecording = useCallback(async () => {
    const recording = recordingRef.current;
    if (!recording) return null;

    setIsRecording(false);
    setMetering(-160);

    await recording.stopAndUnloadAsync();
    await Audio.setAudioModeAsync({ allowsRecordingIOS: false });

    const uri = recording.getURI();
    recordingRef.current = null;

    return uri ? { uri } : null;
  }, []);

  return { isRecording, metering, startRecording, stopRecording };
}
