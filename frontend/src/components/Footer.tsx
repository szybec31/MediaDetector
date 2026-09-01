import { useLanguage } from "../i18n";

function Footer() {
  const { t } = useLanguage();

  const contactEmail =
    import.meta.env.VITE_CONTACT_EMAIL;

  return (
    <footer className="app-footer">
      <div>
        {t.app.name}
      </div>

      {contactEmail && (
        <div>
          {t.footer.contact}: {contactEmail}
        </div>
      )}
    </footer>
  );
}

export default Footer;