import type { ModuleConfig } from "./moduleTypes";

export const moduleConfigs: Record<string, ModuleConfig> = {
  transcription: {
  id: "transcription",
  title: "Transkrypcja audio",
  description:
    "Moduł zamienia nagranie audio na tekst i zapisuje wynik w projekcie.",

  acceptedFileTypes: ["audio-video"],

  parameters: [
    {
      id: "language",
      label: "Język nagrania",
      type: "select",
      required: true,
      defaultValue: "pl",
      options: [
        { label: "Polski", value: "pl" },
        { label: "Angielski", value: "en" },
        { label: "Automatyczne wykrywanie", value: "auto" },
      ],
    },
    {
      id: "beam_size",
      label: "Beam size",
      type: "number",
      defaultValue: 5,
      min: 1,
      max: 10,
    },
    {
      id: "vad_filter",
      label: "Filtr VAD",
      type: "checkbox",
      defaultValue: true,
    },
    {
      id: "word_timestamps",
      label: "Znaczniki czasu dla słów",
      type: "checkbox",
      defaultValue: true,
    },
  ],
    runEndpoint: "/api/modules/transcription/run",
    statusEndpoint: "/api/modules/transcription/status",
  },
  "filter-words": {
    id: "filter-words",
    title: "Filtrowanie słów",
    description:
      "Moduł wyszukuje słowa ze słownika w transkrypcji i zapisuje wyniki w projekcie.",
    acceptedFileTypes: ["transcription-json"],

    parameters: [
      // tutaj dodamy parametry modułu,
    ],

    runEndpoint: "/api/modules/filter-words/run",
    statusEndpoint: "/api/modules/filter-words/status",
  },

  diarization: {
    id: "diarization",
    title: "Rozpoznawanie mówców",
    description:
      "Moduł wykrywa poszczególnych mówców w nagraniu i przypisuje fragmenty wypowiedzi do odpowiednich profili.",

    acceptedFileTypes: ["audio"],

    parameters: [
      {
        id: "profiles",
        label: "Profile osób",
        type: "multiselect",
        required: true,
        defaultValue: [],
        options: [
          { label: "Osoba 1", value: "person-1" },
          { label: "Osoba 2", value: "person-2" },
          { label: "Osoba 3", value: "person-3" },
        ],
      },
      {
        id: "minSpeakers",
        label: "Minimalna liczba mówców",
        type: "number",
        defaultValue: 1,
        min: 1,
        max: 20,
      },
      {
        id: "maxSpeakers",
        label: "Maksymalna liczba mówców",
        type: "number",
        defaultValue: 5,
        min: 1,
        max: 20,
      },
    ],

    runEndpoint: "/api/modules/diarization/run",
    statusEndpoint: "/api/modules/diarization/status",
    resultEndpoint: "/api/modules/diarization/result",
  },

  sceneDetection: {
    id: "scene-detection",
    title: "Detekcja scen",
    description:
      "Moduł analizuje materiał wideo i wykrywa momenty zmiany scen.",

    acceptedFileTypes: ["video"],

    parameters: [
      {
        id: "frameInterval",
        label: "Analiza co ile klatek",
        type: "number",
        defaultValue: 10,
        min: 1,
        max: 1000,
      },
      {
        id: "threshold",
        label: "Próg wykrywania zmiany",
        type: "number",
        defaultValue: 0.5,
        min: 0,
        max: 1,
        step: 0.01,
      },
    ],

    runEndpoint: "/api/modules/scene-detection/run",
    statusEndpoint: "/api/modules/scene-detection/status",
    resultEndpoint: "/api/modules/scene-detection/result",
  },

  subtitles: {
    id: "subtitles",
    title: "Przetwarzanie transkrypcji",
    description:
      "Moduł przyjmuje plik JSON zawierający transkrypcję i generuje plik napisów.",

    acceptedFileTypes: ["transcription-json"],
    requiredFilename: "transkrypcja",

    parameters: [
      {
        id: "format",
        label: "Format wynikowy",
        type: "select",
        defaultValue: "srt",
        options: [
          { label: "SRT", value: "srt" },
          { label: "VTT", value: "vtt" },
        ],
      },
    ],

    runEndpoint: "/api/modules/subtitles/run",
    statusEndpoint: "/api/modules/subtitles/status",
    resultEndpoint: "/api/modules/subtitles/result",
  },
};