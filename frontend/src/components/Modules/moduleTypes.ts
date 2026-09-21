export type ModuleFileType =
  | "audio"
  | "video"
  | "audio-video"
  | "transcription-json"
  | "any";

export interface ModuleParameterOption {
  label: string;
  value: string;
}

export type ModuleParameterType =
  | "text"
  | "number"
  | "select"
  | "checkbox"
  | "multiselect"
  | "file";

export interface ModuleParameter {
  id: string;
  label: string;
  type: ModuleParameterType;
  description?: string;
  required?: boolean;
  defaultValue?: string | number | boolean | string[];
  min?: number;
  max?: number;
  step?: number;
  options?: ModuleParameterOption[];
}

export interface ModuleConfig {
  id: string;
  title: string;
  description: string;

  acceptedFileTypes: ModuleFileType[];

  /**
   * Opcjonalne ograniczenie nazwy pliku.
   * Przykład: "transkrypcja"
   */
  requiredFilename?: string;

  parameters?: ModuleParameter[];

  runEndpoint: string;
  statusEndpoint?: string;
  resultEndpoint?: string;
}

export interface ProjectFile {
  name: string;
  size: number;
  type: string;
  source?: string;
}

export interface ModuleResultFile {
  name: string;
  size: number;
  type: string;
  source?: string;
}

export interface ModuleResult {
  status: "pending" | "running" | "completed" | "failed";
  progress: number;
  message?: string;
  outputFiles?: ModuleResultFile[];
}