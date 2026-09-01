import { useLanguage } from "../i18n";

interface InfoOverlayProps {
  onClose: () => void;
}

function InfoOverlay({
  onClose,
}: InfoOverlayProps) {
  const { t } = useLanguage();

  return (
    <div className="info-overlay">
      <div className="info-panel">
        <button
          className="info-close-button"
          onClick={onClose}
          aria-label={t.info.close}
          title={t.info.close}
        >
          ×
        </button>

        <h1>{t.info.title}</h1>

        <p>
          {t.info.description}
        </p>

        <p>
          {t.info.processing}
        </p>

        <h2>
          {t.info.about}
        </h2>

        <p>
          {t.info.projectDescription}
        </p>

        <p className="info-version">
          {t.info.version} 0.1.0
        </p>
      </div>
    </div>
  );
}

export default InfoOverlay;