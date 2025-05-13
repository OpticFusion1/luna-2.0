export type azureTTSSubtitle = {
  audio_offset: number;
  text_offset: number;
  text?: string;
};

export interface FoundWord {
  username: string;
  value: string;
  isRevealed: boolean;
}
