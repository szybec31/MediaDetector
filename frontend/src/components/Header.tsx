import { useLanguage } from "../i18n";

interface HeaderProps {
  onInfo: () => void;
}

function Header({ onInfo }: HeaderProps) {
  const { language, setLanguage, t } =
    useLanguage();

  return (
    <header className="app-header">
      <div className="app-header-title">
        {t.app.name}
      </div>

      <div className="app-header-actions">
        <div className="language-switcher">
          <button
            className={
              language === "pl"
                ? "language-button active"
                : "language-button"
            }
            onClick={() => setLanguage("pl")}
          >
            PL
          </button>

          <span className="language-separator">
            |
          </span>

          <button
            className={
              language === "en"
                ? "language-button active"
                : "language-button"
            }
            onClick={() => setLanguage("en")}
          >
            EN
          </button>
        </div>

        <button
          className="info-button"
          onClick={onInfo}
          aria-label={t.header.info}
          title={t.header.info}
        >
          i
        </button>
      </div>
    </header>
  );
}

export default Header;