export type RootStackParamList = {
  MainTabs: undefined;
  UploadMusic: undefined;
  TranscriptEditor: { musicId: string };
  NewReel: { presetMusicId?: string };
  JobDetail: { jobId: string };
};

export type TabsParamList = {
  Home: undefined;
  Music: undefined;
  Edits: undefined;
  Settings: undefined;
};
