const pl = {
  app: {
    name: "MediaDetector",
  },

  header: {
    info: "Informacje",
    back: "Powrót"
  },

  sidebar: {
    actions: "Akcje",
    newProject: "Nowy projekt",
    newPerson: "Nowa osoba",
    profanityDictionary: "Słownik przekleństw",
  },

  projects: {
    title: "Projekty",
    loading: "Ładowanie projektów...",
    empty: "Brak projektów.",
    created: "Utworzono",
    error: "Nie udało się wczytać projektów.",
  },

  info: {
    title: "MediaDetector",
    description:
      "MediaDetector to aplikacja do wspomaganego przez AI przetwarzania i analizy plików wideo oraz audio.",
    processing:
      "Aplikacja pozwala organizować pliki multimedialne w projektach oraz przetwarzać je za pomocą niezależnych modułów.",
    about: "O aplikacji",
    projectDescription:
      "Każdy projekt posiada własne pliki oraz wyniki przetwarzania. Poszczególne moduły AI mogą wykorzystywać wyniki wygenerowane przez wcześniejsze moduły.",
    version: "Wersja",
    close: "Zamknij",
  },

  footer: {
    contact: "Kontakt",
  },
  newProject: {
    title: "Nowy projekt",
    description: "Utwórz nowy projekt.",
    name: "Nazwa projektu",
    placeholder: "Nazwa projektu",
    required: "Nazwa projektu jest wymagana.",
    cancel: "Anuluj",
    create: "Utwórz projekt",
    creating: "Tworzenie...",
    failed: "Nie udało się utworzyć projektu.",
  },
  profanityDictionary: {
    title: "Słownik przekleństw",
    description:
      "Globalny słownik słów używanych podczas filtrowania treści.",
    loading: "Ładowanie słownika...",
    loadError: "Nie udało się wczytać słownika.",
    saveError: "Nie udało się zapisać słownika.",
    add: "Dodaj",
    edit: "Edytuj",
    delete: "Usuń",
    save: "Zapisz",
    cancel: "Anuluj",
    saving: "Zapisywanie...",
    saveDictionary: "Zapisz słownik",
    back: "Powrót",
    placeholder: "Wpisz słowo",
  },

  projectDetails: {
    loading: "Ładowanie projektu...",
    project: "Projekt",
    files: "Pliki projektu",
    fileCount: "plików",
    emptyFiles: "Projekt nie zawiera jeszcze żadnych plików.",
    preview: "Podgląd pliku",
    selectFile: "Wybierz plik z listy powyżej.",
    modules: "Moduły",
    modulesComingSoon: "Moduły AI będą tutaj.",
    open: "Otwórz",
    download: "Pobierz",
    delete: "Usuń",
    back: "Powrót",
    downloadAll: "Pobierz wszystkie pliki",
    deleteProject: "Usuń projekt",
    deleteConfirmation:
      'Czy na pewno chcesz usunąć projekt "{name}"?',
    loadError: "Nie udało się wczytać projektu.",
    deleteError: "Nie udało się usunąć projektu.",
  },
  addSourceFile: {
    title: "Dodaj pliki źródłowe",
    description: "Dodaj źródłowe pliki audio lub video do projektu.",
    dropzone: {
      title: "Przeciągnij pliki tutaj",
      description: "lub kliknij, aby wybrać pliki z dysku",
      active: "Upuść pliki tutaj",
      supported: "Obsługiwane pliki audio i video",
    },
    selectedFiles: "Wybrane pliki",
    removeFile: "Usuń plik",
    upload: "Dodaj pliki",
    uploading: "Dodawanie...",
    error: {
      noProject: "Nie znaleziono projektu.",
      noFiles: "Wybierz przynajmniej jeden plik.",
      upload: "Nie udało się dodać plików.",
    },
    success: "Pliki zostały dodane.",
  },
  
};

export default pl;