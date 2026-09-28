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

  "censor-transcription": {
    id: "censor-transcription",
    title: "Cenzurowanie transkrypcji",
    description:
      "Zamienia wykryte przekleństwa w transkrypcji na gwiazdki.",
    acceptedFileTypes: ["transcription-json"],
    parameters: [
      {
        id: "detected_words_file",
        label: "Plik z wykrytymi słowami",
        type: "file",
        required: true,
      },
    ],
    runEndpoint: "/api/modules/censor-transcription/run",
    statusEndpoint: "/api/modules/censor-transcription/status",
  },

  "subtitles": {
    id: "add-subtitles",

    title: "Dodawanie napisów",

    description:
      "Moduł pozwala dodać napisy na podstawie transkrypcji i wtopić je bezpośrednio w plik video.",

    acceptedFileTypes: ["video"],

    parameters: [
      {
        id: "transcription_file",
        label: "Plik transkrypcji",
        type: "file",
        required: true,
      },
      {
        id: "font_size",
        label: "Wielkość czcionki",
        type: "number",
        required: true,
        defaultValue: 24,
        min: 8,
        max: 72,
        step: 1,
      },
      {
        id: "font_color",
        label: "Kolor napisów",
        type: "text",
        required: true,
        defaultValue: "#FFFFFF",
      },
    ],

    runEndpoint: "/api/modules/add-subtitles/run",
    statusEndpoint: "/api/modules/add-subtitles/status",
  },
  "mute-detected-words": {
    id: "mute-detected-words",

    title: "Wycisz wykryte słowa",

    description:
      "Moduł automatycznie wycisza fragmenty audio odpowiadające słowom wykrytym przez słownik.",

    acceptedFileTypes: ["video"],

    parameters: [
      {
        id: "detected_words_file",
        label: "Plik wykrytych słów",
        type: "file",
        required: true,
      },
    ],

    runEndpoint: "/api/modules/mute-detected-words/run",
    statusEndpoint: "/api/modules/mute-detected-words/status",
  },
  "split-media": {
    id: "split-media",
    title: "Rozdziel audio i video",
    description:
      "Moduł rozdziela wskazany plik video na osobny plik video oraz osobny plik audio.",
    acceptedFileTypes: ["video"],
    parameters: [],
    runEndpoint: "/api/modules/split-media/run",
    statusEndpoint: "/api/modules/split-media/status",
  },
  "merge-media": {
    id: "merge-media",
    title: "Połącz video i audio",
    description:
      "Moduł łączy wskazany plik video i plik audio w jeden plik multimedialny.",
    acceptedFileTypes: ["video"],
    parameters: [
      {
        id: "audio_file",
        label: "Plik audio",
        type: "file",
        required: true,
      },
    ],
    runEndpoint: "/api/modules/merge-media/run",
    statusEndpoint: "/api/modules/merge-media/status",
  },

  "face-blur": {
    id: "face-blur",
    title: "Rozpoznawanie i rozmywanie twarzy",
    description:
      "Rozpoznaje twarze wybranych profili i rozmywa pozostałe osoby.",
    acceptedFileTypes: ["video"],
    parameters: [
      {
        id: "provider",
        label: "Urządzenie obliczeniowe",
        type: "select",
        defaultValue: "auto",
        options: [
          { label: "Automatycznie (CUDA lub CPU)", value: "auto" },
          { label: "NVIDIA CUDA", value: "cuda" },
          { label: "CPU", value: "cpu" },
        ],
      },
      {
        id: "det_size",
        label: "Rozmiar detekcji",
        type: "select",
        defaultValue: 960,
        options: [
          { label: "640 — szybciej", value: "640" },
          { label: "800", value: "800" },
          { label: "960 — zalecane na test", value: "960" },
          { label: "1280 — większy rozmiar", value: "1280" },
        ],
      },
      {
        id: "recognition_threshold",
        label: "Próg rozpoznawania",
        type: "number",
        defaultValue: 0.45,
        min: 0,
        max: 1,
        step: 0.01,
      },
      {
        id: "blur_padding",
        label: "Margines rozmycia",
        type: "number",
        defaultValue: 0.35,
        min: 0,
        max: 1,
        step: 0.05,
      },
      {
        id: "blur_kernel",
        label: "Siła rozmycia",
        type: "select",
        defaultValue: 51,
        options: [
          { label: "31", value: "31" },
          { label: "51", value: "51" },
          { label: "71", value: "71" },
        ],
      },
      {
        id: "ffmpeg_preset",
        label: "Szybkość kodowania",
        type: "select",
        defaultValue: "veryfast",
        options: [
          { label: "Ultrafast", value: "ultrafast" },
          { label: "Veryfast", value: "veryfast" },
          { label: "Fast", value: "fast" },
          { label: "Medium", value: "medium" },
        ],
      },
      {
        id: "ffmpeg_crf",
        label: "Jakość pliku wynikowego (CRF)",
        type: "number",
        defaultValue: 20,
        min: 0,
        max: 51,
        step: 1,
      },
    ],
    runEndpoint: "/api/modules/face-blur/run",
    statusEndpoint: "/api/modules/face-blur/status",
  }
};