export const OPTOUT_KEY = "concept_analytics_optout";
export const SESSION_KEY = "concept_analytics_session_id";
export const HEARTBEAT_MS = 15000;
export const ALLOWED_EVENT_TYPES = [
  "session_start", "page_view", "page_visible_heartbeat",
  "page_hidden", "page_unload", "session_resume",
  "concept_enter_view", "concept_visible_heartbeat", "concept_exit_view",
  "section_opened", "accordion_opened", "tab_selected",
  "case_study_opened", "video_played", "audio_played",
  "interactive_started", "download_clicked",
  "external_link_clicked", "internal_link_clicked", "search_submitted",
];
