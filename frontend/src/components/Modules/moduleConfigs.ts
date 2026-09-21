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
};