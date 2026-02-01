export interface OverlaySettings {
  fontSize: number;
  fontFamily: string;
  textColor: string;
  backgroundColor: string;
  position: 'top' | 'bottom';
  maxLines: number;
}

export interface SourceInfo {
  id: string;
  name: string;
  thumbnail: string;
  appIcon: string | null;
}

export type CaptureState = 'idle' | 'connecting' | 'capturing' | 'error';

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected';

export interface WhisperSegment {
  id: number;
  text: string;
  start?: number;
  end?: number;
}

export interface WhisperMessage {
  message?: string;
  status?: string;
  segments?: WhisperSegment[];
  text?: string;
}
